"""
CLI for animation worker agent.
"""

import asyncio
import json
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from .agent import AnimationWorkerAgent
from .models import AnimationWorkerConfig

app = typer.Typer(
    name="animation-worker",
    help="Animation worker agent for creating Roblox animations with Gemini quality analysis",
)
console = Console()


@app.command()
def run(
    issue_number: int = typer.Argument(..., help="GitHub issue number with animation requirements"),
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
    output_dir: Path = typer.Option(
        Path.cwd() / ".animation-output",
        "--output-dir",
        "-o",
        help="Directory for animation output files",
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
    max_iterations: int = typer.Option(
        10,
        "--max-iterations",
        help="Maximum animation iterations",
    ),
    quality_threshold: int = typer.Option(
        85,
        "--quality-threshold",
        help="Minimum quality score (0-100)",
    ),
    fps: int = typer.Option(
        30,
        "--fps",
        help="Animation frames per second",
    ),
    duration: float = typer.Option(
        2.0,
        "--duration",
        help="Animation duration in seconds",
    ),
) -> None:
    """
    Run the animation worker to create an animation from a GitHub issue.

    The agent will:
    1. Read animation requirements from the GitHub issue
    2. Generate Blender animation code using Claude
    3. Create and render the animation
    4. Analyze quality with Gemini vision
    5. Iterate until quality threshold is met
    6. Export to Roblox format
    """
    load_dotenv()

    # Parse repo
    parts = repo.split("/")
    if len(parts) != 2:
        console.print("[red]Repository must be in owner/name format[/red]")
        raise typer.Exit(1)

    repo_owner, repo_name = parts

    # Get tokens
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        console.print("[red]GITHUB_TOKEN environment variable required[/red]")
        raise typer.Exit(1)

    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        console.print("[yellow]Warning: GEMINI_API_KEY not set, Gemini analysis will fail[/yellow]")

    config = AnimationWorkerConfig(
        github_token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        base_dir=base_dir.resolve(),
        worktree_base_dir=worktree_dir.resolve(),
        output_dir=output_dir.resolve(),
        status_dir=status_dir.resolve(),
        manager_notification_file=notification_file.resolve() if notification_file else None,
        max_iterations=max_iterations,
        quality_threshold=quality_threshold,
        fps=fps,
        duration=duration,
        gemini_api_key=gemini_api_key,
    )

    console.print(f"[bold blue]Starting animation worker for issue #{issue_number}[/bold blue]")
    console.print(f"Repository: {repo_owner}/{repo_name}")
    console.print(f"Output: {output_dir}")
    console.print(f"Quality threshold: {quality_threshold}/100")
    console.print(f"Max iterations: {max_iterations}")

    agent = AnimationWorkerAgent(config, issue_number)

    try:
        success = asyncio.run(agent.run())
        if success:
            console.print("[bold green]Animation worker completed successfully![/bold green]")
            raise typer.Exit(0)
        else:
            console.print("[bold red]Animation worker failed[/bold red]")
            raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("[yellow]Animation worker interrupted[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Animation worker crashed: {e}[/bold red]")
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
    """Check the status of a running or completed animation worker."""
    status_file = status_dir / f"animation-worker-{issue_number}.json"

    if not status_file.exists():
        console.print(f"[yellow]No status file found for issue #{issue_number}[/yellow]")
        raise typer.Exit(1)

    data = json.loads(status_file.read_text())

    console.print(f"[bold]Animation Worker Status for Issue #{issue_number}[/bold]")
    console.print(f"PID: {data['pid']}")
    console.print(f"Phase: {data['phase']}")
    console.print(f"Started: {data['started_at']}")
    console.print(f"Updated: {data['updated_at']}")

    console.print(f"\nCurrent Iteration: {data.get('current_iteration', 0)}")
    console.print(f"Final Quality Score: {data.get('final_quality_score', 0)}/100")

    if data.get("final_blend_file"):
        console.print(f"Final Blend: {data['final_blend_file']}")

    if data.get("roblox_export_path"):
        console.print(f"Roblox Export: {data['roblox_export_path']}")

    if data.get("blocked_reason"):
        console.print(f"[red]Blocked: {data['blocked_reason']}[/red]")

    # Show iteration history
    iterations = data.get("iterations", [])
    if iterations:
        console.print("\n[bold]Iteration History:[/bold]")
        for it in iterations:
            verdict_style = "green" if it["verdict"] == "done" else "yellow"
            console.print(
                f"  #{it['iteration_number']}: [{verdict_style}]{it['verdict']}[/{verdict_style}] "
                f"(quality: {it['quality_score']}/100)"
            )

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
    """List all animation worker status files."""
    if not status_dir.exists():
        console.print("[yellow]No status directory found[/yellow]")
        raise typer.Exit(0)

    status_files = list(status_dir.glob("animation-worker-*.json"))

    if not status_files:
        console.print("[yellow]No animation worker status files found[/yellow]")
        raise typer.Exit(0)

    console.print("[bold]Animation Workers:[/bold]")

    for sf in sorted(status_files):
        try:
            data = json.loads(sf.read_text())
            phase = data.get("phase", "unknown")
            issue = data.get("issue_number", "?")
            quality = data.get("final_quality_score", 0)
            iteration = data.get("current_iteration", 0)

            phase_style = {
                "completed": "green",
                "failed": "red",
                "blocked": "yellow",
            }.get(phase, "blue")

            console.print(
                f"  Issue #{issue}: [{phase_style}]{phase}[/{phase_style}] "
                f"(iteration {iteration}, quality {quality}/100)"
            )
        except Exception:
            console.print(f"  {sf.name}: [red]error reading[/red]")


if __name__ == "__main__":
    app()
