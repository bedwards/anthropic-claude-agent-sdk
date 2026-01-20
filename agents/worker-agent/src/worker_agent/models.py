"""
Pydantic models for worker agent state and configuration.

Imports common models from worker_shared and defines PR-worker specific models.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

# Import shared models
from worker_shared import (
    CIStatus,
    LogEntry,
    LogLevel,
    ManagerNotification,
    NotificationType,
    PRReview,
    ReviewComment,
    ReviewStatus,
)

# Re-export shared models for backwards compatibility
__all__ = [
    # Shared models (re-exported)
    "CIStatus",
    "LogEntry",
    "LogLevel",
    "ManagerNotification",
    "NotificationType",
    "PRReview",
    "ReviewComment",
    "ReviewStatus",
    # Worker-specific models
    "WorkerPhase",
    "WorkerStatus",
    "WorkerConfig",
    "ValidationStep",
    "ValidationResult",
]


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

    # Validation thresholds
    coverage_threshold: int = 70

    # Communication channel for manager
    manager_notification_file: Path | None = None


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
