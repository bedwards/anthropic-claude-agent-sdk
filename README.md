# Claude Agent SDK Documentation

**[Read the Documentation →](https://bedwards.github.io/anthropic-claude-agent-sdk/)**

A comprehensive guide to building autonomous AI agents with Anthropic's Claude Agent SDK—the same engine that powers Claude Code, available as a library.

## What's Inside

### Essay: Understanding the Claude Agent SDK

A 5,000-word deep dive covering:

- What distinguishes agents from workflows
- Why Anthropic embraced bash as a core tool
- The three-part agent loop: gather context, take action, verify
- Tools vs bash vs code generation trade-offs
- TypeScript and Python SDK architecture
- Sessions, permissions, hooks, and subagents
- MCP integration and structured outputs
- Hosting and deployment patterns
- The design process for building agents

### Quick Reference

Direct links to all official documentation, guides, and resources.

## Local Development

To run the documentation site locally:

```bash
cd docs
python3 -m http.server 8000
# Open http://localhost:8000
```

## Apps

### Choose Your Own Adventure

**[Play Now →](https://dragon-adventure.pages.dev)**

An interactive story game built with TypeScript and Vite, demonstrating branching narrative logic.

- Multiple story paths with conditional choices
- 8 different endings
- Save/load progress
- Share your position via URL
- Responsive dark-themed UI

```bash
cd apps/choose-your-own-adventure
npm install
npm run dev      # Development server
npm test         # Run tests
npm run deploy   # Deploy to Cloudflare Pages
```

## Examples

```
$ python examples/list-files.py
This directory contains:

**Files:**
- `.gitignore` - Git ignore configuration
- `CLAUDE.md` - Documentation for Claude (likely instructions or context)
- `LICENSE` - License file (34KB)
- `README.md` - Main readme documentation

**Directories:**
- `.git/` - Git repository data
- `docs/` - Documentation directory
- `docs-for-claude/` - Documentation specifically for Claude
- `examples/` - Examples directory
- `raw-docs-source/` - Raw documentation source files
- `scripts/` - Scripts directory

This appears to be a documentation or project repository with various docs directories and examples.
```

## Scripts

Calculate word counts and reading times:

```bash
python3 scripts/calculate_reading_time.py docs/
```

## Source Material

This documentation synthesizes content from:

- [Official Claude Agent SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) (Anthropic Engineering)
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Anthropic Engineering)
- [The Complete Guide to Building Agents](https://nader.substack.com/p/the-complete-guide-to-building-agents) (Nader Dabit)
- Claude Agent SDK Workshop presentation transcript

## Official Resources

| Resource | Link |
|----------|------|
| Python SDK | [GitHub](https://github.com/anthropics/claude-agent-sdk-python) |
| TypeScript SDK | [npm](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk) |
| Example Agents | [GitHub](https://github.com/anthropics/claude-agent-sdk-demos) |
| Documentation | [platform.claude.com](https://platform.claude.com/docs/en/agent-sdk/overview) |

## License

Documentation content is provided for educational purposes. The Claude Agent SDK is a product of Anthropic.
