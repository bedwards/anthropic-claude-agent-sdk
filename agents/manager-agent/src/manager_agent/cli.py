"""
CLI for manager agent.
"""

import asyncio
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .manager import Manager
from .models import ManagerConfig

load_dotenv()

app = typer.Typer(
    name="manager",
    help="Manager agent for orchestrating worker agents",
)

console = Console()


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        console.print("[red]GITHUB_TOKEN environment variable required[/red]")
        raise typer.Exit(1)
    return token


@app.command()
def run(
    repo: str = typer.Argument(
        ...,
        help="Repository in owner/name format",
    ),
    base_dir: Path | None = typer.Option(
        None,
        "--base-dir",
        "-b",
        help="Base directory for the repository (default: current directory)",
    ),
    worktree_dir: Path | None = typer.Option(
        None,
        "--worktree-dir",
        "-w",
        help="Directory for git worktrees (default: .worktrees)",
    ),
    status_dir: Path | None = typer.Option(
        None,
        "--status-dir",
        "-s",
        help="Directory for status files (default: .manager-status)",
    ),
    max_workers: int = typer.Option(
        3,
        "--max-workers",
        "-m",
        help="Maximum concurrent workers",
    ),
    dashboard: bool = typer.Option(
        False,
        "--dashboard",
        "-d",
        help="Show live dashboard",
    ),
    once: bool = typer.Option(
        False,
        "--once",
        help="Run once and exit (for testing)",
    ),
    auto_assign_labels: str | None = typer.Option(
        None,
        "--auto-assign-labels",
        help="Comma-separated labels to auto-assign (default: good-first-issue,bug,enhancement)",
    ),
) -> None:
    """Run the manager agent to orchestrate workers."""
    github_token = get_github_token()

    # Parse repo
    parts = repo.split("/")
    if len(parts) != 2:
        console.print("[red]Repository must be in owner/name format[/red]")
        raise typer.Exit(1)
    repo_owner, repo_name = parts

    # Set defaults
    if base_dir is None:
        base_dir = Path.cwd()
    if worktree_dir is None:
        worktree_dir = base_dir / ".worktrees"
    if status_dir is None:
        status_dir = base_dir / ".manager-status"

    # Create directories
    worktree_dir.mkdir(parents=True, exist_ok=True)
    status_dir.mkdir(parents=True, exist_ok=True)

    # Parse auto-assign labels
    labels = None
    if auto_assign_labels:
        labels = [l.strip() for l in auto_assign_labels.split(",")]

    config = ManagerConfig(
        github_token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        base_dir=base_dir.resolve(),
        worktree_base_dir=worktree_dir.resolve(),
        status_dir=status_dir.resolve(),
        max_concurrent_workers=max_workers,
        auto_assign_labels=labels or ["good-first-issue", "bug", "enhancement"],
    )

    console.print("[bold]Starting manager agent[/bold]")
    console.print(f"  Repository: {repo_owner}/{repo_name}")
    console.print(f"  Worktrees: {worktree_dir}")
    console.print(f"  Status: {status_dir}")
    console.print(f"  Max workers: {max_workers}")
    console.print()

    manager = Manager(config)

    if dashboard:
        asyncio.run(manager.run_with_dashboard())
    else:
        asyncio.run(manager.run(once=once))


@app.command()
def status(
    status_dir: Path | None = typer.Option(
        None,
        "--status-dir",
        "-s",
        help="Directory for status files (default: .manager-status)",
    ),
) -> None:
    """Show current manager and worker status."""
    if status_dir is None:
        status_dir = Path.cwd() / ".manager-status"

    if not status_dir.exists():
        console.print("[yellow]No status directory found[/yellow]")
        raise typer.Exit(0)

    # Find worker status files
    worker_files = list(status_dir.glob("worker-*.json"))

    if not worker_files:
        console.print("[yellow]No active workers found[/yellow]")
        raise typer.Exit(0)

    import json

    table = Table(title="Worker Status")
    table.add_column("Issue", style="cyan")
    table.add_column("Phase", style="green")
    table.add_column("PR", style="blue")
    table.add_column("Status")

    for f in sorted(worker_files):
        try:
            with open(f) as fp:
                data = json.load(fp)

            issue = f"#{data.get('issue_number', '?')}"
            phase = data.get("phase", "unknown")
            pr_number = data.get("pr_number")
            blocked = data.get("blocked_reason")

            pr_str = f"#{pr_number}" if pr_number else "-"
            if blocked:
                status_str = f"[red]BLOCKED: {blocked}[/red]"
            elif phase == "completed":
                status_str = "[green]COMPLETED[/green]"
            elif phase == "failed":
                status_str = "[red]FAILED[/red]"
            else:
                status_str = "[yellow]IN PROGRESS[/yellow]"

            table.add_row(issue, phase, pr_str, status_str)
        except (OSError, json.JSONDecodeError):
            continue

    console.print(table)


@app.command()
def list_issues(
    repo: str = typer.Argument(
        ...,
        help="Repository in owner/name format",
    ),
    labels: str | None = typer.Option(
        None,
        "--labels",
        "-l",
        help="Filter by labels (comma-separated)",
    ),
) -> None:
    """List open issues that could be assigned to workers."""
    from github import Github

    github_token = get_github_token()

    parts = repo.split("/")
    if len(parts) != 2:
        console.print("[red]Repository must be in owner/name format[/red]")
        raise typer.Exit(1)
    repo_owner, repo_name = parts

    gh = Github(github_token)
    repository = gh.get_repo(f"{repo_owner}/{repo_name}")

    table = Table(title=f"Open Issues - {repo}")
    table.add_column("#", style="cyan")
    table.add_column("Title")
    table.add_column("Labels", style="green")
    table.add_column("Created")

    label_filter = None
    if labels:
        label_filter = set(l.strip().lower() for l in labels.split(","))

    issues = repository.get_issues(state="open", sort="created", direction="desc")

    for issue in issues:
        # Skip PRs
        if issue.pull_request is not None:
            continue

        issue_labels = [l.name for l in issue.labels]
        issue_labels_lower = set(l.lower() for l in issue_labels)

        # Filter by labels if specified
        if label_filter and not label_filter.intersection(issue_labels_lower):
            continue

        table.add_row(
            str(issue.number),
            issue.title[:60] + "..." if len(issue.title) > 60 else issue.title,
            ", ".join(issue_labels[:3]),
            issue.created_at.strftime("%Y-%m-%d"),
        )

    console.print(table)


if __name__ == "__main__":
    app()
