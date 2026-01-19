"""
Pydantic models for manager agent state and configuration.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class IssueComplexity(str, Enum):
    """Estimated complexity of an issue."""

    TRIVIAL = "trivial"  # Simple fix, < 1 hour
    SMALL = "small"  # Small feature, < 4 hours
    MEDIUM = "medium"  # Medium feature, < 1 day
    LARGE = "large"  # Large feature, multi-day
    EPIC = "epic"  # Requires breakdown into smaller issues


class IssueStatus(str, Enum):
    """Status of an issue in the manager's view."""

    NEW = "new"  # Just discovered
    TRIAGED = "triaged"  # Complexity assessed
    ASSIGNED = "assigned"  # Worker spawned
    IN_PROGRESS = "in_progress"  # Worker actively working
    BLOCKED = "blocked"  # Worker blocked, needs intervention
    REVIEW = "review"  # PR created, awaiting review
    COMPLETED = "completed"  # Merged successfully
    FAILED = "failed"  # Worker failed, needs manual intervention
    SKIPPED = "skipped"  # Not suitable for automation


class WorkerState(str, Enum):
    """State of a worker process."""

    STARTING = "starting"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueInfo(BaseModel):
    """Information about a GitHub issue being tracked."""

    number: int
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    created_at: datetime
    complexity: IssueComplexity | None = None
    status: IssueStatus = IssueStatus.NEW
    assigned_worker_pid: int | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    notes: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


class WorkerInfo(BaseModel):
    """Information about a running worker agent."""

    pid: int
    issue_number: int
    branch: str
    state: WorkerState = WorkerState.STARTING
    started_at: datetime = Field(default_factory=datetime.now)
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    status_file: Path
    pr_number: int | None = None
    pr_url: str | None = None
    blocked_reason: str | None = None
    error_message: str | None = None


class ManagerConfig(BaseModel):
    """Configuration for the manager agent."""

    # GitHub configuration
    github_token: str
    repo_owner: str
    repo_name: str

    # Working directories
    base_dir: Path
    worktree_base_dir: Path
    status_dir: Path

    # Worker configuration
    max_concurrent_workers: int = 3
    worker_timeout_hours: int = 4
    auto_assign_labels: list[str] = Field(default_factory=lambda: ["good-first-issue", "bug", "enhancement"])
    skip_labels: list[str] = Field(default_factory=lambda: ["wontfix", "duplicate", "invalid", "manual"])

    # Polling intervals
    issue_poll_seconds: int = 60
    worker_poll_seconds: int = 30

    # Escalation
    escalation_file: Path | None = None
    notify_on_block: bool = True
    notify_on_main_failure: bool = True


class ManagerStatus(BaseModel):
    """Current status of the manager agent."""

    pid: int
    started_at: datetime = Field(default_factory=datetime.now)
    last_poll: datetime | None = None
    issues_tracked: int = 0
    workers_active: int = 0
    workers_completed: int = 0
    workers_failed: int = 0
    prs_merged: int = 0
    main_failures: int = 0


class Escalation(BaseModel):
    """An escalation requiring human attention."""

    timestamp: datetime = Field(default_factory=datetime.now)
    issue_number: int
    worker_pid: int | None = None
    escalation_type: str  # "blocked", "failed", "main_failure", "timeout"
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False
