# Worker Agent

Autonomous worker agent using Claude Agent SDK for full PR lifecycle management.

## Purpose

This agent is invoked by a manager Claude Code session to handle the complete lifecycle of implementing a GitHub issue through to merge and main branch verification.

## Lifecycle

1. **Initialize**: Create git worktree for isolation
2. **Implement**: Use Claude Agent SDK to implement the feature
3. **Validate**: Run lint, typecheck, tests locally
4. **Create PR**: Push and open pull request
5. **Review Loop**: Wait for Claude GitHub integration review, address feedback
6. **CI Loop**: Wait for CI, fix failures
7. **Merge**: Squash merge when approved and green
8. **Verify Main**: Watch main branch build, report failures to manager

## Usage

```bash
# Run worker for an issue
worker run 42 --repo owner/repo

# Check status
worker status 42

# List all workers
worker list-workers
```

## Configuration

Environment variables:
- `GITHUB_TOKEN`: Required for GitHub API access
- `GITHUB_REPOSITORY`: Default repository (owner/name)

CLI options:
- `--base-dir`: Repository base directory
- `--worktree-dir`: Where to create git worktrees
- `--status-dir`: Where to write status files
- `--notification-file`: File for manager notifications
- `--auto-merge`: Auto-merge when checks pass
- `--coverage-threshold`: Minimum coverage percentage

## Monitoring

Status files are written to `--status-dir` as JSON:
- `worker-{issue}.json`: Full status including phase, commits, logs

Manager notifications written to `--notification-file`:
- `status_update`: Progress updates
- `permission_request`: Needs manager decision
- `blocked`: Cannot proceed
- `completed`: Successfully merged
- `failed`: Crashed or exhausted retries
- `main_branch_failed`: Merged but main build broke

## Key Behaviors

1. **Does NOT modify lint/typecheck/test configuration** unless absolutely necessary
2. **Commits frequently** for visibility and recovery
3. **Creates follow-up issues** for non-blocking review feedback
4. **Reports to manager** when blocked or when main fails
5. **Cleans up worktree** on completion

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
