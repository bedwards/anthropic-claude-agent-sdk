"""
Status manager for animation worker agent.

Handles logging, status persistence, and manager notifications.
"""

import json
import os
from datetime import datetime
from typing import Any

from rich.console import Console

from .models import (
    AnimationPhase,
    AnimationWorkerConfig,
    AnimationWorkerStatus,
    IterationStatus,
    LogEntry,
    LogLevel,
    ManagerNotification,
    NotificationType,
)

console = Console()


class AnimationStatusManager:
    """
    Manages animation worker status persistence and logging.
    Provides monitoring capabilities for manager and external tools.
    """

    def __init__(
        self,
        config: AnimationWorkerConfig,
        issue_number: int,
        branch: str,
        worktree_path: str,
    ) -> None:
        self.config = config
        self.status_file_path = config.status_dir / f"animation-worker-{issue_number}.json"

        self.status = AnimationWorkerStatus(
            pid=os.getpid(),
            issue_number=issue_number,
            branch=branch,
            worktree_path=worktree_path,
        )

    async def initialize(self) -> None:
        """Initialize status file - creates directory if needed."""
        self.config.status_dir.mkdir(parents=True, exist_ok=True)
        await self._persist()
        self.log(
            LogLevel.INFO, f"Animation worker started for issue #{self.status.issue_number}"
        )

    def log(self, level: LogLevel, message: str) -> None:
        """Add log entry."""
        entry = LogEntry(level=level, message=message)
        self.status.logs.append(entry)
        self.status.updated_at = datetime.now()

        # Output to console with rich formatting
        style_map = {
            LogLevel.DEBUG: "dim",
            LogLevel.INFO: "blue",
            LogLevel.WARN: "yellow",
            LogLevel.ERROR: "red bold",
        }
        icon_map = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "🎬",
            LogLevel.WARN: "⚠️",
            LogLevel.ERROR: "❌",
        }

        console.print(
            f"{icon_map[level]} [{self.status.phase.value}] {message}",
            style=style_map[level],
        )

    async def set_phase(self, phase: AnimationPhase) -> None:
        """Update phase."""
        self.status.phase = phase
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"Phase changed to: {phase.value}")
        await self._persist()

    async def add_commit(self, sha: str) -> None:
        """Record a commit."""
        self.status.commits.append(sha)
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"Commit: {sha[:7]}")
        await self._persist()

    async def set_blocked(self, reason: str) -> None:
        """Mark as blocked - requires manager intervention."""
        self.status.phase = AnimationPhase.BLOCKED
        self.status.blocked_reason = reason
        self.status.updated_at = datetime.now()
        self.log(LogLevel.WARN, f"Blocked: {reason}")
        await self._persist()
        await self.notify_manager(NotificationType.BLOCKED, reason, requires_response=True)

    async def record_iteration(
        self,
        iteration_number: int,
        quality_score: int,
        verdict: str,
        issues: list[str],
        suggestions: list[str],
        blend_file: str | None = None,
        frames_dir: str | None = None,
    ) -> None:
        """Record an animation iteration result."""
        iteration = IterationStatus(
            iteration_number=iteration_number,
            quality_score=quality_score,
            verdict=verdict,
            issues=issues,
            suggestions=suggestions,
            blend_file=blend_file,
            frames_dir=frames_dir,
        )
        self.status.iterations.append(iteration)
        self.status.current_iteration = iteration_number
        self.status.updated_at = datetime.now()

        self.log(
            LogLevel.INFO,
            f"Iteration {iteration_number}: {verdict} (quality: {quality_score}/100)",
        )

        await self._persist()
        await self.notify_manager(
            NotificationType.ITERATION_COMPLETE,
            f"Iteration {iteration_number} complete: {verdict} (quality: {quality_score}/100)",
            requires_response=False,
            metadata={
                "iteration": iteration_number,
                "quality_score": quality_score,
                "verdict": verdict,
            },
        )

    async def set_final_result(
        self,
        quality_score: int,
        blend_file: str | None,
        frames_dir: str | None,
        roblox_export: str | None = None,
    ) -> None:
        """Set final animation result."""
        self.status.final_quality_score = quality_score
        self.status.final_blend_file = blend_file
        self.status.final_frames_dir = frames_dir
        self.status.roblox_export_path = roblox_export
        self.status.updated_at = datetime.now()
        await self._persist()

    def get_status(self) -> AnimationWorkerStatus:
        """Get current status."""
        return self.status.model_copy()

    async def _persist(self) -> None:
        """Persist status to file."""
        self.status_file_path.write_text(
            self.status.model_dump_json(indent=2),
            encoding="utf-8",
        )

    async def notify_manager(
        self,
        notification_type: NotificationType,
        message: str,
        requires_response: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send notification to manager."""
        if self.config.manager_notification_file is None:
            return

        notification = ManagerNotification(
            worker_pid=self.status.pid,
            issue_number=self.status.issue_number,
            notification_type=notification_type,
            message=message,
            requires_response=requires_response,
            metadata=metadata or {},
        )

        try:
            # Read existing notifications
            existing: list[dict[str, Any]] = []
            if self.config.manager_notification_file.exists():
                content = self.config.manager_notification_file.read_text(encoding="utf-8")
                if content.strip():
                    existing = json.loads(content)

            # Append new notification
            existing.append(notification.model_dump(mode="json"))

            # Write back
            self.config.manager_notification_file.write_text(
                json.dumps(existing, indent=2, default=str),
                encoding="utf-8",
            )
            self.log(LogLevel.DEBUG, f"Notified manager: {notification_type.value}")
        except Exception as e:
            self.log(LogLevel.ERROR, f"Failed to notify manager: {e}")
