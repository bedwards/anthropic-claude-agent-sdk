"""
Mock managers for dry-run mode.
These simulate git and GitHub operations without making actual changes.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from .models import (
    CIStatus,
    LogLevel,
    PRReview,
    ReviewComment,
    ReviewStatus,
    WorkerConfig,
)
from .status_manager import StatusManager


class DryRunGitManager:
    """
    Mock GitManager for dry-run mode.
    Simulates git operations without making actual changes.
    """

    def __init__(
        self,
        base_dir: Path,
        worktree_base_dir: Path,
        issue_number: int,
        status_manager: StatusManager,
    ) -> None:
        self.base_dir = base_dir
        self.branch = f"worker/issue-{issue_number}"
        self.worktree_path = worktree_base_dir / f"issue-{issue_number}"
        self.status_manager = status_manager
        self._commit_counter = 0

    def get_worktree_path(self) -> Path:
        """Get the worktree path."""
        return self.worktree_path

    def get_branch(self) -> str:
        """Get the branch name."""
        return self.branch

    async def initialize_worktree(self) -> None:
        """Simulate worktree initialization."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would create worktree at {self.worktree_path}",
        )
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would create/checkout branch {self.branch}",
        )

        # Actually create the directory so Claude SDK can work in it
        self.worktree_path.mkdir(parents=True, exist_ok=True)
        self.status_manager.log(
            LogLevel.DEBUG,
            f"[DRY-RUN] Created directory {self.worktree_path} for simulation",
        )

        # Check what type of project this is
        base_package_json = self.base_dir / "package.json"
        base_pyproject = self.base_dir / "pyproject.toml"

        if base_package_json.exists():
            self.status_manager.log(
                LogLevel.INFO,
                "[DRY-RUN] Would install npm dependencies in worktree",
            )
        elif base_pyproject.exists():
            self.status_manager.log(
                LogLevel.INFO,
                "[DRY-RUN] Would install Python dependencies in worktree",
            )

    async def commit(self, message: str) -> str | None:
        """Simulate committing changes."""
        self._commit_counter += 1
        # Generate a fake SHA
        fake_sha = f"dry-run-{self._commit_counter:07d}{'0' * 33}"

        self.status_manager.log(
            LogLevel.INFO,
            f'[DRY-RUN] Would commit with message: "{message}"',
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            f"[DRY-RUN] Simulated commit SHA: {fake_sha[:7]}",
        )

        await self.status_manager.add_commit(fake_sha)
        return fake_sha

    async def push(self) -> bool:
        """Simulate pushing to remote."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would push to origin/{self.branch}",
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] No actual git push performed",
        )
        return True

    async def has_conflicts(self) -> bool:
        """Simulate checking for merge conflicts."""
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] Would check for merge conflicts with main",
        )
        # Simulate no conflicts in dry-run
        return False

    async def rebase_on_main(self) -> bool:
        """Simulate rebasing on main."""
        self.status_manager.log(
            LogLevel.INFO,
            "[DRY-RUN] Would rebase on origin/main",
        )
        # Simulate successful rebase in dry-run
        return True

    def get_changed_files(self) -> list[str]:
        """Simulate getting changed files."""
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] Would get list of changed files",
        )
        # Return empty list in dry-run
        return []

    def get_log(self, count: int = 10) -> str:
        """Simulate getting git log."""
        self.status_manager.log(
            LogLevel.DEBUG,
            f"[DRY-RUN] Would get git log (last {count} commits)",
        )
        return "[DRY-RUN] Git log simulation"

    async def cleanup(self) -> None:
        """Simulate cleanup."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would cleanup worktree at {self.worktree_path}",
        )


class DryRunGitHubManager:
    """
    Mock GitHubManager for dry-run mode.
    Simulates GitHub API operations without making actual changes.
    """

    def __init__(self, config: WorkerConfig, status_manager: StatusManager) -> None:
        self.config = config
        self.status_manager = status_manager
        self._pr_counter = 1000  # Start at 1000 for fake PR numbers

    async def get_issue(self, issue_number: int) -> dict[str, str | list[str]]:
        """Simulate getting issue details."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would fetch issue #{issue_number} from GitHub",
        )

        # Return mock issue data
        return {
            "title": f"[DRY-RUN] Mock Issue #{issue_number}",
            "body": """This is a simulated issue for dry-run mode.

## Description
In dry-run mode, no actual GitHub API calls are made.

## Acceptance Criteria
- [ ] Simulate feature implementation
- [ ] Generate mock responses
- [ ] Log all simulated actions""",
            "labels": ["dry-run", "simulated"],
        }

    async def create_pr(
        self,
        branch: str,
        issue_number: int,
        title: str,
        body: str,
    ) -> dict[str, int | str]:
        """Simulate creating a pull request."""
        self._pr_counter += 1
        pr_number = self._pr_counter

        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would create PR from {branch} to main",
        )
        self.status_manager.log(
            LogLevel.INFO,
            f'[DRY-RUN] PR title: "{title}"',
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] No actual PR created on GitHub",
        )

        fake_url = f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}/pull/{pr_number}"

        await self.status_manager.set_pr(pr_number, fake_url)

        return {
            "number": pr_number,
            "url": fake_url,
        }

    async def get_pr_reviews(self, pr_number: int) -> list[PRReview]:
        """Simulate getting PR reviews."""
        self.status_manager.log(
            LogLevel.DEBUG,
            f"[DRY-RUN] Would fetch reviews for PR #{pr_number}",
        )
        # Return empty list in dry-run
        return []

    async def wait_for_claude_review(
        self,
        pr_number: int,
        timeout_seconds: int,
    ) -> PRReview | None:
        """Simulate waiting for Claude GitHub integration review."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would wait for Claude review on PR #{pr_number}",
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] Simulating 3-second wait...",
        )

        # Simulate a short wait
        await asyncio.sleep(3)

        # Simulate an approval
        self.status_manager.log(
            LogLevel.INFO,
            "[DRY-RUN] Simulated Claude review: APPROVED",
        )

        await self.status_manager.set_review_status(ReviewStatus.APPROVED)

        return PRReview(
            id=1,
            state="APPROVED",
            body="[DRY-RUN] Simulated approval from Claude",
            submitted_at=datetime.now(),
            user_login="claude-bot",
            user_type="Bot",
            comments=[],
        )

    async def get_pr_check_status(self, pr_number: int) -> CIStatus:
        """Simulate getting PR check status."""
        self.status_manager.log(
            LogLevel.DEBUG,
            f"[DRY-RUN] Would check CI status for PR #{pr_number}",
        )
        await self.status_manager.set_ci_status(CIStatus.SUCCESS)
        return CIStatus.SUCCESS

    async def wait_for_ci(self, pr_number: int, timeout_seconds: int) -> CIStatus:
        """Simulate waiting for CI checks."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would wait for CI checks on PR #{pr_number}",
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] Simulating 3-second wait...",
        )

        # Simulate a short wait
        await asyncio.sleep(3)

        self.status_manager.log(
            LogLevel.INFO,
            "[DRY-RUN] Simulated CI status: SUCCESS",
        )

        await self.status_manager.set_ci_status(CIStatus.SUCCESS)
        return CIStatus.SUCCESS

    async def wait_for_main_branch_build(self, timeout_seconds: int) -> CIStatus:
        """Simulate waiting for main branch build."""
        self.status_manager.log(
            LogLevel.INFO,
            "[DRY-RUN] Would wait for main branch build after merge",
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] Simulating 2-second wait...",
        )

        # Simulate a short wait
        await asyncio.sleep(2)

        self.status_manager.log(
            LogLevel.INFO,
            "[DRY-RUN] Simulated main branch build: SUCCESS",
        )

        return CIStatus.SUCCESS

    async def create_issue_from_feedback(
        self,
        original_issue_number: int,
        pr_number: int,
        comment: ReviewComment,
    ) -> int:
        """Simulate creating an issue from review feedback."""
        fake_issue_number = 9000 + original_issue_number

        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would create follow-up issue #{fake_issue_number}",
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            f'[DRY-RUN] Issue for non-blocking feedback: "{comment.body[:50]}..."',
        )

        await self.status_manager.add_created_issue(fake_issue_number)
        return fake_issue_number

    async def merge_pr(self, pr_number: int) -> bool:
        """Simulate merging the PR."""
        self.status_manager.log(
            LogLevel.INFO,
            f"[DRY-RUN] Would merge PR #{pr_number} (squash merge)",
        )
        self.status_manager.log(
            LogLevel.DEBUG,
            "[DRY-RUN] No actual merge performed on GitHub",
        )
        return True

    async def has_merge_conflicts(self, pr_number: int) -> bool:
        """Simulate checking for merge conflicts."""
        self.status_manager.log(
            LogLevel.DEBUG,
            f"[DRY-RUN] Would check if PR #{pr_number} has merge conflicts",
        )
        # Simulate no conflicts in dry-run
        return False
