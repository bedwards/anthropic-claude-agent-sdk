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

# Run in dry-run mode (simulate without making actual changes)
worker run 42 --repo owner/repo --dry-run

# Check status
worker status 42

# List all workers
worker list-workers
```

### Dry-Run Mode

Dry-run mode simulates the full worker agent lifecycle without making actual changes:

**What is simulated:**
- Git operations (commit, push, rebase) - logged but not executed
- GitHub API writes (PR creation, merging, issue creation) - no actual API calls
- Claude SDK interactions - mocked with simulated responses
- All phases of the lifecycle with realistic timing

**What still happens:**
- Worktree directory is created (for file operations)
- GitHub reads are allowed (fetching issue details)
- Status file is written with `dry_run: true` flag
- Detailed logging of all simulated actions with `[DRY-RUN]` prefix

**Use cases:**
- Test configuration before real runs
- Debug agent behavior without side effects
- Training and demonstrations
- Verify issue parsing and workflow logic

**Example:**
```bash
# Test the agent on issue #12
worker run 12 --repo myorg/myrepo --dry-run

# Check the simulated status
worker status 12
# Output will show: Mode: DRY-RUN (simulated)
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
- `--dry-run`: Simulate without making actual changes (no git pushes or GitHub writes)

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
