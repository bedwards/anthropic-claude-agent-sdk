"""Tests for manager agent models."""

from datetime import datetime
from pathlib import Path

import pytest

from manager_agent.models import (
    Escalation,
    IssueComplexity,
    IssueInfo,
    IssueStatus,
    ManagerConfig,
    ManagerStatus,
    WorkerInfo,
    WorkerState,
)


class TestIssueInfo:
    """Tests for IssueInfo model."""

    def test_create_basic_issue(self) -> None:
        """Test creating a basic issue."""
        issue = IssueInfo(
            number=1,
            title="Test issue",
            body="Test body",
            created_at=datetime.now(),
        )
        assert issue.number == 1
        assert issue.title == "Test issue"
        assert issue.status == IssueStatus.NEW
        assert issue.complexity is None

    def test_issue_with_labels(self) -> None:
        """Test issue with labels."""
        issue = IssueInfo(
            number=2,
            title="Bug fix",
            body="Fix the bug",
            labels=["bug", "good-first-issue"],
            created_at=datetime.now(),
        )
        assert "bug" in issue.labels
        assert "good-first-issue" in issue.labels

    def test_issue_status_transitions(self) -> None:
        """Test issue status can transition."""
        issue = IssueInfo(
            number=3,
            title="Feature",
            body="Add feature",
            created_at=datetime.now(),
        )
        assert issue.status == IssueStatus.NEW

        issue.status = IssueStatus.TRIAGED
        assert issue.status == IssueStatus.TRIAGED

        issue.status = IssueStatus.ASSIGNED
        assert issue.status == IssueStatus.ASSIGNED


class TestWorkerInfo:
    """Tests for WorkerInfo model."""

    def test_create_worker(self) -> None:
        """Test creating a worker."""
        worker = WorkerInfo(
            pid=12345,
            issue_number=1,
            branch="worker/issue-1",
            status_file=Path("/tmp/worker-1.json"),
        )
        assert worker.pid == 12345
        assert worker.state == WorkerState.STARTING
        assert worker.pr_number is None

    def test_worker_with_pr(self) -> None:
        """Test worker with PR info."""
        worker = WorkerInfo(
            pid=12345,
            issue_number=1,
            branch="worker/issue-1",
            status_file=Path("/tmp/worker-1.json"),
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
        )
        assert worker.pr_number == 42
        assert "42" in worker.pr_url


class TestManagerConfig:
    """Tests for ManagerConfig model."""

    def test_create_config(self) -> None:
        """Test creating manager config."""
        config = ManagerConfig(
            github_token="test-token",
            repo_owner="owner",
            repo_name="repo",
            base_dir=Path("/tmp/base"),
            worktree_base_dir=Path("/tmp/worktrees"),
            status_dir=Path("/tmp/status"),
        )
        assert config.github_token == "test-token"
        assert config.max_concurrent_workers == 3
        assert config.worker_timeout_hours == 4

    def test_config_defaults(self) -> None:
        """Test config defaults."""
        config = ManagerConfig(
            github_token="token",
            repo_owner="owner",
            repo_name="repo",
            base_dir=Path("/tmp"),
            worktree_base_dir=Path("/tmp"),
            status_dir=Path("/tmp"),
        )
        assert "good-first-issue" in config.auto_assign_labels
        assert "bug" in config.auto_assign_labels
        assert "wontfix" in config.skip_labels


class TestEscalation:
    """Tests for Escalation model."""

    def test_create_escalation(self) -> None:
        """Test creating an escalation."""
        escalation = Escalation(
            issue_number=1,
            worker_pid=12345,
            escalation_type="blocked",
            message="Worker blocked on merge conflict",
        )
        assert escalation.issue_number == 1
        assert escalation.resolved is False

    def test_escalation_with_context(self) -> None:
        """Test escalation with context."""
        escalation = Escalation(
            issue_number=1,
            escalation_type="main_failure",
            message="Main branch build failed",
            context={
                "pr_number": 42,
                "error": "Tests failed",
            },
        )
        assert escalation.context["pr_number"] == 42


class TestIssueComplexity:
    """Tests for IssueComplexity enum."""

    def test_complexity_values(self) -> None:
        """Test complexity enum values."""
        assert IssueComplexity.TRIVIAL.value == "trivial"
        assert IssueComplexity.SMALL.value == "small"
        assert IssueComplexity.MEDIUM.value == "medium"
        assert IssueComplexity.LARGE.value == "large"
        assert IssueComplexity.EPIC.value == "epic"
