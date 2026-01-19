"""Tests for worker agent models."""

from worker_agent.models import (
    LogEntry,
    LogLevel,
    ManagerNotification,
    NotificationType,
    WorkerConfig,
    WorkerPhase,
    WorkerStatus,
)


def test_worker_status_creation() -> None:
    """Test creating a WorkerStatus."""
    status = WorkerStatus(
        pid=12345,
        issue_number=42,
        branch="worker/issue-42",
        worktree_path="/tmp/worktrees/issue-42",
    )

    assert status.pid == 12345
    assert status.issue_number == 42
    assert status.phase == WorkerPhase.INITIALIZING
    assert status.commits == []
    assert status.created_issues == []


def test_worker_status_phase_transitions() -> None:
    """Test phase transitions."""
    status = WorkerStatus(
        pid=1,
        issue_number=1,
        branch="test",
        worktree_path="/tmp",
    )

    assert status.phase == WorkerPhase.INITIALIZING

    status.phase = WorkerPhase.IMPLEMENTING
    assert status.phase == WorkerPhase.IMPLEMENTING

    status.phase = WorkerPhase.COMPLETED
    assert status.phase == WorkerPhase.COMPLETED


def test_log_entry_creation() -> None:
    """Test creating a LogEntry."""
    entry = LogEntry(level=LogLevel.INFO, message="Test message")

    assert entry.level == LogLevel.INFO
    assert entry.message == "Test message"
    assert entry.timestamp is not None


def test_manager_notification_creation() -> None:
    """Test creating a ManagerNotification."""
    notification = ManagerNotification(
        worker_pid=123,
        issue_number=42,
        notification_type=NotificationType.COMPLETED,
        message="Done!",
        requires_response=False,
    )

    assert notification.worker_pid == 123
    assert notification.notification_type == NotificationType.COMPLETED
    assert notification.requires_response is False


def test_worker_config_defaults() -> None:
    """Test WorkerConfig default values."""
    from pathlib import Path

    config = WorkerConfig(
        github_token="token",
        repo_owner="owner",
        repo_name="repo",
        base_dir=Path("/base"),
        worktree_base_dir=Path("/worktrees"),
        status_dir=Path("/status"),
    )

    assert config.auto_merge is False
    assert config.max_retries == 3
    assert config.coverage_threshold == 70
    assert config.manager_notification_file is None
