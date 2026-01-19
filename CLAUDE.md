# CLAUDE.md

## Project Overview

Documentation website for the Claude Agent SDK, hosted on GitHub Pages from the `docs/` folder.

## Repository Structure

```
├── docs/                 # GitHub Pages site (static HTML)
│   ├── index.html       # Landing page
│   ├── essay.html       # Main essay
│   ├── styles.css       # Stylesheet
│   └── .nojekyll        # Disables Jekyll processing
├── docs-for-claude/      # Knowledge base for Claude sessions
│   ├── INDEX.md         # Section index with line numbers (read first)
│   └── claude-agent-sdk-knowledge.md  # Full knowledge base (~660 lines)
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
