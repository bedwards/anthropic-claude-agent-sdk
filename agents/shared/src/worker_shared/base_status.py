"""
Base status manager for worker agents.

Handles logging, status persistence, and manager notifications.
Specific workers extend this with their own status types.
"""

import json
import os
from datetime import datetime
from typing import Any, Generic, TypeVar

from rich.console import Console

from .base_models import (
    BaseWorkerConfig,
    BaseWorkerStatus,
    LogEntry,
    LogLevel,
    ManagerNotification,
    NotificationType,
)

console = Console()

ConfigT = TypeVar("ConfigT", bound=BaseWorkerConfig)
StatusT = TypeVar("StatusT", bound=BaseWorkerStatus)


class BaseStatusManager(Generic[ConfigT, StatusT]):
    """
    Base status manager for worker agents.

    Manages worker status persistence and logging.
    Provides monitoring capabilities for manager and external tools.
    """

    config: ConfigT
    status: StatusT

    def __init__(
        self,
        config: ConfigT,
        issue_number: int,
        branch: str,
        worktree_path: str,
        status_class: type[StatusT],
        initial_phase: str,
    ) -> None:
        self.config = config
        self.status_file_path = config.status_dir / f"worker-{issue_number}.json"

        self.status = status_class(
            pid=os.getpid(),
            issue_number=issue_number,
            branch=branch,
            worktree_path=worktree_path,
            phase=initial_phase,
        )

    async def initialize(self) -> None:
        """Initialize status file - creates directory if needed."""
        self.config.status_dir.mkdir(parents=True, exist_ok=True)
        await self._persist()
        self.log(LogLevel.INFO, f"Worker agent started for issue #{self.status.issue_number}")

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
            LogLevel.INFO: "📋",
            LogLevel.WARN: "⚠️",
            LogLevel.ERROR: "❌",
        }

        console.print(
            f"{icon_map[level]} [{self.status.phase}] {message}",
            style=style_map[level],
        )

    async def set_phase(self, phase: str) -> None:
        """Update phase."""
        self.status.phase = phase
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"Phase changed to: {phase}")
        await self._persist()

    async def add_commit(self, sha: str) -> None:
        """Record a commit."""
        self.status.commits.append(sha)
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"Commit: {sha[:7]}")
        await self._persist()

    async def set_blocked(self, reason: str) -> None:
        """Mark as blocked - requires manager intervention."""
        self.status.phase = "blocked"
        self.status.blocked_reason = reason
        self.status.updated_at = datetime.now()
        self.log(LogLevel.WARN, f"Blocked: {reason}")
        await self._persist()
        await self.notify_manager(NotificationType.BLOCKED, reason, requires_response=True)

    def get_status(self) -> StatusT:
        """Get current status."""
        return self.status.model_copy()  # type: ignore[return-value]

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
