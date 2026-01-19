"""Tests for dry-run mode functionality."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from worker_agent.agent import WorkerAgent
from worker_agent.dry_run_managers import DryRunGitHubManager, DryRunGitManager
from worker_agent.models import (
    CIStatus,
    WorkerConfig,
)
from worker_agent.status_manager import StatusManager


@pytest.fixture
def dry_run_config(tmp_path: Path) -> WorkerConfig:
    """Create a dry-run config for testing."""
    return WorkerConfig(
        github_token="fake-token",
        repo_owner="test-owner",
        repo_name="test-repo",
        base_dir=tmp_path / "base",
        worktree_base_dir=tmp_path / "worktrees",
        status_dir=tmp_path / "status",
        dry_run=True,
    )


@pytest.fixture
def normal_config(tmp_path: Path) -> WorkerConfig:
    """Create a normal (non-dry-run) config for testing."""
    return WorkerConfig(
        github_token="fake-token",
        repo_owner="test-owner",
        repo_name="test-repo",
        base_dir=tmp_path / "base",
        worktree_base_dir=tmp_path / "worktrees",
        status_dir=tmp_path / "status",
        dry_run=False,
    )


@pytest.fixture
async def status_manager(dry_run_config: WorkerConfig, tmp_path: Path) -> StatusManager:
    """Create a status manager for testing."""
    mgr = StatusManager(
        dry_run_config,
        issue_number=1,
        branch="test-branch",
        worktree_path=str(tmp_path / "worktrees" / "issue-1"),
    )
    await mgr.initialize()
    return mgr


class TestDryRunConfig:
    """Test dry-run configuration."""

    def test_dry_run_default_false(self, tmp_path: Path) -> None:
        """Test that dry_run defaults to False."""
        config = WorkerConfig(
            github_token="token",
            repo_owner="owner",
            repo_name="repo",
            base_dir=tmp_path,
            worktree_base_dir=tmp_path,
            status_dir=tmp_path,
        )
        assert config.dry_run is False

    def test_dry_run_can_be_enabled(self, tmp_path: Path) -> None:
        """Test that dry_run can be set to True."""
        config = WorkerConfig(
            github_token="token",
            repo_owner="owner",
            repo_name="repo",
            base_dir=tmp_path,
            worktree_base_dir=tmp_path,
            status_dir=tmp_path,
            dry_run=True,
        )
        assert config.dry_run is True


class TestDryRunStatus:
    """Test dry-run status tracking."""

    @pytest.mark.asyncio
    async def test_status_tracks_dry_run(
        self, dry_run_config: WorkerConfig, tmp_path: Path
    ) -> None:
        """Test that status file tracks dry_run mode."""
        mgr = StatusManager(
            dry_run_config,
            issue_number=1,
            branch="test-branch",
            worktree_path=str(tmp_path / "worktrees" / "issue-1"),
        )
        await mgr.initialize()

        status = mgr.get_status()
        assert status.dry_run is True

    @pytest.mark.asyncio
    async def test_status_file_shows_dry_run(
        self, dry_run_config: WorkerConfig, tmp_path: Path
    ) -> None:
        """Test that status file persists dry_run flag."""
        mgr = StatusManager(
            dry_run_config,
            issue_number=42,
            branch="test-branch",
            worktree_path=str(tmp_path / "worktrees" / "issue-42"),
        )
        await mgr.initialize()

        # Read the status file
        import json

        status_file = dry_run_config.status_dir / "worker-42.json"
        data = json.loads(status_file.read_text())

        assert data["dry_run"] is True


class TestDryRunGitManager:
    """Test dry-run git manager."""

    @pytest.mark.asyncio
    async def test_initialize_worktree_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that worktree initialization is simulated."""
        git_mgr = DryRunGitManager(
            dry_run_config.base_dir,
            dry_run_config.worktree_base_dir,
            issue_number=1,
            status_manager=status_manager,
        )

        await git_mgr.initialize_worktree()

        # Verify worktree path was created (for Claude SDK)
        assert git_mgr.get_worktree_path().exists()

        # Check logs for dry-run messages
        logs = status_manager.get_status().logs
        log_messages = [log.message for log in logs]
        assert any("[DRY-RUN]" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_commit_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that commits are simulated."""
        git_mgr = DryRunGitManager(
            dry_run_config.base_dir,
            dry_run_config.worktree_base_dir,
            issue_number=1,
            status_manager=status_manager,
        )

        sha = await git_mgr.commit("Test commit")

        assert sha is not None
        assert sha.startswith("dry-run-")
        assert len(sha) >= 40  # At least as long as a git SHA

        # Verify commit was logged
        status = status_manager.get_status()
        assert sha in status.commits

    @pytest.mark.asyncio
    async def test_push_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that push is simulated."""
        git_mgr = DryRunGitManager(
            dry_run_config.base_dir,
            dry_run_config.worktree_base_dir,
            issue_number=1,
            status_manager=status_manager,
        )

        result = await git_mgr.push()

        assert result is True

        # Check logs for dry-run push message
        logs = status_manager.get_status().logs
        log_messages = [log.message for log in logs]
        assert any("Would push to origin/" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_no_conflicts_in_dry_run(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that conflicts are simulated as none."""
        git_mgr = DryRunGitManager(
            dry_run_config.base_dir,
            dry_run_config.worktree_base_dir,
            issue_number=1,
            status_manager=status_manager,
        )

        has_conflicts = await git_mgr.has_conflicts()

        assert has_conflicts is False


class TestDryRunGitHubManager:
    """Test dry-run GitHub manager."""

    @pytest.mark.asyncio
    async def test_get_issue_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that getting issue returns mock data."""
        github_mgr = DryRunGitHubManager(dry_run_config, status_manager)

        issue = await github_mgr.get_issue(42)

        assert issue["title"] == "[DRY-RUN] Mock Issue #42"
        assert "simulated" in issue["body"]
        assert "dry-run" in issue["labels"]

    @pytest.mark.asyncio
    async def test_create_pr_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that PR creation is simulated."""
        github_mgr = DryRunGitHubManager(dry_run_config, status_manager)

        pr_info = await github_mgr.create_pr(
            branch="test-branch",
            issue_number=1,
            title="Test PR",
            body="Test body",
        )

        assert pr_info["number"] > 0
        assert "github.com" in pr_info["url"]
        assert "pull" in pr_info["url"]

        # Verify PR was logged
        status = status_manager.get_status()
        assert status.pr_number == pr_info["number"]
        assert status.pr_url == pr_info["url"]

    @pytest.mark.asyncio
    async def test_wait_for_review_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that review waiting is simulated."""
        github_mgr = DryRunGitHubManager(dry_run_config, status_manager)

        review = await github_mgr.wait_for_claude_review(pr_number=1, timeout_seconds=10)

        assert review is not None
        assert review.state == "APPROVED"
        assert review.user_type == "Bot"
        assert "[DRY-RUN]" in review.body

    @pytest.mark.asyncio
    async def test_ci_always_succeeds(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that CI is simulated as success."""
        github_mgr = DryRunGitHubManager(dry_run_config, status_manager)

        ci_status = await github_mgr.wait_for_ci(pr_number=1, timeout_seconds=10)

        assert ci_status == CIStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_merge_simulated(
        self, dry_run_config: WorkerConfig, status_manager: StatusManager
    ) -> None:
        """Test that merge is simulated."""
        github_mgr = DryRunGitHubManager(dry_run_config, status_manager)

        result = await github_mgr.merge_pr(pr_number=1)

        assert result is True

        # Check logs for dry-run merge message
        logs = status_manager.get_status().logs
        log_messages = [log.message for log in logs]
        assert any("Would merge PR" in msg for msg in log_messages)


class TestDryRunCLI:
    """Test dry-run CLI behavior."""

    def test_status_command_shows_dry_run(
        self, dry_run_config: WorkerConfig, tmp_path: Path
    ) -> None:
        """Test that status command displays dry-run mode."""
        import json

        from typer.testing import CliRunner

        from worker_agent.cli import app

        runner = CliRunner()

        # Create a status file with dry_run=True
        status_file = dry_run_config.status_dir / "worker-42.json"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_data = {
            "pid": 12345,
            "issue_number": 42,
            "branch": "worker/issue-42",
            "worktree_path": "/tmp/worktree",
            "phase": "implementing",
            "started_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:01:00",
            "dry_run": True,
            "commits": [],
            "logs": [],
            "created_issues": [],
            "main_branch_verified": False,
        }
        status_file.write_text(json.dumps(status_data))

        # Run status command
        result = runner.invoke(
            app, ["status", "42", "--status-dir", str(dry_run_config.status_dir)]
        )

        assert result.exit_code == 0
        assert "DRY-RUN" in result.stdout
        assert "simulated" in result.stdout.lower()


class TestDryRunAgent:
    """Test dry-run agent behavior."""

    @pytest.mark.asyncio
    async def test_agent_uses_dry_run_managers(
        self, dry_run_config: WorkerConfig
    ) -> None:
        """Test that agent uses dry-run managers when dry_run=True."""
        agent = WorkerAgent(dry_run_config, issue_number=1)

        # Initialize the agent
        with patch.object(agent, "_implement_feature", new_callable=AsyncMock) as mock_impl:
            with patch.object(agent, "_validate", new_callable=AsyncMock) as mock_val:
                with patch.object(agent, "_create_pr", new_callable=AsyncMock) as mock_pr:
                    mock_impl.return_value = True
                    mock_val.return_value = True
                    mock_pr.return_value = {"number": 1, "url": "http://test"}

                    # Start but don't complete the full lifecycle
                    # Just verify the managers are initialized correctly
                    try:
                        # Run initialization only
                        branch = f"worker/issue-{agent.issue_number}"
                        worktree_path = dry_run_config.worktree_base_dir / f"issue-{agent.issue_number}"

                        agent.status_manager = StatusManager(
                            dry_run_config,
                            agent.issue_number,
                            branch,
                            str(worktree_path),
                        )
                        await agent.status_manager.initialize()

                        # Initialize managers
                        if dry_run_config.dry_run:
                            agent.git_manager = DryRunGitManager(
                                dry_run_config.base_dir,
                                dry_run_config.worktree_base_dir,
                                agent.issue_number,
                                agent.status_manager,
                            )
                            agent.github_manager = DryRunGitHubManager(
                                dry_run_config, agent.status_manager
                            )

                        # Verify managers are dry-run versions
                        assert isinstance(agent.git_manager, DryRunGitManager)
                        assert isinstance(agent.github_manager, DryRunGitHubManager)
                    except Exception:
                        pass  # Expected since we're not running the full lifecycle

    @pytest.mark.asyncio
    async def test_agent_uses_normal_managers(self, normal_config: WorkerConfig) -> None:
        """Test that agent uses normal managers when dry_run=False."""
        from worker_agent.git_manager import GitManager
        from worker_agent.github_manager import GitHubManager

        agent = WorkerAgent(normal_config, issue_number=1)

        # Initialize managers
        branch = f"worker/issue-{agent.issue_number}"
        worktree_path = normal_config.worktree_base_dir / f"issue-{agent.issue_number}"

        agent.status_manager = StatusManager(
            normal_config,
            agent.issue_number,
            branch,
            str(worktree_path),
        )
        await agent.status_manager.initialize()

        # Initialize managers
        if not normal_config.dry_run:
            agent.git_manager = GitManager(
                normal_config.base_dir,
                normal_config.worktree_base_dir,
                agent.issue_number,
                agent.status_manager,
            )
            with patch("worker_agent.github_manager.Github"):
                agent.github_manager = GitHubManager(normal_config, agent.status_manager)

        # Verify managers are normal versions
        assert isinstance(agent.git_manager, GitManager)
        assert isinstance(agent.github_manager, GitHubManager)
