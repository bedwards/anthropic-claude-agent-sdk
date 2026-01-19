"""
Main manager agent orchestration.
Coordinates issue monitoring, worker spawning, and escalation handling.
"""

import asyncio
import os
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.table import Table

from .escalation_handler import EscalationHandler
from .github_monitor import GitHubMonitor
from .models import (
    IssueStatus,
    ManagerConfig,
    ManagerStatus,
    WorkerState,
)
from .worker_pool import WorkerPool


class Manager:
    """
    Main manager agent that orchestrates the worker pool.
    """

    def __init__(self, config: ManagerConfig) -> None:
        self.config = config
        self.console = Console()
        self.github_monitor = GitHubMonitor(config)
        self.worker_pool = WorkerPool(config)
        self.escalation_handler = EscalationHandler(config)
        self.status = ManagerStatus(pid=os.getpid())
        self._running = False

    def _create_status_table(self) -> Table:
        """Create a rich table showing current status."""
        table = Table(title="Manager Agent Status")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Issues Tracked", str(self.status.issues_tracked))
        table.add_row("Workers Active", str(self.status.workers_active))
        table.add_row("Workers Completed", str(self.status.workers_completed))
        table.add_row("Workers Failed", str(self.status.workers_failed))
        table.add_row("PRs Merged", str(self.status.prs_merged))
        table.add_row("Main Failures", str(self.status.main_failures))

        # Add worker details
        workers = self.worker_pool.get_active_workers()
        if workers:
            table.add_section()
            table.add_row("[bold]Active Workers[/bold]", "")
            for worker in workers:
                status = f"Issue #{worker.issue_number}"
                if worker.pr_number:
                    status += f" (PR #{worker.pr_number})"
                table.add_row(f"  PID {worker.pid}", status)

        # Add blocked workers
        blocked = self.worker_pool.get_blocked_workers()
        if blocked:
            table.add_section()
            table.add_row("[bold red]Blocked Workers[/bold red]", "")
            for worker in blocked:
                table.add_row(
                    f"  Issue #{worker.issue_number}",
                    worker.blocked_reason or "Unknown",
                )

        return table

    async def _process_new_issues(self) -> None:
        """Poll for and process new issues."""
        new_issues = await self.github_monitor.poll_issues()

        for issue in new_issues:
            self.console.print(
                f"[green]New issue discovered:[/green] #{issue.number} - {issue.title}"
            )
            self.console.print(f"  Complexity: {issue.complexity}")

        self.status.issues_tracked = len(self.github_monitor.get_tracked_issues())

    async def _assign_workers(self) -> None:
        """Assign workers to ready issues."""
        available = self.worker_pool.available_slots()
        if available <= 0:
            return

        # Get issues ready for assignment
        ready_issues = self.github_monitor.get_assignable_issues()

        for issue in ready_issues[:available]:
            self.console.print(
                f"[cyan]Spawning worker for issue #{issue.number}:[/cyan] {issue.title}"
            )

            worker = await self.worker_pool.spawn_worker(issue)
            if worker:
                self.github_monitor.update_issue_status(
                    issue.number,
                    IssueStatus.ASSIGNED,
                    assigned_worker_pid=worker.pid,
                )
                self.console.print(f"  Worker spawned with PID {worker.pid}")
            else:
                self.console.print("  [red]Failed to spawn worker[/red]")

    async def _monitor_workers(self) -> None:
        """Monitor workers and handle state changes."""
        changed = await self.worker_pool.poll_workers()

        for worker in changed:
            issue = self.github_monitor.get_issue(worker.issue_number)
            if not issue:
                continue

            if worker.state == WorkerState.RUNNING:
                self.github_monitor.update_issue_status(
                    worker.issue_number,
                    IssueStatus.IN_PROGRESS,
                    pr_number=worker.pr_number,
                    pr_url=worker.pr_url,
                )

            elif worker.state == WorkerState.BLOCKED:
                self.console.print(
                    f"[yellow]Worker blocked on issue #{worker.issue_number}:[/yellow] "
                    f"{worker.blocked_reason}"
                )
                self.github_monitor.update_issue_status(
                    worker.issue_number, IssueStatus.BLOCKED
                )
                self.escalation_handler.escalate_blocked(worker, issue)
                self.worker_pool.cleanup_worker(worker.issue_number)

            elif worker.state == WorkerState.COMPLETED:
                self.console.print(
                    f"[green]Worker completed issue #{worker.issue_number}![/green]"
                )
                if worker.pr_number:
                    self.console.print(f"  PR #{worker.pr_number} merged")
                self.github_monitor.update_issue_status(
                    worker.issue_number,
                    IssueStatus.COMPLETED,
                    pr_number=worker.pr_number,
                    pr_url=worker.pr_url,
                )
                self.status.workers_completed += 1
                self.status.prs_merged += 1
                self.worker_pool.cleanup_worker(worker.issue_number)

            elif worker.state == WorkerState.FAILED:
                self.console.print(
                    f"[red]Worker failed on issue #{worker.issue_number}:[/red] "
                    f"{worker.error_message}"
                )
                self.github_monitor.update_issue_status(
                    worker.issue_number, IssueStatus.FAILED
                )
                self.escalation_handler.escalate_failed(worker, issue)
                self.status.workers_failed += 1
                self.worker_pool.cleanup_worker(worker.issue_number)

        # Check for timed out workers
        timed_out = self.worker_pool.get_timed_out_workers()
        for worker in timed_out:
            issue = self.github_monitor.get_issue(worker.issue_number)
            if issue:
                self.console.print(
                    f"[yellow]Worker timed out on issue #{worker.issue_number}[/yellow]"
                )
                self.escalation_handler.escalate_timeout(worker, issue)
                await self.worker_pool.kill_worker(worker.issue_number)
                self.github_monitor.update_issue_status(
                    worker.issue_number, IssueStatus.FAILED
                )
                self.status.workers_failed += 1
                self.worker_pool.cleanup_worker(worker.issue_number)

        # Update status counts
        self.status.workers_active = len(self.worker_pool.get_active_workers())

    async def run(self, once: bool = False) -> None:
        """
        Run the manager agent loop.

        Args:
            once: If True, run once and exit (for testing)
        """
        self._running = True
        self.console.print("[bold green]Manager agent started[/bold green]")
        self.console.print(f"  Repo: {self.config.repo_owner}/{self.config.repo_name}")
        self.console.print(f"  Max workers: {self.config.max_concurrent_workers}")

        try:
            while self._running:
                self.status.last_poll = datetime.now()

                # Process new issues
                await self._process_new_issues()

                # Assign workers to ready issues
                await self._assign_workers()

                # Monitor existing workers
                await self._monitor_workers()

                if once:
                    break

                # Wait before next poll
                await asyncio.sleep(self.config.issue_poll_seconds)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Shutting down manager agent...[/yellow]")
        finally:
            self._running = False

    def stop(self) -> None:
        """Stop the manager agent."""
        self._running = False

    async def run_with_dashboard(self) -> None:
        """Run the manager with a live dashboard display."""
        self._running = True

        with Live(self._create_status_table(), refresh_per_second=1) as live:
            try:
                while self._running:
                    self.status.last_poll = datetime.now()

                    await self._process_new_issues()
                    await self._assign_workers()
                    await self._monitor_workers()

                    live.update(self._create_status_table())

                    await asyncio.sleep(self.config.issue_poll_seconds)
            except KeyboardInterrupt:
                pass
            finally:
                self._running = False
