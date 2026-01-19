"""
Status manager for worker agent.
Handles logging, status persistence, and manager notifications.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from .models import (
    CIStatus,
    LogEntry,
    LogLevel,
    ManagerNotification,
    NotificationType,
    ReviewStatus,
    WorkerConfig,
    WorkerPhase,
    WorkerStatus,
)

console = Console()


class StatusManager:
    """
    Manages worker status persistence and logging.
    Provides monitoring capabilities for manager and external tools.
    """

    def __init__(
        self,
        config: WorkerConfig,
        issue_number: int,
        branch: str,
        worktree_path: str,
    ) -> None:
        self.config = config
        self.status_file_path = config.status_dir / f"worker-{issue_number}.json"

        self.status = WorkerStatus(
            pid=os.getpid(),
            issue_number=issue_number,
            branch=branch,
            worktree_path=worktree_path,
        )

    async def initialize(self) -> None:
        """Initialize status file - creates directory if needed."""
        self.config.status_dir.mkdir(parents=True, exist_ok=True)
        self.status.dry_run = self.config.dry_run
        await self._persist()
        self.log(LogLevel.INFO, f"Worker agent started for issue #{self.status.issue_number}")
        if self.config.dry_run:
            self.log(LogLevel.INFO, "🔍 Running in DRY-RUN mode - no actual changes will be made")

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
            f"{icon_map[level]} [{self.status.phase.value}] {message}",
            style=style_map[level],
        )

        # Persist asynchronously (fire and forget for non-critical updates)
        # In practice, we'll call _persist explicitly at key points

    async def set_phase(self, phase: WorkerPhase) -> None:
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

    async def set_pr(self, pr_number: int, pr_url: str) -> None:
        """Set PR information."""
        self.status.pr_number = pr_number
        self.status.pr_url = pr_url
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"PR created: #{pr_number} - {pr_url}")
        await self._persist()

    async def set_review_status(self, status: ReviewStatus) -> None:
        """Update review status."""
        self.status.review_status = status
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"Review status: {status.value}")
        await self._persist()

    async def set_ci_status(self, status: CIStatus) -> None:
        """Update CI status."""
        self.status.ci_status = status
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"CI status: {status.value}")
        await self._persist()

    async def set_blocked(self, reason: str) -> None:
        """Mark as blocked - requires manager intervention."""
        self.status.phase = WorkerPhase.BLOCKED
        self.status.blocked_reason = reason
        self.status.updated_at = datetime.now()
        self.log(LogLevel.WARN, f"Blocked: {reason}")
        await self._persist()
        await self.notify_manager(NotificationType.BLOCKED, reason, requires_response=True)

    async def set_main_branch_verified(self, verified: bool) -> None:
        """Set whether main branch build was verified."""
        self.status.main_branch_verified = verified
        self.status.updated_at = datetime.now()
        await self._persist()

    async def add_created_issue(self, issue_number: int) -> None:
        """Record created issue."""
        self.status.created_issues.append(issue_number)
        self.status.updated_at = datetime.now()
        self.log(LogLevel.INFO, f"Created issue #{issue_number} for non-blocking feedback")
        await self._persist()

    def get_status(self) -> WorkerStatus:
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
