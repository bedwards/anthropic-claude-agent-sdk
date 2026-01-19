"""
Pydantic models for worker agent state and configuration.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WorkerPhase(str, Enum):
    """Current phase of the worker agent lifecycle."""

    INITIALIZING = "initializing"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    CREATING_PR = "creating_pr"
    AWAITING_REVIEW = "awaiting_review"
    ADDRESSING_FEEDBACK = "addressing_feedback"
    CHECKING_CI = "checking_ci"
    RESOLVING_CONFLICTS = "resolving_conflicts"
    MERGING = "merging"
    VERIFYING_MAIN = "verifying_main"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ReviewStatus(str, Enum):
    """Status of PR review."""

    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"


class CIStatus(str, Enum):
    """Status of CI checks."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


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


class WorkerStatus(BaseModel):
    """
    Worker agent status - persisted to status file for monitoring.
    Manager and external tools can read this file to track progress.
    """

    pid: int
    issue_number: int
    branch: str
    worktree_path: str
    phase: WorkerPhase = WorkerPhase.INITIALIZING
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    commits: list[str] = Field(default_factory=list)
    pr_number: int | None = None
    pr_url: str | None = None
    review_status: ReviewStatus | None = None
    ci_status: CIStatus | None = None
    blocked_reason: str | None = None
    created_issues: list[int] = Field(default_factory=list)
    logs: list[LogEntry] = Field(default_factory=list)
    main_branch_verified: bool = False
    dry_run: bool = False  # Whether this worker is running in dry-run mode


class WorkerConfig(BaseModel):
    """Configuration for the worker agent."""

    # GitHub configuration
    github_token: str
    repo_owner: str
    repo_name: str

    # Working directory configuration
    base_dir: Path
    worktree_base_dir: Path

    # Status file location
    status_dir: Path

    # Behavior configuration
    auto_merge: bool = False
    max_retries: int = 3
    review_timeout_seconds: int = 600  # 10 minutes
    ci_timeout_seconds: int = 600  # 10 minutes
    main_build_timeout_seconds: int = 300  # 5 minutes
    commit_frequency_seconds: int = 60  # 1 minute
    dry_run: bool = False  # Dry-run mode: simulate without actual changes

    # Validation thresholds
    coverage_threshold: int = 70

    # Communication channel for manager
    manager_notification_file: Path | None = None


class NotificationType(str, Enum):
    """Type of notification to manager."""

    STATUS_UPDATE = "status_update"
    PERMISSION_REQUEST = "permission_request"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    MAIN_BRANCH_FAILED = "main_branch_failed"


class ManagerNotification(BaseModel):
    """Message to manager (written to notification file)."""

    worker_pid: int
    issue_number: int
    notification_type: NotificationType
    message: str
    requires_response: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


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


class ValidationStep(str, Enum):
    """Validation step type."""

    LINT = "lint"
    TYPECHECK = "typecheck"
    TEST = "test"
    COVERAGE = "coverage"


class ValidationResult(BaseModel):
    """Result of a validation step."""

    step: ValidationStep
    passed: bool
    output: str
    error_count: int = 0
    warning_count: int = 0
