"""
Escalation handling for manager agent.
Handles blocked workers, failures, and notifications.
"""

import json
from datetime import datetime
from pathlib import Path

from .models import (
    Escalation,
    IssueInfo,
    ManagerConfig,
    WorkerInfo,
)


class EscalationHandler:
    """
    Handles escalations from workers that need human attention.
    """

    def __init__(self, config: ManagerConfig) -> None:
        self.config = config
        self._escalations: list[Escalation] = []

    def _write_escalation(self, escalation: Escalation) -> None:
        """Write escalation to file for external monitoring."""
        if not self.config.escalation_file:
            return

        try:
            # Append to escalation file
            with open(self.config.escalation_file, "a") as f:
                f.write(escalation.model_dump_json() + "\n")
        except IOError as e:
            print(f"Failed to write escalation: {e}")

    def escalate_blocked(self, worker: WorkerInfo, issue: IssueInfo) -> Escalation:
        """Create an escalation for a blocked worker."""
        escalation = Escalation(
            issue_number=issue.number,
            worker_pid=worker.pid,
            escalation_type="blocked",
            message=f"Worker blocked on issue #{issue.number}: {worker.blocked_reason}",
            context={
                "issue_title": issue.title,
                "branch": worker.branch,
                "pr_number": worker.pr_number,
                "pr_url": worker.pr_url,
                "blocked_reason": worker.blocked_reason,
            },
        )

        self._escalations.append(escalation)
        self._write_escalation(escalation)

        if self.config.notify_on_block:
            self._notify(escalation)

        return escalation

    def escalate_failed(self, worker: WorkerInfo, issue: IssueInfo) -> Escalation:
        """Create an escalation for a failed worker."""
        escalation = Escalation(
            issue_number=issue.number,
            worker_pid=worker.pid,
            escalation_type="failed",
            message=f"Worker failed on issue #{issue.number}: {worker.error_message}",
            context={
                "issue_title": issue.title,
                "branch": worker.branch,
                "pr_number": worker.pr_number,
                "error_message": worker.error_message,
            },
        )

        self._escalations.append(escalation)
        self._write_escalation(escalation)

        return escalation

    def escalate_timeout(self, worker: WorkerInfo, issue: IssueInfo) -> Escalation:
        """Create an escalation for a timed-out worker."""
        escalation = Escalation(
            issue_number=issue.number,
            worker_pid=worker.pid,
            escalation_type="timeout",
            message=f"Worker timed out on issue #{issue.number} after {self.config.worker_timeout_hours}h",
            context={
                "issue_title": issue.title,
                "branch": worker.branch,
                "pr_number": worker.pr_number,
                "started_at": worker.started_at.isoformat(),
            },
        )

        self._escalations.append(escalation)
        self._write_escalation(escalation)

        return escalation

    def escalate_main_failure(
        self,
        worker: WorkerInfo,
        issue: IssueInfo,
        error_details: str,
    ) -> Escalation:
        """Create an escalation for main branch build failure after merge."""
        escalation = Escalation(
            issue_number=issue.number,
            worker_pid=worker.pid,
            escalation_type="main_failure",
            message=f"Main branch failed after merging PR #{worker.pr_number} for issue #{issue.number}",
            context={
                "issue_title": issue.title,
                "pr_number": worker.pr_number,
                "pr_url": worker.pr_url,
                "error_details": error_details,
            },
        )

        self._escalations.append(escalation)
        self._write_escalation(escalation)

        if self.config.notify_on_main_failure:
            self._notify(escalation)

        return escalation

    def _notify(self, escalation: Escalation) -> None:
        """Send notification for an escalation."""
        # For now, just print to console
        # Could be extended to send Slack/email/etc.
        print(f"\n{'='*60}")
        print(f"ESCALATION: {escalation.escalation_type.upper()}")
        print(f"Issue: #{escalation.issue_number}")
        print(f"Message: {escalation.message}")
        if escalation.context:
            print(f"Context: {json.dumps(escalation.context, indent=2, default=str)}")
        print(f"{'='*60}\n")

    def get_unresolved_escalations(self) -> list[Escalation]:
        """Get all unresolved escalations."""
        return [e for e in self._escalations if not e.resolved]

    def resolve_escalation(self, issue_number: int) -> None:
        """Mark escalations for an issue as resolved."""
        for escalation in self._escalations:
            if escalation.issue_number == issue_number:
                escalation.resolved = True

    def get_escalations_for_issue(self, issue_number: int) -> list[Escalation]:
        """Get all escalations for a specific issue."""
        return [e for e in self._escalations if e.issue_number == issue_number]
