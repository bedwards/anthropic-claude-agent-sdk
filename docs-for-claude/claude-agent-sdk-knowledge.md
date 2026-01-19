# Claude Agent SDK Complete Knowledge Base

This document contains comprehensive knowledge about the Claude Agent SDK, structured for efficient retrieval by Claude in future sessions.

---

## CORE CONCEPTS

### What Is an Agent

An agent is fundamentally different from a workflow. Workflows follow predetermined structures—you define steps in advance and the system follows them every time. Agents build their own structure. You give an agent a goal and tools, and it decides its own trajectory.

Claude Code is the canonical example: you speak in natural language, it reads files, runs commands, edits code, verifies changes compile, and might work autonomously for ten to thirty minutes. The Agent SDK packages this capability as a library.

The opposite of an agent is a workflow. If you know exactly what steps need to happen in what order, use a workflow. If steps depend on what you find along the way, or different inputs require fundamentally different approaches, use an agent.

### The Three-Part Agent Loop

Every well-designed agent follows: gather context, take action, verify the work.

**Gather Context**: Find information needed for the task. For code, search and read files. For email, locate messages. For databases, understand schema. Quality of context gathering directly determines agent performance. Like approaching an unfamiliar codebase—explore first, build mental model, then act.

**Take Action**: Use appropriate tools. Code generation, bash, or specialized tools. Depends entirely on gathered context.

**Verify**: Close the loop. If you can programmatically verify work, you have an excellent automation candidate. Code can be linted and executed. Tests can run. Research can cite sources. Spreadsheets can validate formulas.

Heuristic: Ask "how can I verify this work?" If verification is possible and precise, good agent candidate. If subjective or impossible, need human review.

### Agent SDK vs Client SDK

**Anthropic Client SDK**: Direct API access. You send prompts, implement tool execution yourself. When model returns tool use request, you execute, gather result, send another request. You manage the loop, handle errors, track context, decide when to summarize.

**Agent SDK**: Inverts the relationship. You provide prompt and configuration. SDK handles tool loop internally—retries, error handling, context management, compaction. Claude autonomously reads files, finds bugs, fixes them without manual intervention each step.

The Agent SDK handles dozens of edge cases learned from deploying Claude Code to millions of users.

---

## WHY BASH IS CENTRAL

### The Bash Philosophy

Anthropic discovered something counterintuitive: the bash tool represents perhaps the most powerful capability you can give an agent, obviating most specialized tools.

What bash enables:
- Store results to files
- Dynamically generate and call scripts
- Compose functionality through pipes
- Use any system software: FFmpeg, LibreOffice, curl, jq
- Claude doesn't need custom grep—it uses grep directly
- Doesn't need package manager integration—runs npm or pip

### Code Generation for Non-Coding Tasks

Counterintuitive principle: use code generation for non-coding tasks. Ask Claude for weather in San Francisco, it might write a script to fetch weather API, determine location from IP, provide recommendations.

Email agent example: Without bash, user asks "how much spent on ridesharing this week"—agent searches Uber/Lyft emails, retrieves hundred results, must reason through all text at once. With bash: save query results to files, grep for prices, add together, check work by storing intermediate results with line numbers. Agent verifies its own calculations.

### Tools vs Bash vs Code Generation

**Traditional Tools**: Extremely structured and reliable. Fastest output, minimal errors/retries. Write tool writes file. Read tool reads file. Atomic and predictable. But: consume significant context, model gets confused with 50-100 tools, lack composability.

**Bash**: Composability through scripts, relatively low context. Agent may need discovery time (running help commands). Progressive disclosure trades latency for reduced context. Doesn't need all capabilities upfront—discovers as needed.

**Code Generation**: Highest composability with dynamic scripts. Longest execution (interpretation/compilation). API design crucial—agent composes APIs in unexpected ways.

When to use each:
- Tools: Atomic actions requiring strong guarantees (file writes needing approval, emails that can't be unsent)
- Bash: Composable actions (searching folders, git commands, memory through file system)
- Code generation: Highly dynamic logic, composing multiple APIs, data analysis, deep research

Most real agents use all three in combination.

---

## TYPESCRIPT SDK

### Core Function: query()

Returns object extending AsyncGenerator with additional control methods. Call with prompt and options, iterate through messages as they stream.

```typescript
import { query, ClaudeAgentOptions } from '@anthropic-ai/claude-agent-sdk';

const conversation = query({
  prompt: "Your task",
  options: { /* configuration */ }
});

for await (const message of conversation) {
  // Handle messages
}
```

### Configuration Options

Key properties of ClaudeAgentOptions:
- `allowedTools`: Array of tool names (Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, etc.)
- `systemPrompt`: Instructions or preset configuration
- `mcpServers`: External tools via Model Context Protocol
- `permissionMode`: Control what requires approval (default, acceptEdits, bypassPermissions, plan)
- `cwd`: Working directory
- `maxTurns`: Limit conversation turns
- `outputFormat`: JSON Schema for structured outputs

### Message Types

Messages flow through generator:
- `AssistantMessage`: Claude's reasoning with content blocks
- `UserMessage`: Inputs and tool results
- Partial streaming messages for real-time display
- Compact boundaries when history summarized
- `ResultMessage`: Final result with cost/usage info

### Query Object Methods

Beyond iteration:
- `interrupt()`: Stop Claude mid-execution during streaming
- `rewindFiles(uuid)`: Restore files to previous state (requires checkpointing)
- `setPermissionMode()`: Change permissions during execution

### TypeScript V2 Preview

Simplifies multi-turn conversations. Instead of managing generator state, each turn is separate send/stream cycle:

```typescript
const session = createSession(options);
await session.send("First message");
for await (const msg of session.stream()) { /* ... */ }

await session.send("Follow-up");  // Claude remembers context
for await (const msg of session.stream()) { /* ... */ }
```

---

## PYTHON SDK

### Two Interfaces

**query() function**: New session each interaction. Suits one-off questions, independent tasks, simple automation. Each call starts fresh, no memory.

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Your task",
    options=ClaudeAgentOptions(allowed_tools=["Bash", "Read"])
):
    print(message)
```

**ClaudeSDKClient**: Maintains conversation across exchanges. Session continuity, supports interrupts, enables hooks and custom tools, response-driven logic.

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient(options) as client:
    await client.query("First question")
    async for msg in client.receive_response():
        print(msg)

    await client.query("Follow-up")  # Remembers context
    async for msg in client.receive_response():
        print(msg)
```

### ClaudeSDKClient Methods

- `connect(prompt)`: Connect with optional initial prompt
- `query(prompt, session_id)`: Send new request in streaming mode
- `receive_messages()`: All messages as async iterator
- `receive_response()`: Messages until ResultMessage
- `interrupt()`: Stop mid-execution (streaming mode only)
- `rewind_files(uuid)`: Restore files to checkpoint
- `disconnect()`: End connection

Note: Avoid using `break` to exit iteration early—causes asyncio cleanup issues. Use flags instead.

### Configuration (ClaudeAgentOptions dataclass)

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    cwd: str | Path | None = None
    output_format: OutputFormat | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    agents: dict[str, AgentDefinition] | None = None
    # ... and more
```

---

## SESSIONS AND CONTINUITY

### Session Management

SDK creates sessions automatically, returns session ID in initial system message. Capture ID to resume later. Resuming loads conversation history and context—Claude continues exactly where it left off.

Patterns enabled:
- Long-running workflows persist across restarts
- Users return to previous conversations
- Agents interrupted and resumed without losing progress

### Forking

Creates new session branch from existing point. Useful for:
- Exploring different approaches from same starting point
- Testing changes without affecting original history
- Maintaining separate conversation paths for experiments

Like git branching—try something, see results, go back to branch point if needed.

### File Checkpointing

Tracks modifications via Write, Edit, NotebookEdit tools during session. Rewind files to any previous state.

Enable in options, capture checkpoint UUIDs from user messages, call `rewindFiles(uuid)`. Restores files on disk: created files deleted, modified files restore to previous content.

Note: Changes via bash not tracked—only built-in file tools participate. For full reversibility, prefer built-in tools.

---

## PERMISSIONS SYSTEM

### Permission Modes

- `default`: Requires canUseTool callback for unmatched tools
- `acceptEdits`: Auto-approves file operations, prompts for others
- `bypassPermissions`: Runs everything without prompts (use only in controlled environments like CI)
- `plan`: Prevents tool execution, Claude analyzes and plans only

### Evaluation Order

When Claude requests tool:
1. Hooks run first (can allow, deny, or continue)
2. Permission rules check deny rules, then allow rules, then ask rules
3. Active permission mode applies defaults
4. If nothing resolved, canUseTool callback handles it

### canUseTool Callback

Receives tool name, input parameters, context. Return:
- Allow result with potentially modified input
- Deny result with message explaining why

Must return within 60 seconds or Claude assumes denial.

### Swiss Cheese Defense

Multiple security layers, each with holes arranged so no single path goes straight through:
1. Model alignment training (Claude unlikely to attempt harmful actions)
2. Harness permissioning and prompting
3. Bash parser determines what commands actually do
4. Sandboxing limits actual capabilities

Network sandboxing prevents exfiltration. File system sandboxing prevents access outside working directory. Container sandboxing isolates from host.

---

## HOOKS

### Hook Events

- `PreToolUse`: Before tool execution (can block)
- `PostToolUse`: After execution (logging/auditing)
- `UserPromptSubmit`: Can inject context or modify prompts
- `SessionStart`, `SessionEnd`: Session lifecycle
- `Stop`: Save session state before exit
- `SubagentStop`: When subagent stops
- `PreCompact`: Archive full transcripts before summarization

Note: Python SDK doesn't support SessionStart, SessionEnd, Notification hooks due to setup limitations.

### Hook Structure

Two parts: callback function with logic, configuration telling SDK which event and which tools to match.

```python
async def validate_bash(input_data, tool_use_id, context):
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        if 'rm -rf /' in command:
            return {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Dangerous command blocked'
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(matcher='Bash', hooks=[validate_bash])
        ]
    }
)
```

Hooks chain in array order. If any returns deny, operation blocks.

---

## SUBAGENTS

### What Are Subagents

Separate agent instances spawned by main agent for focused subtasks. Isolate context, run in parallel, apply specialized instructions without bloating main prompt.

### Defining Subagents

```python
options = ClaudeAgentOptions(
    agents={
        "researcher": AgentDefinition(
            description="Research and analyze codebases",
            prompt="You are a code research specialist...",
            tools=["Read", "Glob", "Grep"],
            model="haiku"
        ),
        "security": AgentDefinition(
            description="Security vulnerability analysis",
            prompt="You are a security expert...",
            tools=["Read", "Grep", "Bash"]
        )
    }
)
```

### Benefits

**Context Isolation**: Specialized tasks don't pollute main conversation. Research subagent explores dozens of files, returns only relevant findings. Main agent receives summary.

**Parallelization**: Multiple subagents run concurrently. Code review: style checker, security scanner, test coverage analyzer run simultaneously. Main agent synthesizes results.

**Limitation**: Subagents cannot spawn their own subagents (prevents infinite recursion).

---

## MODEL CONTEXT PROTOCOL (MCP)

### What Is MCP

Open standard connecting agents to external tools and data sources. Query databases, integrate Slack/GitHub, browser automation, hundreds of services without custom tool implementations.

### Server Types

- Stdio processes (local)
- HTTP or Server-Sent Events (remote)
- In-process SDK servers (custom tools)

### Configuration

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"]
        }
    },
    allowed_tools=["mcp__github__*"]  # Wildcard for all tools from server
)
```

Tool naming: `mcp__servername__toolname`

### Tool Search

Activates when MCP tool descriptions exceed 10% of context window. Instead of preloading all tools, Claude uses search tool to discover relevant MCP tools on demand.

### Custom Tools (In-Process)

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("calculate", "Perform calculations", {"expression": str})
async def calculate(args):
    result = eval(args["expression"], {"__builtins__": {}})
    return {"content": [{"type": "text", "text": f"Result: {result}"}]}

server = create_sdk_mcp_server(
    name="calculator",
    tools=[calculate]
)

options = ClaudeAgentOptions(
    mcp_servers={"calc": server},
    allowed_tools=["mcp__calc__calculate"]
)
```

Better performance than external servers (no IPC overhead).

---

## STRUCTURED OUTPUTS

### Purpose

Agents return free-form text by default. Structured outputs define exact data shape using JSON Schema for programmatic use.

### Usage

```python
options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "issues": {"type": "array", "items": {"type": "string"}},
                "score": {"type": "number"}
            },
            "required": ["summary", "issues", "score"]
        }
    }
)
```

Agent uses any tools needed, still returns validated JSON. Check result message subtype: `success` means valid output, `error_max_structured_output_retries` means couldn't produce valid output.

### Type Safety

Use Zod (TypeScript) or Pydantic (Python) for schema definition and strongly-typed objects.

---

## HOSTING AND DEPLOYMENT

### Requirements

- Python 3.10+ or Node.js 18+
- Claude Code CLI installed
- ~1GB RAM, ~5GB disk
- Outbound HTTPS to api.anthropic.com

### Deployment Patterns

**Ephemeral Sessions**: New container per user task, destroyed on completion. Suits one-off tasks (bug investigation, invoice processing, document translation). Clean environment, no state leakage.

**Long-Running Sessions**: Persistent container instances. Suits proactive agents, site builders, chatbots. Container persists, maintains file system state and conversation context.

**Hybrid Sessions**: Ephemeral containers hydrated with history/state from databases or session resumption. Suits intermittent patterns (project management, deep research, customer support). Isolation benefits with continuity.

**Multi-Agent Containers**: Single container with multiple SDK processes. Rare—must prevent agents overwriting each other's work. Use when collaboration benefits outweigh complexity.

### Sandboxing

Container-based sandboxing for:
- Process isolation
- Resource limits
- Network control
- Ephemeral filesystems

---

## DESIGN PROCESS

### Three Questions Per Capability

1. What is the best way to search/gather context?
2. What is the best way to take action?
3. What is the best way to verify the work?

### Example: Spreadsheet Agent

**Searching options**:
- Convert to CSV and grep
- AWK for tabular queries
- Translate to SQLite for SQL queries
- Range syntax like B3:B5 (model knows well)
- Search XML (XLSX files are XML internally)

**Taking action**:
- Insert 2D arrays
- Execute SQL queries
- Edit XML directly

Gathering context and taking action APIs often share structure.

**Verification**:
- Check for null pointers
- Validate formulas
- Ensure row counts match expectations
- Insert deterministic rules wherever possible

### Context Engineering Beyond Prompts

- File system becomes memory
- Scripts become reusable tools
- Files become searchable context
- Skills are folders agent can navigate with instructions and examples

Long outputs should go to files (agent can grep across results, check work, maintain references). Memory can live in a memories folder where agent writes insights for future reference.

### Read Transcripts Repeatedly

Every time you see agent running, examine what it does and why. Figure out how to help it. This intuition-building reveals what your specific domain requires. Agent will do unanticipated things. Watch, learn, adjust.

---

## BUILT-IN TOOLS REFERENCE

### File Operations

- **Read**: Read file contents with optional offset/limit
- **Write**: Write/overwrite file
- **Edit**: String replacement in files
- **Glob**: Pattern matching for files
- **Grep**: Regex search with ripgrep
- **NotebookEdit**: Edit Jupyter notebook cells

### Execution

- **Bash**: Execute shell commands (most powerful tool)
- **Task**: Spawn subagents

### Web

- **WebFetch**: Fetch URL content with AI processing
- **WebSearch**: Search the web

### User Interaction

- **AskUserQuestion**: Ask clarifying questions
- **TodoWrite**: Manage task lists

### MCP

- **ListMcpResources**: List available MCP resources
- **ReadMcpResource**: Read MCP resource content

---

## MIGRATION NOTES

### Naming Change

SDK renamed from "Claude Code SDK" to "Claude Agent SDK" reflecting broader capabilities. Package names changed accordingly.

### Breaking Changes (from older versions)

1. **System prompt**: No longer defaults to Claude Code's prompt. Must explicitly request if needed:
```python
system_prompt={"type": "preset", "preset": "claude_code"}
```

2. **Settings sources**: No longer load automatically. Ensures predictable behavior independent of local filesystem. For CLAUDE.md files, must include "project" in setting_sources:
```python
setting_sources=["project"]
```

---

## QUICK REFERENCE

### Minimal Python Example

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="What files are here?",
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"])
    ):
        if hasattr(message, 'result'):
            print(message.result)

asyncio.run(main())
```

### Minimal TypeScript Example

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const conversation = query({
  prompt: "What files are here?",
  options: { allowedTools: ["Bash", "Glob"] }
});

for await (const message of conversation) {
  if (message.type === 'result') {
    console.log(message.result);
  }
}
```

### Error Handling

```python
from claude_agent_sdk import (
    query, CLINotFoundError, ProcessError, CLIJSONDecodeError
)

try:
    async for message in query(prompt="Hello"):
        print(message)
except CLINotFoundError:
    print("Install Claude Code: npm install -g @anthropic-ai/claude-code")
except ProcessError as e:
    print(f"Process failed: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Parse error: {e}")
```

---

## OFFICIAL LINKS

### Documentation
- Overview: https://platform.claude.com/docs/en/agent-sdk/overview
- Quickstart: https://platform.claude.com/docs/en/agent-sdk/quickstart
- TypeScript SDK: https://platform.claude.com/docs/en/agent-sdk/typescript
- TypeScript V2: https://platform.claude.com/docs/en/agent-sdk/typescript-v2-preview
- Python SDK: https://platform.claude.com/docs/en/agent-sdk/python
- Migration Guide: https://platform.claude.com/docs/en/agent-sdk/migration-guide

### Guides
- Streaming vs Single: https://platform.claude.com/docs/en/agent-sdk/streaming-vs-single-mode
- Permissions: https://platform.claude.com/docs/en/agent-sdk/permissions
- User Input: https://platform.claude.com/docs/en/agent-sdk/user-input
- Hooks: https://platform.claude.com/docs/en/agent-sdk/hooks
- Sessions: https://platform.claude.com/docs/en/agent-sdk/sessions
- File Checkpointing: https://platform.claude.com/docs/en/agent-sdk/file-checkpointing
- Structured Outputs: https://platform.claude.com/docs/en/agent-sdk/structured-outputs
- Hosting: https://platform.claude.com/docs/en/agent-sdk/hosting
- Secure Deployment: https://platform.claude.com/docs/en/agent-sdk/secure-deployment
- System Prompts: https://platform.claude.com/docs/en/agent-sdk/modifying-system-prompts
- MCP: https://platform.claude.com/docs/en/agent-sdk/mcp
- Custom Tools: https://platform.claude.com/docs/en/agent-sdk/custom-tools
- Subagents: https://platform.claude.com/docs/en/agent-sdk/subagents
- Slash Commands: https://platform.claude.com/docs/en/agent-sdk/slash-commands
- Skills: https://platform.claude.com/docs/en/agent-sdk/skills
- Cost Tracking: https://platform.claude.com/docs/en/agent-sdk/cost-tracking

### Repositories
- Python SDK: https://github.com/anthropics/claude-agent-sdk-python
- TypeScript SDK: https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk
- Examples: https://github.com/anthropics/claude-agent-sdk-demos

### Blog Posts
- Building Agents: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- Effective Harnesses: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

---

## WORKER AGENT IMPLEMENTATION

### The Gap in One-Shot Workers
One-shot workers implement features but leave a gap: everything after the PR is created. Code review feedback arrives, CI checks run, merge conflicts appear. In the one-shot pattern, the manager must monitor every PR, read every review, spawn new workers for feedback, and orchestrate merges. The manager becomes a bottleneck.

The worker agent closes this gap by owning the entire PR lifecycle: implementation through verified merge.

### Worker Agent Lifecycle
1. Initialize: Create git worktree for isolation
2. Implement: Use Claude Agent SDK to implement the feature
3. Validate: Run lint, typecheck, tests locally (before creating PR)
4. Create PR: Push and open pull request
5. Review Loop: Wait for Claude GitHub integration review, address blocking feedback, create issues for non-blocking
6. CI Loop: Wait for CI, fix failures
7. Merge: Squash merge when approved and green
8. Verify Main: Watch main branch build after merge, report failures to manager

### Git Worktrees for Parallel Isolation
Each worker agent creates its own worktree (e.g., `.worktrees/issue-42`). Worktrees share git history but have separate working files. This enables true parallelism: ten workers can run simultaneously without conflicts. Each worktree needs its own dependency installation.

### Worker Agent Architecture
- **StatusManager**: Logging and status persistence to JSON files
- **GitManager**: Git worktree, commits, pushes, conflict checking, rebasing
- **GitHubManager**: Issue reading, PR creation, review polling, CI status, merging, main branch monitoring
- **WorkerAgent**: State machine orchestrating all phases
- **CLI**: Command-line interface (`worker run 42 --repo owner/repo`)

### Main Branch Verification
After merging, the agent watches the main branch build. If main fails, the agent reports to the manager with a MAIN_BRANCH_FAILED notification. The manager can then create a fix issue and spawn another worker. The system becomes self-healing.

### What Worker Agent Does NOT Do
- Make architectural decisions (issue must be detailed enough)
- Modify build configuration without permission
- Force push or rewrite public history
- Handle complex merge conflicts (flags for human resolution)
- Decide what to work on (manager decides priorities)

### Worker Agent Development
```bash
cd agents/worker-agent
uv sync                    # Install dependencies
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run mypy .              # Type check
```

### Worker Agent Files
- `agents/worker-agent/pyproject.toml` - Project configuration
- `agents/worker-agent/src/worker_agent/models.py` - Pydantic models
- `agents/worker-agent/src/worker_agent/status_manager.py` - Logging/status
- `agents/worker-agent/src/worker_agent/git_manager.py` - Git operations
- `agents/worker-agent/src/worker_agent/github_manager.py` - GitHub API
- `agents/worker-agent/src/worker_agent/agent.py` - Main orchestration
- `agents/worker-agent/src/worker_agent/cli.py` - CLI
