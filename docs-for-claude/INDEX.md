# Claude Agent SDK Knowledge Base Index

Use this index to find specific sections in `claude-agent-sdk-knowledge.md`.
Read this file first, then use `Read` with `offset` and `limit` parameters to fetch specific sections.

## How to Use

1. Find the section you need below
2. Note the line range (start-end)
3. Read that section: `Read("docs-for-claude/claude-agent-sdk-knowledge.md", offset=START, limit=LENGTH)`

---

## Section Index

| Section | Lines | Description |
|---------|-------|-------------|
| **CORE CONCEPTS** | 7-37 | Foundational understanding |
| ├─ What Is an Agent | 9-15 | Agent vs workflow distinction |
| ├─ The Three-Part Agent Loop | 17-27 | Gather, act, verify pattern |
| └─ Agent SDK vs Client SDK | 29-37 | When to use which SDK |
| **WHY BASH IS CENTRAL** | 39-74 | Bash philosophy and trade-offs |
| ├─ The Bash Philosophy | 41-51 | Why bash is most powerful tool |
| ├─ Code Generation for Non-Coding Tasks | 53-57 | Using code for any task |
| └─ Tools vs Bash vs Code Generation | 59-74 | When to use each approach |
| **TYPESCRIPT SDK** | 76-135 | TypeScript implementation |
| ├─ Core Function: query() | 78-93 | Main query function |
| ├─ Configuration Options | 95-104 | ClaudeAgentOptions properties |
| ├─ Message Types | 106-113 | Message types in generator |
| ├─ Query Object Methods | 115-120 | interrupt, rewindFiles, etc. |
| └─ TypeScript V2 Preview | 122-135 | Multi-turn conversation API |
| **PYTHON SDK** | 137-200 | Python implementation |
| ├─ Two Interfaces | 139-166 | query() vs ClaudeSDKClient |
| ├─ ClaudeSDKClient Methods | 168-178 | connect, query, interrupt, etc. |
| └─ Configuration | 180-200 | ClaudeAgentOptions dataclass |
| **SESSIONS AND CONTINUITY** | 202-230 | Session management |
| ├─ Session Management | 204-211 | Creating and resuming sessions |
| ├─ Forking | 213-220 | Branching conversations |
| └─ File Checkpointing | 222-230 | Tracking and rewinding file changes |
| **PERMISSIONS SYSTEM** | 232-267 | Security and permissions |
| ├─ Permission Modes | 234-239 | default, acceptEdits, bypass, plan |
| ├─ Evaluation Order | 241-247 | How permissions are checked |
| ├─ canUseTool Callback | 249-255 | Custom permission logic |
| └─ Swiss Cheese Defense | 257-267 | Multi-layer security model |
| **HOOKS** | 269-312 | Intercepting agent behavior |
| ├─ Hook Events | 271-281 | PreToolUse, PostToolUse, etc. |
| └─ Hook Structure | 283-312 | Implementing hooks with examples |
| **SUBAGENTS** | 314-348 | Spawning specialized agents |
| ├─ What Are Subagents | 316-318 | Definition and purpose |
| ├─ Defining Subagents | 320-338 | AgentDefinition configuration |
| └─ Benefits | 340-348 | Context isolation, parallelization |
| **MODEL CONTEXT PROTOCOL (MCP)** | 350-405 | External tool integration |
| ├─ What Is MCP | 352-354 | Open standard for tools |
| ├─ Server Types | 356-360 | stdio, HTTP, SSE, in-process |
| ├─ Configuration | 362-376 | Setting up MCP servers |
| ├─ Tool Search | 378-380 | Automatic discovery |
| └─ Custom Tools (In-Process) | 382-405 | Creating custom MCP tools |
| **STRUCTURED OUTPUTS** | 407-438 | JSON Schema validation |
| ├─ Purpose | 409-411 | Why use structured outputs |
| ├─ Usage | 413-432 | Configuration with JSON Schema |
| └─ Type Safety | 434-438 | Zod and Pydantic integration |
| **HOSTING AND DEPLOYMENT** | 440-467 | Production deployment |
| ├─ Requirements | 442-447 | System requirements |
| ├─ Deployment Patterns | 449-457 | Ephemeral, long-running, hybrid |
| └─ Sandboxing | 459-467 | Container-based isolation |
| **DESIGN PROCESS** | 469-512 | Building effective agents |
| ├─ Three Questions Per Capability | 471-475 | Search, action, verification |
| ├─ Example: Spreadsheet Agent | 477-497 | Detailed design walkthrough |
| ├─ Context Engineering | 499-506 | Beyond prompts |
| └─ Read Transcripts Repeatedly | 508-512 | Learning from agent behavior |
| **BUILT-IN TOOLS REFERENCE** | 514-545 | Tool quick reference |
| ├─ File Operations | 516-523 | Read, Write, Edit, Glob, Grep |
| ├─ Execution | 525-528 | Bash, Task |
| ├─ Web | 530-533 | WebFetch, WebSearch |
| ├─ User Interaction | 535-538 | AskUserQuestion, TodoWrite |
| └─ MCP | 540-545 | ListMcpResources, ReadMcpResource |
| **MIGRATION NOTES** | 547-565 | Upgrading from older versions |
| ├─ Naming Change | 549-551 | Claude Code SDK → Agent SDK |
| └─ Breaking Changes | 553-565 | System prompt, settings sources |
| **QUICK REFERENCE** | 567-621 | Code examples |
| ├─ Minimal Python Example | 569-584 | Basic Python usage |
| ├─ Minimal TypeScript Example | 586-601 | Basic TypeScript usage |
| └─ Error Handling | 603-621 | Exception handling patterns |
| **OFFICIAL LINKS** | 623-659 | All official URLs |
| ├─ Documentation | 625-631 | SDK docs links |
| ├─ Guides | 633-649 | Feature guide links |
| ├─ Repositories | 651-654 | GitHub and npm links |
| └─ Blog Posts | 656-659 | Anthropic engineering blog |

---

## Quick Lookup by Topic

**Getting Started**: Lines 567-621 (Quick Reference)
**Understanding Agents**: Lines 7-37 (Core Concepts)
**Python Usage**: Lines 137-200 (Python SDK)
**TypeScript Usage**: Lines 76-135 (TypeScript SDK)
**Security**: Lines 232-267 (Permissions System)
**External Tools**: Lines 350-405 (MCP)
**Parallel Work**: Lines 314-348 (Subagents)
**Best Practices**: Lines 469-512 (Design Process)
**All Links**: Lines 623-659 (Official Links)
