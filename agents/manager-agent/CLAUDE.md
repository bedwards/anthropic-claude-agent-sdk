# Manager Agent

Orchestrator that monitors GitHub issues and spawns worker agents for autonomous PR lifecycle management.

## Purpose

The manager agent is the central coordinator that:
- Watches for new issues with appropriate labels
- Triages issues by complexity
- Spawns worker agents for suitable issues
- Monitors worker progress and handles escalations
- Reports metrics and status

## Architecture

```
Manager Agent
├── GitHubMonitor     - Polls for new issues, tracks state
├── WorkerPool        - Spawns/monitors worker processes
├── EscalationHandler - Handles blocked workers, failures
└── CLI               - Command-line interface
```

## Usage

```bash
# Run manager agent
manager run owner/repo

# Run with live dashboard
manager run owner/repo --dashboard

# Check status
manager status

# List open issues
manager list-issues owner/repo --labels "bug,enhancement"
```

## Configuration

Environment variables:
- `GITHUB_TOKEN`: Required for GitHub API access

CLI options:
- `--base-dir`: Repository base directory
- `--worktree-dir`: Where workers create git worktrees
- `--status-dir`: Where status files are written
- `--max-workers`: Maximum concurrent workers (default: 3)
- `--auto-assign-labels`: Labels that trigger auto-assignment

## Issue Selection

Issues are auto-assigned to workers if they:
1. Have labels in `auto_assign_labels` (default: good-first-issue, bug, enhancement)
2. Do NOT have labels in `skip_labels` (wontfix, duplicate, invalid, manual)
3. Are not already linked to a PR
4. Are not marked as EPIC complexity

## Complexity Estimation

Issues are triaged by complexity:
- **TRIVIAL**: Typos, simple fixes, labeled "good-first-issue"
- **SMALL**: Small features, short body text
- **MEDIUM**: Moderate features, medium body text
- **LARGE**: Large features, long body text, "refactor" keywords
- **EPIC**: Labeled "epic", requires breakdown

## Worker Lifecycle

1. Manager discovers new issue matching criteria
2. Manager spawns worker agent with issue number
3. Worker runs in isolated worktree
4. Worker writes status to JSON file
5. Manager polls status file for progress
6. On completion/failure, manager updates tracking

## Escalations

The manager creates escalations for:
- **Blocked workers**: Merge conflicts, review blockers
- **Failed workers**: Crashes, exhausted retries
- **Timeouts**: Workers exceeding time limit
- **Main branch failures**: Build failures after merge

Escalations are written to `escalation_file` and printed to console.

## Monitoring

Status files in `--status-dir`:
- `worker-{issue}.json`: Individual worker status

Use `manager status` to view current state.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run mypy .
```
