"""
CLI for worker agent.
"""

import asyncio
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from .agent import WorkerAgent
from .models import WorkerConfig

app = typer.Typer(
    name="worker-agent",
    help="Autonomous worker agent for PR lifecycle management",
)
console = Console()


@app.command()
def run(
    issue_number: int = typer.Argument(..., help="GitHub issue number to implement"),
    repo: str = typer.Option(
        ...,
        "--repo",
        "-r",
        help="Repository in owner/name format",
        envvar="GITHUB_REPOSITORY",
    ),
    base_dir: Path = typer.Option(
        Path.cwd(),
        "--base-dir",
        "-d",
        help="Base directory of the repository",
    ),
    worktree_dir: Path = typer.Option(
        Path.cwd() / ".worktrees",
        "--worktree-dir",
        "-w",
        help="Directory for git worktrees",
    ),
    status_dir: Path = typer.Option(
        Path.cwd() / ".worker-status",
        "--status-dir",
        "-s",
        help="Directory for status files",
    ),
    notification_file: Path | None = typer.Option(
        None,
        "--notification-file",
        "-n",
        help="File for manager notifications",
    ),
    auto_merge: bool = typer.Option(
        False,
        "--auto-merge",
        help="Automatically merge when all checks pass",
    ),
    coverage_threshold: int = typer.Option(
        70,
        "--coverage-threshold",
        help="Minimum code coverage percentage",
    ),
) -> None:
    """
    Run the worker agent to implement a GitHub issue.

    The agent will:
    1. Create a git worktree for isolation
    2. Implement the feature using Claude Agent SDK
    3. Run local validation (lint, typecheck, tests)
    4. Create a PR
    5. Wait for Claude GitHub integration review
    6. Address feedback and iterate
    7. Merge when approved and CI passes
    8. Verify main branch build succeeds
    """
    load_dotenv()

    # Parse repo
    parts = repo.split("/")
    if len(parts) != 2:
        console.print("[red]Repository must be in owner/name format[/red]")
        raise typer.Exit(1)

    repo_owner, repo_name = parts

    # Get GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        console.print("[red]GITHUB_TOKEN environment variable required[/red]")
        raise typer.Exit(1)

    config = WorkerConfig(
        github_token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        base_dir=base_dir.resolve(),
        worktree_base_dir=worktree_dir.resolve(),
        status_dir=status_dir.resolve(),
        manager_notification_file=notification_file.resolve() if notification_file else None,
        auto_merge=auto_merge,
        coverage_threshold=coverage_threshold,
    )

    console.print(f"[bold blue]Starting worker agent for issue #{issue_number}[/bold blue]")
    console.print(f"Repository: {repo_owner}/{repo_name}")
    console.print(f"Worktree: {worktree_dir}")
    console.print(f"Status: {status_dir}")

    agent = WorkerAgent(config, issue_number)

    try:
        success = asyncio.run(agent.run())
        if success:
            console.print("[bold green]Worker agent completed successfully![/bold green]")
            raise typer.Exit(0)
        else:
            console.print("[bold red]Worker agent failed or was blocked[/bold red]")
            raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("[yellow]Worker agent interrupted[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Worker agent crashed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def status(
    issue_number: int = typer.Argument(..., help="Issue number to check status for"),
    status_dir: Path = typer.Option(
        Path.cwd() / ".worker-status",
        "--status-dir",
        "-s",
        help="Directory for status files",
    ),
) -> None:
    """Check the status of a running or completed worker agent."""
    import json

    status_file = status_dir / f"worker-{issue_number}.json"

    if not status_file.exists():
        console.print(f"[yellow]No status file found for issue #{issue_number}[/yellow]")
        raise typer.Exit(1)

    data = json.loads(status_file.read_text())

    console.print(f"[bold]Worker Status for Issue #{issue_number}[/bold]")
    console.print(f"PID: {data['pid']}")
    console.print(f"Phase: {data['phase']}")
    console.print(f"Branch: {data['branch']}")
    console.print(f"Started: {data['started_at']}")
    console.print(f"Updated: {data['updated_at']}")

    if data.get("pr_number"):
        console.print(f"PR: #{data['pr_number']} - {data.get('pr_url', '')}")

    if data.get("review_status"):
        console.print(f"Review: {data['review_status']}")

    if data.get("ci_status"):
        console.print(f"CI: {data['ci_status']}")

    if data.get("blocked_reason"):
        console.print(f"[red]Blocked: {data['blocked_reason']}[/red]")

    console.print(f"Commits: {len(data.get('commits', []))}")
    console.print(f"Created Issues: {data.get('created_issues', [])}")

    # Show recent logs
    logs = data.get("logs", [])[-10:]
    if logs:
        console.print("\n[bold]Recent Logs:[/bold]")
        for log in logs:
            style = {"debug": "dim", "info": "blue", "warn": "yellow", "error": "red"}
            console.print(f"  [{log['level']}] {log['message']}", style=style.get(log["level"]))


@app.command()
def list_workers(
    status_dir: Path = typer.Option(
        Path.cwd() / ".worker-status",
        "--status-dir",
        "-s",
        help="Directory for status files",
    ),
) -> None:
    """List all worker agent status files."""
    import json

    if not status_dir.exists():
        console.print("[yellow]No status directory found[/yellow]")
        raise typer.Exit(0)

    status_files = list(status_dir.glob("worker-*.json"))

    if not status_files:
        console.print("[yellow]No worker status files found[/yellow]")
        raise typer.Exit(0)

    console.print("[bold]Worker Agents:[/bold]")

    for sf in sorted(status_files):
        try:
            data = json.loads(sf.read_text())
            phase = data.get("phase", "unknown")
            issue = data.get("issue_number", "?")
            pr = data.get("pr_number")

            phase_style = {
                "completed": "green",
                "failed": "red",
                "blocked": "yellow",
            }.get(phase, "blue")

            pr_str = f" PR#{pr}" if pr else ""
            console.print(f"  Issue #{issue}: [{phase_style}]{phase}[/{phase_style}]{pr_str}")
        except Exception:
            console.print(f"  {sf.name}: [red]error reading[/red]")


if __name__ == "__main__":
    app()
