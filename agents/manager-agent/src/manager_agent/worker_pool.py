"""
Worker pool management for manager agent.
Spawns, monitors, and manages worker agent processes.
"""

import asyncio
import json
import os
import signal
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from .models import (
    IssueInfo,
    IssueStatus,
    ManagerConfig,
    WorkerInfo,
    WorkerState,
)


class WorkerPool:
    """
    Manages a pool of worker agent processes.
    """

    def __init__(self, config: ManagerConfig) -> None:
        self.config = config
        self._workers: dict[int, WorkerInfo] = {}  # pid -> WorkerInfo
        self._issue_to_worker: dict[int, int] = {}  # issue_number -> pid

    def _get_worker_status_file(self, issue_number: int) -> Path:
        """Get the status file path for a worker."""
        return self.config.status_dir / f"worker-{issue_number}.json"

    def _read_worker_status(self, status_file: Path) -> dict | None:
        """Read worker status from file."""
        try:
            if status_file.exists():
                with open(status_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return None

    async def spawn_worker(self, issue: IssueInfo) -> WorkerInfo | None:
        """
        Spawn a new worker agent for an issue.
        Returns WorkerInfo if successful, None if failed.
        """
        if issue.number in self._issue_to_worker:
            # Worker already exists for this issue
            return self._workers.get(self._issue_to_worker[issue.number])

        if len(self._workers) >= self.config.max_concurrent_workers:
            # Pool is full
            return None

        status_file = self._get_worker_status_file(issue.number)

        # Build worker command
        cmd = [
            "worker",
            "run",
            str(issue.number),
            "--repo",
            f"{self.config.repo_owner}/{self.config.repo_name}",
            "--base-dir",
            str(self.config.base_dir),
            "--worktree-dir",
            str(self.config.worktree_base_dir),
            "--status-dir",
            str(self.config.status_dir),
        ]

        # Set environment
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = self.config.github_token

        try:
            # Spawn worker process
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Detach from parent
            )

            worker = WorkerInfo(
                pid=process.pid,
                issue_number=issue.number,
                branch=f"worker/issue-{issue.number}",
                state=WorkerState.STARTING,
                status_file=status_file,
            )

            self._workers[process.pid] = worker
            self._issue_to_worker[issue.number] = process.pid

            return worker

        except Exception as e:
            print(f"Failed to spawn worker for issue #{issue.number}: {e}")
            return None

    async def poll_workers(self) -> list[WorkerInfo]:
        """
        Poll all workers and update their state.
        Returns list of workers that have state changes.
        """
        changed: list[WorkerInfo] = []

        for pid, worker in list(self._workers.items()):
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 = check if process exists
                process_alive = True
            except OSError:
                process_alive = False

            # Read status file
            status = self._read_worker_status(worker.status_file)

            old_state = worker.state

            if status:
                worker.last_heartbeat = datetime.now()

                # Update from status file
                phase = status.get("phase", "")
                blocked_reason = status.get("blocked_reason")
                pr_number = status.get("pr_number")
                pr_url = status.get("pr_url")

                if pr_number:
                    worker.pr_number = pr_number
                    worker.pr_url = pr_url

                if blocked_reason:
                    worker.state = WorkerState.BLOCKED
                    worker.blocked_reason = blocked_reason
                elif phase == "completed":
                    worker.state = WorkerState.COMPLETED
                elif phase == "failed":
                    worker.state = WorkerState.FAILED
                    worker.error_message = status.get("error_message")
                elif not process_alive:
                    # Process died but status doesn't show failure
                    worker.state = WorkerState.FAILED
                    worker.error_message = "Process terminated unexpectedly"
                else:
                    worker.state = WorkerState.RUNNING
            elif not process_alive:
                worker.state = WorkerState.FAILED
                worker.error_message = "Process terminated without status"

            if worker.state != old_state:
                changed.append(worker)

        return changed

    def get_worker(self, issue_number: int) -> WorkerInfo | None:
        """Get worker for a specific issue."""
        pid = self._issue_to_worker.get(issue_number)
        if pid:
            return self._workers.get(pid)
        return None

    def get_active_workers(self) -> list[WorkerInfo]:
        """Get all active (running or starting) workers."""
        return [
            w
            for w in self._workers.values()
            if w.state in (WorkerState.STARTING, WorkerState.RUNNING)
        ]

    def get_blocked_workers(self) -> list[WorkerInfo]:
        """Get all blocked workers."""
        return [w for w in self._workers.values() if w.state == WorkerState.BLOCKED]

    def get_completed_workers(self) -> list[WorkerInfo]:
        """Get all completed workers."""
        return [w for w in self._workers.values() if w.state == WorkerState.COMPLETED]

    def get_failed_workers(self) -> list[WorkerInfo]:
        """Get all failed workers."""
        return [w for w in self._workers.values() if w.state == WorkerState.FAILED]

    def cleanup_worker(self, issue_number: int) -> None:
        """Remove a worker from tracking (after completion/failure handled)."""
        pid = self._issue_to_worker.pop(issue_number, None)
        if pid:
            self._workers.pop(pid, None)

    async def kill_worker(self, issue_number: int) -> bool:
        """Kill a worker process."""
        pid = self._issue_to_worker.get(issue_number)
        if not pid:
            return False

        try:
            os.kill(pid, signal.SIGTERM)
            await asyncio.sleep(2)

            # Check if still running
            try:
                os.kill(pid, 0)
                # Still running, force kill
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass  # Already dead

            return True
        except OSError:
            return False

    def get_timed_out_workers(self) -> list[WorkerInfo]:
        """Get workers that have exceeded the timeout."""
        timeout = timedelta(hours=self.config.worker_timeout_hours)
        now = datetime.now()

        return [
            w
            for w in self._workers.values()
            if w.state in (WorkerState.STARTING, WorkerState.RUNNING)
            and (now - w.started_at) > timeout
        ]

    def available_slots(self) -> int:
        """Get number of available worker slots."""
        active = len(self.get_active_workers())
        return max(0, self.config.max_concurrent_workers - active)
