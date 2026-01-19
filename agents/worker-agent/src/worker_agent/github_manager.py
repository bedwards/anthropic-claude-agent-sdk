"""
GitHub manager for worker agent.
Handles PRs, reviews, issues, and CI checks.
"""

import asyncio
import re
from datetime import datetime

from github import Github
from github.GithubException import GithubException
from github.PullRequest import PullRequest

from .models import (
    CIStatus,
    LogLevel,
    PRReview,
    ReviewComment,
    ReviewStatus,
    WorkerConfig,
)
from .status_manager import StatusManager


class GitHubManager:
    """
    Manages GitHub operations: PRs, reviews, issues, checks.
    """

    def __init__(self, config: WorkerConfig, status_manager: StatusManager) -> None:
        self.config = config
        self.status_manager = status_manager
        self.github = Github(config.github_token)
        self.repo = self.github.get_repo(f"{config.repo_owner}/{config.repo_name}")

    async def get_issue(self, issue_number: int) -> dict[str, str | list[str]]:
        """Get issue details."""
        issue = self.repo.get_issue(issue_number)
        return {
            "title": issue.title,
            "body": issue.body or "",
            "labels": [label.name for label in issue.labels],
        }

    async def get_existing_pr(self, branch: str) -> dict[str, int | str] | None:
        """Check if a PR already exists for this branch."""
        pulls = self.repo.get_pulls(state="open", head=f"{self.config.repo_owner}:{branch}")
        for pr in pulls:
            return {
                "number": pr.number,
                "url": pr.html_url,
            }
        return None

    async def create_pr(
        self,
        branch: str,
        issue_number: int,
        title: str,
        body: str,
    ) -> dict[str, int | str]:
        """Create a pull request, or return existing one if already exists."""
        self.status_manager.log(LogLevel.INFO, f"Creating PR for branch {branch}")

        # Check if PR already exists for this branch
        existing = await self.get_existing_pr(branch)
        if existing:
            self.status_manager.log(
                LogLevel.INFO,
                f"PR already exists for branch {branch}: #{existing['number']}",
            )
            await self.status_manager.set_pr(existing["number"], str(existing["url"]))
            return existing

        try:
            pr = self.repo.create_pull(
                title=f"{title} (closes #{issue_number})",
                body=f"{body}\n\nCloses #{issue_number}\n\n---\n_Created by worker agent_",
                head=branch,
                base="main",
            )

            await self.status_manager.set_pr(pr.number, pr.html_url)

            return {
                "number": pr.number,
                "url": pr.html_url,
            }
        except GithubException as e:
            if e.status == 422:
                # PR might have been created between our check and create
                existing = await self.get_existing_pr(branch)
                if existing:
                    self.status_manager.log(
                        LogLevel.INFO,
                        f"PR was created concurrently: #{existing['number']}",
                    )
                    await self.status_manager.set_pr(existing["number"], str(existing["url"]))
                    return existing
            raise

    async def get_pr_reviews(self, pr_number: int) -> list[PRReview]:
        """Get PR reviews, filtering for Claude GitHub integration."""
        pr = self.repo.get_pull(pr_number)
        reviews = list(pr.get_reviews())
        review_comments = list(pr.get_review_comments())

        result: list[PRReview] = []

        for review in reviews:
            # Get comments for this review
            comments_for_review: list[ReviewComment] = []
            for comment in review_comments:
                if comment.pull_request_review_id == review.id:
                    # Consider comment blocking if it contains certain keywords
                    body_lower = comment.body.lower()
                    is_blocking = any(
                        keyword in body_lower
                        for keyword in ["must", "required", "blocking", "security"]
                    )
                    comments_for_review.append(
                        ReviewComment(
                            path=comment.path,
                            line=comment.line or comment.original_line or 0,
                            body=comment.body,
                            is_blocking=is_blocking,
                        )
                    )

            submitted_at = None
            if review.submitted_at:
                submitted_at = review.submitted_at

            result.append(
                PRReview(
                    id=review.id,
                    state=review.state,
                    body=review.body or "",
                    submitted_at=submitted_at,
                    user_login=review.user.login if review.user else "unknown",
                    user_type=review.user.type if review.user else "User",
                    comments=comments_for_review,
                )
            )

        return result

    async def get_pr_comments_from_claude(self, pr_number: int) -> list[PRReview]:
        """Get PR issue comments from Claude GitHub integration.

        Claude GitHub integration posts issue comments (not formal reviews),
        so we need to check these separately.
        """
        pr = self.repo.get_pull(pr_number)
        issue_comments = list(pr.get_issue_comments())

        result: list[PRReview] = []

        for comment in issue_comments:
            user_login = comment.user.login if comment.user else "unknown"
            user_type = comment.user.type if comment.user else "User"

            # Check if this is from Claude
            is_claude = (
                user_type == "Bot"
                or "claude" in user_login.lower()
                or "anthropic" in user_login.lower()
            )

            if not is_claude:
                continue

            # Parse comment to determine if it's requesting changes
            body_lower = comment.body.lower()

            # Claude comments that suggest fixes are treated as change requests
            requests_changes = any(
                indicator in body_lower
                for indicator in ["fix:", "issue:", "bug:", "error:", "problem:", "should", "must", "need to"]
            )

            # Determine state based on content
            if requests_changes:
                state = "CHANGES_REQUESTED"
            else:
                state = "COMMENTED"

            # Extract file path and line from comment if present
            # Claude format: [file.py:123](url)
            review_comments: list[ReviewComment] = []
            file_refs = re.findall(r'\[`?([^`\]]+(?::\d+)?)`?\]', comment.body)
            for ref in file_refs:
                if ':' in ref:
                    path, line_str = ref.rsplit(':', 1)
                    try:
                        line = int(line_str.split('-')[0])  # Handle ranges like 101-113
                    except ValueError:
                        line = 0
                else:
                    path = ref
                    line = 0

                review_comments.append(
                    ReviewComment(
                        path=path,
                        line=line,
                        body=comment.body,
                        is_blocking=requests_changes,
                    )
                )

            result.append(
                PRReview(
                    id=comment.id,
                    state=state,
                    body=comment.body,
                    submitted_at=comment.created_at,
                    user_login=user_login,
                    user_type=user_type,
                    comments=review_comments if review_comments else [
                        ReviewComment(path="", line=0, body=comment.body, is_blocking=requests_changes)
                    ],
                )
            )

        return result

    async def wait_for_claude_review(
        self,
        pr_number: int,
        timeout_seconds: int,
        already_processed_ids: set[int] | None = None,
    ) -> PRReview | None:
        """Wait for Claude GitHub integration to review.

        Checks both formal PR reviews AND issue comments, since Claude
        GitHub integration typically posts issue comments rather than
        formal reviews.

        Args:
            pr_number: PR number to check
            timeout_seconds: How long to wait
            already_processed_ids: Set of comment IDs that have already been
                addressed - these will be skipped to avoid re-processing
        """
        start_time = datetime.now()
        poll_interval = 15  # seconds
        skip_ids = already_processed_ids or set()

        self.status_manager.log(
            LogLevel.INFO,
            f"Waiting for Claude GitHub integration feedback on PR #{pr_number}",
        )
        if skip_ids:
            self.status_manager.log(
                LogLevel.DEBUG,
                f"Skipping {len(skip_ids)} already-processed comment(s)",
            )

        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            # Check formal PR reviews first
            reviews = await self.get_pr_reviews(pr_number)
            for review in reviews:
                if review.id in skip_ids:
                    continue
                is_claude = (
                    review.user_type == "Bot"
                    or "claude" in review.user_login.lower()
                    or "anthropic" in review.user_login.lower()
                )
                if is_claude and review.state != "PENDING":
                    self.status_manager.log(
                        LogLevel.INFO,
                        f"Claude formal review received: {review.state}",
                    )
                    status_map = {
                        "APPROVED": ReviewStatus.APPROVED,
                        "CHANGES_REQUESTED": ReviewStatus.CHANGES_REQUESTED,
                        "COMMENTED": ReviewStatus.COMMENTED,
                    }
                    await self.status_manager.set_review_status(
                        status_map.get(review.state, ReviewStatus.COMMENTED)
                    )
                    return review

            # Check issue comments (Claude GitHub integration uses these)
            claude_comments = await self.get_pr_comments_from_claude(pr_number)
            for comment in claude_comments:
                if comment.id in skip_ids:
                    continue
                self.status_manager.log(
                    LogLevel.INFO,
                    f"Claude comment received: {comment.state} from {comment.user_login}",
                )
                status_map = {
                    "APPROVED": ReviewStatus.APPROVED,
                    "CHANGES_REQUESTED": ReviewStatus.CHANGES_REQUESTED,
                    "COMMENTED": ReviewStatus.COMMENTED,
                }
                await self.status_manager.set_review_status(
                    status_map.get(comment.state, ReviewStatus.COMMENTED)
                )
                return comment

            self.status_manager.log(
                LogLevel.DEBUG,
                f"No new Claude feedback yet, polling in {poll_interval}s...",
            )
            await asyncio.sleep(poll_interval)

        self.status_manager.log(
            LogLevel.WARN,
            f"Timed out waiting for Claude feedback after {timeout_seconds}s",
        )
        return None

    async def get_pr_check_status(self, pr_number: int) -> CIStatus:
        """Get PR check status (CI)."""
        pr = self.repo.get_pull(pr_number)
        head_sha = pr.head.sha

        # Get combined status
        combined_status = self.repo.get_commit(head_sha).get_combined_status()

        # Get check runs (GitHub Actions)
        check_runs = list(self.repo.get_commit(head_sha).get_check_runs())

        # Determine overall status
        has_failure = combined_status.state == "failure" or any(
            run.conclusion == "failure" for run in check_runs
        )

        all_complete = combined_status.state != "pending" and all(
            run.status == "completed" for run in check_runs
        )

        if has_failure:
            await self.status_manager.set_ci_status(CIStatus.FAILURE)
            return CIStatus.FAILURE

        if all_complete:
            await self.status_manager.set_ci_status(CIStatus.SUCCESS)
            return CIStatus.SUCCESS

        await self.status_manager.set_ci_status(CIStatus.PENDING)
        return CIStatus.PENDING

    async def wait_for_ci(self, pr_number: int, timeout_seconds: int) -> CIStatus:
        """Wait for CI checks to complete."""
        start_time = datetime.now()
        poll_interval = 30  # seconds

        self.status_manager.log(LogLevel.INFO, f"Waiting for CI checks on PR #{pr_number}")

        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            status = await self.get_pr_check_status(pr_number)

            if status == CIStatus.SUCCESS:
                self.status_manager.log(LogLevel.INFO, "CI checks passed")
                return CIStatus.SUCCESS

            if status == CIStatus.FAILURE:
                self.status_manager.log(LogLevel.WARN, "CI checks failed")
                return CIStatus.FAILURE

            self.status_manager.log(
                LogLevel.DEBUG,
                f"CI still pending, polling in {poll_interval}s...",
            )
            await asyncio.sleep(poll_interval)

        self.status_manager.log(
            LogLevel.WARN,
            f"CI timeout after {timeout_seconds}s, treating as failure",
        )
        return CIStatus.FAILURE

    async def wait_for_main_branch_build(self, timeout_seconds: int) -> CIStatus:
        """Wait for main branch build to complete after merge."""
        start_time = datetime.now()
        poll_interval = 15  # seconds

        self.status_manager.log(LogLevel.INFO, "Waiting for main branch build...")

        # Get the latest commit on main
        main_branch = self.repo.get_branch("main")

        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            # Get check runs for main
            check_runs = list(main_branch.commit.get_check_runs())
            combined_status = main_branch.commit.get_combined_status()

            has_failure = combined_status.state == "failure" or any(
                run.conclusion == "failure" for run in check_runs
            )

            all_complete = combined_status.state != "pending" and all(
                run.status == "completed" for run in check_runs
            )

            if has_failure:
                self.status_manager.log(LogLevel.ERROR, "Main branch build FAILED!")
                return CIStatus.FAILURE

            if all_complete:
                self.status_manager.log(LogLevel.INFO, "Main branch build passed")
                return CIStatus.SUCCESS

            self.status_manager.log(
                LogLevel.DEBUG,
                f"Main build still pending, polling in {poll_interval}s...",
            )
            await asyncio.sleep(poll_interval)

        self.status_manager.log(
            LogLevel.WARN,
            f"Main build timeout after {timeout_seconds}s",
        )
        return CIStatus.PENDING

    async def create_issue_from_feedback(
        self,
        original_issue_number: int,
        pr_number: int,
        comment: ReviewComment,
    ) -> int:
        """Create an issue for non-blocking review feedback."""
        issue = self.repo.create_issue(
            title=f"Follow-up from PR #{pr_number}: {comment.path}",
            body=f"""## Non-blocking feedback from code review

**Original Issue:** #{original_issue_number}
**PR:** #{pr_number}
**File:** `{comment.path}` (line {comment.line})

### Feedback
{comment.body}

---
_Created automatically by worker agent from non-blocking review comment_""",
            labels=["follow-up", "from-review"],
        )

        await self.status_manager.add_created_issue(issue.number)
        return issue.number

    async def merge_pr(self, pr_number: int) -> bool:
        """Merge the PR."""
        try:
            pr = self.repo.get_pull(pr_number)
            pr.merge(merge_method="squash")
            self.status_manager.log(LogLevel.INFO, f"Successfully merged PR #{pr_number}")
            return True
        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to merge PR: {e}")
            return False

    async def has_merge_conflicts(self, pr_number: int) -> bool:
        """Check if PR has merge conflicts."""
        pr = self.repo.get_pull(pr_number)
        return pr.mergeable is False
