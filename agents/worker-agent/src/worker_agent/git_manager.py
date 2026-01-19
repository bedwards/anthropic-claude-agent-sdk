"""
Git manager for worker agent.
Handles git operations including worktrees for parallel agent isolation.
"""

import shutil
import subprocess
from pathlib import Path

from .models import LogLevel
from .status_manager import StatusManager


class GitManager:
    """
    Manages git operations including worktrees.
    Provides isolation for parallel worker agents.
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

    def get_worktree_path(self) -> Path:
        """Get the worktree path."""
        return self.worktree_path

    def get_branch(self) -> str:
        """Get the branch name."""
        return self.branch

    async def initialize_worktree(self) -> None:
        """Initialize worktree for this worker."""
        self.status_manager.log(LogLevel.INFO, f"Creating worktree at {self.worktree_path}")

        # Ensure parent directory exists
        self.worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Fetch latest from origin
        self._exec("git fetch origin", self.base_dir)

        # Check if branch exists remotely
        remote_branches = self._exec("git branch -r", self.base_dir)
        branch_exists = f"origin/{self.branch}" in remote_branches

        if branch_exists:
            # Checkout existing branch
            self._exec(
                f'git worktree add "{self.worktree_path}" {self.branch}',
                self.base_dir,
            )
            self.status_manager.log(LogLevel.INFO, f"Resumed existing branch: {self.branch}")
        else:
            # Create new branch from main
            self._exec(
                f'git worktree add -b {self.branch} "{self.worktree_path}" origin/main',
                self.base_dir,
            )
            self.status_manager.log(LogLevel.INFO, f"Created new branch: {self.branch}")

        # Install dependencies in worktree if package.json exists
        package_json = self.worktree_path / "package.json"
        if package_json.exists():
            self.status_manager.log(LogLevel.INFO, "Installing dependencies in worktree...")
            self._exec("npm install", self.worktree_path)

        # Or pyproject.toml for Python projects
        pyproject = self.worktree_path / "pyproject.toml"
        if pyproject.exists():
            self.status_manager.log(LogLevel.INFO, "Installing Python dependencies in worktree...")
            # Try uv first, fall back to pip
            try:
                self._exec("uv sync", self.worktree_path)
            except subprocess.CalledProcessError:
                self._exec("pip install -e .", self.worktree_path)

    async def commit(self, message: str) -> str | None:
        """Commit changes with message. Returns SHA or None if no changes."""
        try:
            # Check if there are changes to commit
            status = self._exec("git status --porcelain", self.worktree_path)
            if not status.strip():
                self.status_manager.log(LogLevel.DEBUG, "No changes to commit")
                return None

            # Stage all changes
            self._exec("git add -A", self.worktree_path)

            # Commit
            escaped_message = message.replace('"', '\\"')
            self._exec(f'git commit -m "{escaped_message}"', self.worktree_path)

            # Get commit SHA
            sha = self._exec("git rev-parse HEAD", self.worktree_path).strip()

            await self.status_manager.add_commit(sha)
            return sha
        except subprocess.CalledProcessError as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to commit: {e}")
            return None

    async def push(self) -> bool:
        """Push to remote."""
        try:
            self._exec(f"git push -u origin {self.branch}", self.worktree_path)
            self.status_manager.log(LogLevel.INFO, f"Pushed to origin/{self.branch}")
            return True
        except subprocess.CalledProcessError as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to push: {e}")
            return False

    async def has_conflicts(self) -> bool:
        """Check for merge conflicts with main."""
        try:
            self._exec("git fetch origin main", self.worktree_path)

            # Try merge --no-commit to check for conflicts
            try:
                self._exec(
                    "git merge origin/main --no-commit --no-ff",
                    self.worktree_path,
                )
                # No conflicts - abort the merge
                self._exec("git merge --abort", self.worktree_path)
                return False
            except subprocess.CalledProcessError:
                # Conflicts detected - abort the merge
                try:
                    self._exec("git merge --abort", self.worktree_path)
                except subprocess.CalledProcessError:
                    pass  # May already be aborted
                return True
        except subprocess.CalledProcessError as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to check conflicts: {e}")
            return True  # Assume conflicts on error

    async def rebase_on_main(self) -> bool:
        """Rebase on main to resolve simple conflicts."""
        try:
            self._exec("git fetch origin main", self.worktree_path)
            self._exec("git rebase origin/main", self.worktree_path)
            self.status_manager.log(LogLevel.INFO, "Successfully rebased on main")
            return True
        except subprocess.CalledProcessError as e:
            # Abort failed rebase
            try:
                self._exec("git rebase --abort", self.worktree_path)
            except subprocess.CalledProcessError:
                pass  # May not be in rebase state
            self.status_manager.log(
                LogLevel.WARN,
                f"Rebase failed, manual resolution needed: {e}",
            )
            return False

    def get_changed_files(self) -> list[str]:
        """Get list of changed files compared to main."""
        diff = self._exec("git diff --name-only origin/main", self.worktree_path)
        return [f.strip() for f in diff.split("\n") if f.strip()]

    def get_log(self, count: int = 10) -> str:
        """Get git log for this branch."""
        return self._exec(f"git log --oneline -{count}", self.worktree_path)

    async def cleanup(self) -> None:
        """Cleanup worktree."""
        try:
            self._exec(
                f'git worktree remove "{self.worktree_path}" --force',
                self.base_dir,
            )
            self.status_manager.log(LogLevel.INFO, "Cleaned up worktree")
        except subprocess.CalledProcessError as e:
            self.status_manager.log(LogLevel.WARN, f"Failed to cleanup worktree: {e}")
            # Try force removal of directory
            try:
                shutil.rmtree(self.worktree_path)
            except Exception:
                pass

    def _exec(self, command: str, cwd: Path) -> str:
        """Execute git command synchronously."""
        self.status_manager.log(LogLevel.DEBUG, f"Executing: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
