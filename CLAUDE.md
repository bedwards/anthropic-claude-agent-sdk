# CLAUDE.md

## Project Overview

Documentation website for the Claude Agent SDK, hosted on GitHub Pages from the `docs/` folder.

## Repository Structure

```
├── docs/                 # GitHub Pages site (static HTML)
│   ├── index.html       # Landing page
│   ├── essay.html       # Main essay (~5,000 words)
│   ├── worker-agent.html # Worker agent essay (~3,500 words)
│   ├── multi-model-animation.html # Multi-model animation essay
│   ├── styles.css       # Stylesheet
│   └── .nojekyll        # Disables Jekyll processing
├── docs-for-claude/      # Knowledge base for Claude sessions
│   ├── INDEX.md         # Section index with line numbers (read first)
│   └── claude-agent-sdk-knowledge.md  # Full knowledge base (~660 lines)
├── agents/
│   ├── shared/          # Shared library for worker agents
│   │   └── src/worker_shared/
│   │       ├── base_models.py     # Common Pydantic models
│   │       ├── base_status.py     # Generic status manager
│   │       ├── git_ops.py         # Git worktree operations
│   │       └── github_ops.py      # GitHub API operations
│   ├── worker-agent/    # PR lifecycle worker agent
│   │   └── src/worker_agent/
│   │       ├── models.py, status_manager.py, git_manager.py
│   │       ├── github_manager.py, agent.py, cli.py
│   │       └── tests/
│   └── animation-worker/ # Animation creation worker agent
│       └── src/animation_worker/
│           ├── models.py          # Animation-specific models
│           ├── status_manager.py  # Animation status management
│           ├── agent.py           # Animation workflow
│           └── cli.py             # Animation CLI
├── apps/
│   └── roblox-animation/ # Animation tools with Gemini integration
│       └── src/animation_tools/
│           ├── create_animation.py  # Blender animation creation
│           ├── render_frames.py     # Frame rendering
│           ├── analyze_animation.py # Gemini vision analysis
│           └── orchestrator.py      # Workflow orchestration
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

## Security Guidelines

**NEVER commit:**
- Secrets, API keys, tokens, passwords
- `.env` files (except `.env.example`)
- Credentials files (`credentials.json`, `*.pem`, `*.key`)
- Service account files

**NEVER put client-side:**
- API keys or secrets
- Database credentials
- Private configuration

**Generated files to exclude:**
- `__pycache__/`, `*.pyc`
- `node_modules/`
- `.venv/`, `venv/`
- `uv.lock` (regenerated on install)
- `.coverage`, `.pytest_cache/`
- Build artifacts (`dist/`, `build/`)

The root `.gitignore` covers these patterns. Always verify before committing.

## Development Process

**CRITICAL: Never write code directly. Always use our process:**

1. **Create GitHub Issues** - All implementation work starts as a GitHub issue with detailed requirements
2. **Worker Agent Implements** - The worker agent (`agents/worker-agent/`) handles the actual coding
3. **Manager Role** - Claude in conversation acts as manager: creates issues, reviews PRs, coordinates

**Why this process:**
- Isolation: Worker runs in separate worktree, can't break main
- Visibility: All work tracked in GitHub issues and PRs
- Recovery: If worker fails, work is preserved in branch
- Review: Claude GitHub integration reviews all PRs

**Manager responsibilities:**
- Analyze requirements and create well-specified issues
- Monitor worker progress
- Review PR feedback and guide worker responses
- Create follow-up issues for additional work
- NEVER write implementation code directly

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

### Worker Agent Test Status

**Tested and working:**
- Git worktree creation for isolation
- Reading GitHub issue details
- Claude Agent SDK implementation phase
- Writing tests (generated 378 lines of tests)
- Running validation (lint, typecheck, tests)
- Committing and pushing to branch
- PR creation

**Not yet tested:**
- Review feedback loop (responding to Claude GitHub integration)
- CI failure fixing
- Merge conflict resolution
- PR merge
- Main branch verification post-merge
- Manager notifications

**Known issues to fix:**
- Should check if PR exists before creating (handle 422)
- Need better error recovery on failures
- Cleanup on crash/interrupt incomplete

## Animation Worker Agent

The `agents/animation-worker/` directory contains an autonomous worker agent for creating Roblox animations using Claude Agent SDK with Gemini vision analysis.

### Key Principle

**Gemini's verdict is authoritative.** Claude orchestrates the workflow and generates animation code, but Gemini determines when the animation meets quality standards. Claude should not second-guess Gemini's "done" or "needs_work" verdicts.

### Animation Workflow

1. Read animation requirements from GitHub issue
2. Use Claude to generate Blender Python animation code
3. Run Blender headlessly to create .blend file
4. Render animation frames to PNG
5. Analyze frames with Gemini vision (provides verdict)
6. If "needs_work", iterate with Gemini's feedback
7. Export final animation to Roblox format using anim2rbx

### Animation Worker Usage

```bash
cd agents/animation-worker
uv sync
animation-worker run 68 --repo owner/repo    # Run for issue #68
animation-worker status 68                    # Check status
animation-worker list-workers                 # List all workers
```

Environment variables:
- `GITHUB_TOKEN`: Required for GitHub API access
- `GEMINI_API_KEY`: Required for Gemini vision analysis
- `DYLD_LIBRARY_PATH`: Set to `/usr/local/opt/assimp@5/lib` for anim2rbx

### Animation Tools

The `apps/roblox-animation/src/animation_tools/` provides:
- `create_animation`: Generate Blender animation from Python code
- `render_frames`: Render animation to PNG frames
- `analyze_animation`: Gemini vision analysis with done/needs_work verdict

## Multi-Model Agent Architecture

This project demonstrates multi-model agents where Claude and Gemini collaborate:
- **Claude**: Orchestrates workflow, generates code, makes decisions
- **Gemini**: Provides authoritative vision analysis verdicts

This pattern keeps Claude as the "brain" while leveraging Gemini's visual capabilities for tasks like animation quality assessment.

## Claude Agent SDK Lessons Learned (War Stories)

Real-world lessons from building with the Claude Agent SDK:

### Process Discipline

1. **Manager vs Worker Separation** - The conversational Claude should NEVER write implementation code. Create issues, let worker agents implement. This prevents scope creep and ensures all work is tracked.

2. **Don't Remove Functionality** - When adding features, expand existing code rather than replacing it. Easy to accidentally break things during "simplification."

3. **Maintain Broad Perspective** - Easy to get tunnel vision on one feature. Keep the whole system in mind.

### Technical Lessons

1. **Git Worktrees for Isolation** - Workers operate in worktrees so failures don't affect main branch. Essential for autonomous operation.

2. **Frequent Commits** - Worker should commit after each significant change. Enables recovery and visibility.

3. **Local Validation First** - Run lint/typecheck/tests locally before pushing. Faster feedback than CI.

4. **Handle API Rate Limits** - GitHub API has rate limits. Worker needs backoff logic.

### Claude Agent SDK Specifics

1. **Tool Results Are Rich** - Tool results can include system reminders and context. Parse carefully.

2. **Context Windows Fill Up** - Long conversations get compacted. Maintain external state (todo lists, issue descriptions) rather than relying on conversation memory.

3. **Parallel Tool Calls** - Use parallel tool calls when operations are independent. Significant speedup.

4. **Subagent Spawning** - Task tool spawns subagents for complex work. Each subagent is fresh context.

### What Works Well

- GitHub Issues as source of truth for requirements
- Worker agent handling full PR lifecycle
- Claude GitHub integration for automated review
- Structured logging for debugging autonomous workers

### What's Tricky

- Error recovery when worker hits unexpected states
- Balancing autonomy with user oversight
- Managing context across long conversations
- Testing async/autonomous behaviors
