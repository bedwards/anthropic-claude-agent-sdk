"""
Models for animation worker agent.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AnimationPhase(str, Enum):
    """Current phase of the animation worker lifecycle."""

    INITIALIZING = "initializing"
    READING_REQUIREMENTS = "reading_requirements"
    GENERATING_CODE = "generating_code"
    CREATING_ANIMATION = "creating_animation"
    RENDERING_FRAMES = "rendering_frames"
    ANALYZING_QUALITY = "analyzing_quality"
    IMPROVING_ANIMATION = "improving_animation"
    EXPORTING_ROBLOX = "exporting_roblox"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


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


class AnimationWorkerConfig(BaseModel):
    """Configuration for the animation worker agent."""

    # GitHub configuration
    github_token: str
    repo_owner: str
    repo_name: str

    # Working directory configuration
    base_dir: Path
    worktree_base_dir: Path
    output_dir: Path

    # Status file location
    status_dir: Path

    # Animation configuration
    max_iterations: int = 10
    quality_threshold: int = 85
    fps: int = 30
    duration: float = 2.0
    render_resolution: tuple[int, int] = (1280, 720)
    render_samples: int = 16

    # Behavior configuration
    max_retries: int = 3

    # Gemini API key
    gemini_api_key: str | None = None

    # Communication channel for manager
    manager_notification_file: Path | None = None


class IterationStatus(BaseModel):
    """Status of a single animation iteration."""

    iteration_number: int
    quality_score: int
    verdict: str  # "done" or "needs_work"
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    blend_file: str | None = None
    frames_dir: str | None = None


class AnimationWorkerStatus(BaseModel):
    """Animation worker status - persisted to status file for monitoring."""

    pid: int
    issue_number: int
    branch: str
    worktree_path: str
    phase: AnimationPhase = AnimationPhase.INITIALIZING
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    commits: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None
    logs: list[LogEntry] = Field(default_factory=list)

    # Animation-specific status
    current_iteration: int = 0
    iterations: list[IterationStatus] = Field(default_factory=list)
    final_quality_score: int = 0
    final_blend_file: str | None = None
    final_frames_dir: str | None = None
    roblox_export_path: str | None = None


class NotificationType(str, Enum):
    """Type of notification to manager."""

    STATUS_UPDATE = "status_update"
    PERMISSION_REQUEST = "permission_request"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
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
