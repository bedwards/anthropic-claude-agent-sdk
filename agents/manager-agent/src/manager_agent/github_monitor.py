"""
GitHub issue monitoring for manager agent.
Watches for new issues and tracks their state.
"""

from datetime import datetime

from github import Github
from github.Issue import Issue

from .models import (
    IssueComplexity,
    IssueInfo,
    IssueStatus,
    ManagerConfig,
)


class GitHubMonitor:
    """
    Monitors GitHub for new issues and tracks their state.
    """

    def __init__(self, config: ManagerConfig) -> None:
        self.config = config
        self.github = Github(config.github_token)
        self.repo = self.github.get_repo(f"{config.repo_owner}/{config.repo_name}")
        self._tracked_issues: dict[int, IssueInfo] = {}

    def _should_auto_assign(self, issue: Issue) -> bool:
        """Check if an issue should be automatically assigned to a worker."""
        labels = [label.name.lower() for label in issue.labels]

        # Skip if has skip labels
        for skip_label in self.config.skip_labels:
            if skip_label.lower() in labels:
                return False

        # Skip if already has a PR (check for linked PR in body or comments)
        if issue.pull_request is not None:
            return False

        # Auto-assign if has auto-assign labels
        for auto_label in self.config.auto_assign_labels:
            if auto_label.lower() in labels:
                return True

        return False

    def _estimate_complexity(self, issue: Issue) -> IssueComplexity:
        """Estimate issue complexity based on title, body, and labels."""
        labels = [label.name.lower() for label in issue.labels]
        body_len = len(issue.body or "")
        title = issue.title.lower()

        # Check labels first
        if "trivial" in labels or "good-first-issue" in labels:
            return IssueComplexity.TRIVIAL
        if "epic" in labels:
            return IssueComplexity.EPIC

        # Check title keywords
        if any(word in title for word in ["typo", "fix typo", "update readme"]):
            return IssueComplexity.TRIVIAL

        if any(word in title for word in ["refactor", "redesign", "rewrite"]):
            return IssueComplexity.LARGE

        # Estimate based on body length
        if body_len < 200:
            return IssueComplexity.SMALL
        if body_len < 1000:
            return IssueComplexity.MEDIUM
        return IssueComplexity.LARGE

    def _issue_to_info(self, issue: Issue) -> IssueInfo:
        """Convert GitHub Issue to IssueInfo model."""
        return IssueInfo(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            labels=[label.name for label in issue.labels],
            created_at=issue.created_at,
            complexity=self._estimate_complexity(issue),
            status=IssueStatus.NEW,
        )

    async def poll_issues(self) -> list[IssueInfo]:
        """
        Poll for open issues that could be assigned to workers.
        Returns list of new issues discovered.
        """
        new_issues: list[IssueInfo] = []

        # Get open issues
        issues = self.repo.get_issues(state="open", sort="created", direction="desc")

        for issue in issues:
            # Skip PRs (GitHub API returns them as issues too)
            if issue.pull_request is not None:
                continue

            # Skip already tracked
            if issue.number in self._tracked_issues:
                continue

            # Check if should auto-assign
            if self._should_auto_assign(issue):
                info = self._issue_to_info(issue)
                info.status = IssueStatus.TRIAGED
                self._tracked_issues[issue.number] = info
                new_issues.append(info)

        return new_issues

    def get_tracked_issues(self) -> list[IssueInfo]:
        """Get all tracked issues."""
        return list(self._tracked_issues.values())

    def get_issue(self, issue_number: int) -> IssueInfo | None:
        """Get a specific tracked issue."""
        return self._tracked_issues.get(issue_number)

    def update_issue_status(
        self,
        issue_number: int,
        status: IssueStatus,
        **kwargs: int | str | None,
    ) -> None:
        """Update the status of a tracked issue."""
        if issue_number in self._tracked_issues:
            issue = self._tracked_issues[issue_number]
            issue.status = status
            issue.last_updated = datetime.now()

            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(issue, key):
                    setattr(issue, key, value)

    def get_assignable_issues(self) -> list[IssueInfo]:
        """Get issues that are ready to be assigned to workers."""
        return [
            issue
            for issue in self._tracked_issues.values()
            if issue.status == IssueStatus.TRIAGED
            and issue.complexity not in (IssueComplexity.EPIC, None)
        ]

    def add_issue_note(self, issue_number: int, note: str) -> None:
        """Add a note to a tracked issue."""
        if issue_number in self._tracked_issues:
            self._tracked_issues[issue_number].notes.append(
                f"[{datetime.now().isoformat()}] {note}"
            )

    async def check_issue_closed(self, issue_number: int) -> bool:
        """Check if an issue has been closed on GitHub."""
        try:
            issue = self.repo.get_issue(issue_number)
            return issue.state == "closed"
        except Exception:
            return False
