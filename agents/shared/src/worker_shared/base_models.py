"""
Base models for Claude worker agents.

These models are shared across different worker types (PR worker, animation worker, etc.).
Specific workers extend these with their own specialized models.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log level for worker logs."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class LogEntry(BaseModel):
    """Single log entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    level: LogLevel
    message: str


class NotificationType(str, Enum):
    """Type of notification to manager."""

    STATUS_UPDATE = "status_update"
    PERMISSION_REQUEST = "permission_request"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    # PR-specific
    MAIN_BRANCH_FAILED = "main_branch_failed"
    # Animation-specific
    ITERATION_COMPLETE = "iteration_complete"
    QUALITY_THRESHOLD_MET = "quality_threshold_met"


class ManagerNotification(BaseModel):
    """Message to manager (written to notification file)."""

    worker_pid: int
    issue_number: int
    notification_type: NotificationType
    message: str
    requires_response: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseWorkerConfig(BaseModel):
    """
    Base configuration shared by all worker types.

    Specific workers extend this with their own configuration fields.
    """

    # GitHub configuration
    github_token: str
    repo_owner: str
    repo_name: str

    # Working directory configuration
    base_dir: Path
    worktree_base_dir: Path

    # Status file location
    status_dir: Path

    # Common behavior configuration
    max_retries: int = 3

    # Communication channel for manager
    manager_notification_file: Path | None = None


class BaseWorkerStatus(BaseModel):
    """
    Base worker status shared by all worker types.

    Specific workers extend this with their own status fields.
    """

    pid: int
    issue_number: int
    branch: str
    worktree_path: str
    phase: str  # Subclasses use their own phase enum
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    commits: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None
    logs: list[LogEntry] = Field(default_factory=list)


class CIStatus(str, Enum):
    """Status of CI checks."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


class ReviewStatus(str, Enum):
    """Status of PR review."""

    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"


class ReviewComment(BaseModel):
    """A comment from a PR review."""

    path: str
    line: int
    body: str
    is_blocking: bool = False


class PRReview(BaseModel):
    """GitHub PR review from Claude integration."""

    id: int
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED, PENDING
    body: str
    submitted_at: datetime | None = None
    user_login: str
    user_type: str
    comments: list[ReviewComment] = Field(default_factory=list)
