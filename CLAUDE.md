# CLAUDE.md

## Project Overview

Documentation website for the Claude Agent SDK, hosted on GitHub Pages from the `docs/` folder.

## Repository Structure

```
├── docs/                 # GitHub Pages site (static HTML)
│   ├── index.html       # Landing page
│   ├── essay.html       # Main essay (~5,000 words)
│   ├── worker-agent.html # Worker agent essay (~3,500 words)
│   ├── styles.css       # Stylesheet
│   └── .nojekyll        # Disables Jekyll processing
├── docs-for-claude/      # Knowledge base for Claude sessions
│   ├── INDEX.md         # Section index with line numbers (read first)
│   └── claude-agent-sdk-knowledge.md  # Full knowledge base (~660 lines)
├── agents/
│   └── worker-agent/    # Autonomous worker agent implementation
│       ├── pyproject.toml
│       ├── src/worker_agent/
│       │   ├── models.py          # Pydantic models
│       │   ├── status_manager.py  # Logging and status persistence
│       │   ├── git_manager.py     # Git worktree operations
│       │   ├── github_manager.py  # GitHub API operations
│       │   ├── agent.py           # Main orchestration
│       │   └── cli.py             # Command-line interface
│       └── tests/
├── scripts/
│   └── calculate_reading_time.py  # Word count and reading time utility
├── raw-docs-source/     # Source material (not published)
└── README.md
```

## Retrieving Knowledge in Future Sessions

When you need information about the Claude Agent SDK:

1. **Read the index first**: `Read("docs-for-claude/INDEX.md")`
2. **Find the relevant section** and note the line range
3. **Read specific lines**: `Read("docs-for-claude/claude-agent-sdk-knowledge.md", offset=START, limit=LENGTH)`

Example: To read about Python SDK (lines 137-200):
```
Read("docs-for-claude/claude-agent-sdk-knowledge.md", offset=137, limit=63)
```

### Quick Topic Lookup

| Topic | Lines |
|-------|-------|
| Getting Started | 567-621 |
| Understanding Agents | 7-37 |
| Python Usage | 137-200 |
| TypeScript Usage | 76-135 |
| Security/Permissions | 232-267 |
| MCP/External Tools | 350-405 |
| Subagents | 314-348 |
| Best Practices | 469-512 |
| All Official Links | 623-659 |

## Workflow

- Always commit and push after every change
- Run `python3 scripts/calculate_reading_time.py docs/` to verify word counts before updating metadata
- Use `wc -w` as a secondary verification

## GitHub Pages

- Served from `docs/` folder on `main` branch
- Static HTML (no Jekyll) - `.nojekyll` file must be present
- URL: https://bedwards.github.io/anthropic-claude-agent-sdk/

## Writing Style for Documentation

- Flowing prose optimized for Speechify reading
- Vary sentence and paragraph length for natural rhythm
- Avoid jargon; write out acronyms on first use
- Favor text over code snippets, bullet lists, and tables
- Explain concepts from first principles
- Include direct links to official documentation

## Local Development

```bash
cd docs && python3 -m http.server 8000
```

## Worker Agent

The `agents/worker-agent/` directory contains an autonomous worker agent that handles the complete PR lifecycle:

1. Creates git worktree for isolation
2. Implements feature using Claude Agent SDK
3. Runs local validation (lint, typecheck, tests)
4. Creates pull request
5. Watches for Claude GitHub integration review
6. Addresses blocking feedback, creates issues for non-blocking
7. Monitors CI and fixes failures
8. Merges when approved and green
9. Verifies main branch build after merge
10. Reports to manager if main fails

### Worker Agent Development

```bash
cd agents/worker-agent
uv sync                    # Install dependencies
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run mypy .              # Type check
```

### Worker Agent Usage

```bash
cd agents/worker-agent
worker run 42 --repo owner/repo    # Run worker for issue #42
worker status 42                    # Check status
worker list-workers                 # List all workers
```

Environment variables:
- `GITHUB_TOKEN`: Required for GitHub API access
- `GITHUB_REPOSITORY`: Default repository (owner/name)

Key behaviors:
- Does NOT modify lint/typecheck/test configuration unless absolutely necessary
- Commits frequently for visibility and recovery
- Creates follow-up issues for non-blocking review feedback
- Cleans up worktree on completion
