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
├── scripts/
│   └── calculate_reading_time.py  # Word count and reading time utility
├── raw-docs-source/     # Source material (not published)
└── README.md
```

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
