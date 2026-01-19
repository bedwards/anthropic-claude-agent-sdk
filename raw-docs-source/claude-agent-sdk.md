The Claude Agent SDK: A Complete Guide to Building Autonomous AI Agents
The Core Insight: Why This Matters Right Now
Building AI agents just changed. The Claude Agent SDK gives you the same tools, agentic loop, and context management that power Claude Code, fully programmable in Python and TypeScript. Instead of implementing your own tool execution and orchestration, you get built-in capabilities for reading files, running commands, and editing code out of the box.
This is not just another framework. As Tariq from Anthropic explained in a recent technical presentation, the team kept rebuilding the same components internally until they realized: everyone needs a harness containing tools, prompts, a file system, skills, subagents, web search, compacting, hooks, and memory. The Agent SDK packages all of these lessons learned from deploying Claude Code at scale.
Direct links to all documentation:

Overview: https://platform.claude.com/docs/en/agent-sdk/overview
Quickstart: https://platform.claude.com/docs/en/agent-sdk/quickstart
TypeScript SDK: https://platform.claude.com/docs/en/agent-sdk/typescript
TypeScript V2 Preview: https://platform.claude.com/docs/en/agent-sdk/typescript-v2-preview
Python SDK: https://platform.claude.com/docs/en/agent-sdk/python
Migration Guide: https://platform.claude.com/docs/en/agent-sdk/migration-guide

Guides:

Streaming Input: https://platform.claude.com/docs/en/agent-sdk/streaming-vs-single-mode
Configure Permissions: https://platform.claude.com/docs/en/agent-sdk/permissions
Handle Approvals and User Input: https://platform.claude.com/docs/en/agent-sdk/user-input
Hooks: https://platform.claude.com/docs/en/agent-sdk/hooks
Sessions: https://platform.claude.com/docs/en/agent-sdk/sessions
File Checkpointing: https://platform.claude.com/docs/en/agent-sdk/file-checkpointing
Structured Outputs: https://platform.claude.com/docs/en/agent-sdk/structured-outputs
Hosting: https://platform.claude.com/docs/en/agent-sdk/hosting
Secure Deployment: https://platform.claude.com/docs/en/agent-sdk/secure-deployment
Modifying System Prompts: https://platform.claude.com/docs/en/agent-sdk/modifying-system-prompts
MCP Integration: https://platform.claude.com/docs/en/agent-sdk/mcp
Custom Tools: https://platform.claude.com/docs/en/agent-sdk/custom-tools
Subagents: https://platform.claude.com/docs/en/agent-sdk/subagents
Slash Commands: https://platform.claude.com/docs/en/agent-sdk/slash-commands
Skills: https://platform.claude.com/docs/en/agent-sdk/skills
Cost Tracking: https://platform.claude.com/docs/en/agent-sdk/cost-tracking


What Is an Agent, Really?
Before diving into the SDK, let's establish what we mean by an agent. This matters because the terminology often creates confusion.
When GPT-3 emerged, most applications involved single Large Language Model (LLM) features. You would send a prompt like "categorize this email" and receive a structured response. Then came workflows, where you chain together structured steps: index code via Retrieval Augmented Generation (RAG), retrieve context, generate a completion. These workflows are predictable and deterministic.
Agents represent something fundamentally different. Claude Code became the canonical example. You speak to it in natural language, and it decides its own trajectory. It builds its own context, chooses which tools to use, works for ten, twenty, or thirty minutes autonomously. You are not telling it step by step what to do. You are giving it a goal and the tools to achieve that goal.
The opposite of an agent is a workflow. A workflow follows your predetermined structure. An agent builds its own structure. The Agent SDK supports both, but the power lies in letting the model decide how to accomplish your objectives.

The Anthropic Philosophy: Bash Is All You Need
Here is where the SDK diverges sharply from other frameworks. Anthropic discovered that the bash tool represents perhaps the most powerful capability you can give an agent.
Consider what bash enables: storing results to files, dynamically generating scripts, composing functionality through pipes, using existing software like FFmpeg or LibreOffice. When Anthropic was designing Claude Code, they could have created separate tools for searching, linting, and executing. Instead, Claude uses grep and runs npm commands directly. It can discover your linting configuration and suggest installing ESLint if you lack one.
This insight led to a counterintuitive design principle: use code generation for non-coding tasks. When you ask Claude Code to find the weather in San Francisco and suggest what to wear, it might write a script to fetch a weather API, determine your location from your IP address, and call out to recommendations. For any task involving composing APIs or doing data analysis, code generation provides remarkable flexibility.
Take an email agent example. Without bash, when a user asks "how much did I spend on ride sharing this week," the agent searches for Uber or Lyft, retrieves a hundred emails, and must somehow reason through all that text. With bash, the agent can save query results to files, grep for prices, add them together, and check its work by storing intermediate results with line numbers.
The SDK embraces this philosophy completely. Every agent runs in an environment with file system access and bash capabilities, which is why deployment requires containers or sandbox environments.

The Agent SDK vs Client SDK: Understanding the Difference
The Anthropic Client SDK gives you direct API access. You send prompts and implement tool execution yourself. When the model returns a tool use request, you execute it, gather the result, and send another request. You manage the loop.
The Agent SDK inverts this relationship. You provide a prompt and configuration. The SDK handles the tool loop internally, including retries, error handling, context management, and compaction. Claude autonomously reads files, finds bugs, and fixes them without your manual intervention.
This distinction matters enormously for development speed. With the client SDK, building a capable agent requires implementing dozens of edge cases: handling tool execution errors, managing context windows that grow too large, coordinating parallel tool calls, handling interruptions. The Agent SDK handles these concerns because they represent lessons learned from deploying Claude Code to millions of users.

Getting Started in Five Minutes
Install Claude Code first since the Agent SDK uses it as its runtime. On macOS or Linux, run the installation script from claude.ai. Then install the SDK package for your language: npm install @anthropic-ai/claude-agent-sdk for TypeScript or pip install claude-agent-sdk for Python.
Set your API key as an environment variable. If you have already authenticated Claude Code by running claude in your terminal, the SDK uses that authentication automatically. Otherwise, get a key from the Console.
Here is the simplest possible agent in Python:
pythonimport asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="What files are in this directory?",
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
The query function creates an agentic loop that streams messages as Claude works. The async for loop continues while Claude thinks, calls tools, observes results, and decides what to do next. When Claude finishes or hits an error, the loop ends.

The Three-Part Agent Loop: Gather, Act, Verify
Every well-designed agent follows a pattern: gather context, take action, verify the work.
Gathering context means finding the information needed for the task. For Claude Code, this involves grepping and finding relevant files. For an email agent, it means locating relevant emails. This step often gets underestimated. The quality of context gathering directly determines agent performance.
Taking action means using the right tools. Does the agent have code generation capabilities? Can it access bash for flexible composition? Are there specialized tools for the domain?
Verification closes the loop. If you can programmatically verify the agent's work, you have an excellent candidate for automation. Code can be linted and executed. Research can cite sources. Spreadsheets can be validated for null pointers. The agents closest to being generally capable are those with strong verification steps.
A plan might fit between gathering context and taking action, helping the agent think step by step. Plans add latency, so they represent a tradeoff. The SDK supports planning through permission modes and the AskUserQuestion tool, letting Claude clarify requirements before proceeding.

Tools vs Bash vs Code Generation: Choosing Your Approach
The SDK gives you three ways to accomplish tasks, each with distinct tradeoffs.
Traditional tools are extremely structured and reliable. When you need the fastest output with minimal errors and retries, tools excel. However, they consume significant context. Anyone who has built an agent with fifty or a hundred tools knows the model gets confused. Tools also lack composability since you cannot chain them together dynamically.
Bash provides composability through static scripts with low context usage. The agent might need discovery time to figure out what it can do, perhaps running playright --help to understand available subcommands. This progressive disclosure trades some latency for reduced context consumption.
Code generation offers the highest composability with dynamic scripts. These take the longest to execute since they might need linting or compilation. API design becomes crucial here because the agent will compose your APIs in unexpected ways.
Use tools for atomic actions requiring strong guarantees, like writing files that need user approval or sending emails. Use bash for composable actions like searching folders, running git commands, or maintaining memory through the file system. Use code generation for highly dynamic logic, composing multiple APIs, data analysis, or deep research.

The TypeScript SDK: Complete Control
The TypeScript SDK centers on the query function, which returns a Query object extending AsyncGenerator with additional methods for interrupting execution, rewinding files, changing permission modes, and querying available models and commands.
Configuration happens through an options object with properties including allowed tools, system prompt, Model Context Protocol (MCP) servers, permission mode, working directory, hooks, agents, and more. The settingSources property controls whether the SDK loads filesystem settings like CLAUDE.md files, which is important because the SDK defaults to loading no settings for isolation.
Message types flow through the generator including assistant messages with Claude's reasoning, user messages, tool results, partial streaming messages, compact boundaries when conversation history gets summarized, and the final result message containing cost, usage, and any structured output.
The permission system evaluates requests in order: hooks run first and can allow, deny, or continue; then permission rules check deny rules, allow rules, and ask rules; then the active permission mode applies; finally, the canUseTool callback handles anything unresolved. This layered approach provides defense in depth.

TypeScript V2 Preview: Simplified Multi-Turn Conversations
The V2 interface removes the need for async generators and yield coordination. Instead of managing generator state across turns, each turn becomes a separate send and stream cycle.
Create a session, send a message, stream the response. To continue the conversation, call send again on the same session. Claude remembers previous turns automatically. The API surface reduces to three concepts: createSession or resumeSession to start or continue, send to dispatch your message, and stream to get the response.
This makes multi-turn conversations dramatically simpler, though some advanced features like session forking remain V1-only during the preview period.

The Python SDK: Choosing Between query and ClaudeSDKClient
The Python SDK offers two interfaces: query for creating a new session with each interaction, and ClaudeSDKClient for maintaining conversations across multiple exchanges.
Query suits one-off questions, independent tasks, and simple automation scripts. Each call starts fresh with no memory.
ClaudeSDKClient maintains session continuity, supports interrupts, hooks, and custom tools, and allows response-driven logic where your next action depends on Claude's response. Use it when building chat interfaces, REPLs, or when you need Claude to remember context.
The client operates as an async context manager. Connect with an initial prompt, call query to send messages, iterate through receive_response to get messages until a ResultMessage arrives. The interrupt method stops Claude mid-execution when using streaming mode.

Migration from Claude Code SDK: What Changed
The SDK was renamed from Claude Code SDK to Claude Agent SDK, reflecting its broader capabilities beyond coding. Package names changed from @anthropic-ai/claude-code to @anthropic-ai/claude-agent-sdk in TypeScript and from claude-code-sdk to claude-agent-sdk in Python.
Two breaking changes require attention. The system prompt no longer defaults to Claude Code's prompt, so you must explicitly request it if needed. Settings sources no longer load automatically, ensuring SDK applications have predictable behavior independent of local filesystem configurations. This matters for continuous integration environments, deployed applications, and multi-tenant systems where settings leakage between users would cause problems.

Streaming Input: The Recommended Approach
The SDK supports two input modes. Streaming input mode provides a persistent, interactive session where the agent operates as a long-lived process taking user input, handling interruptions, surfacing permission requests, and managing sessions. Single message input provides one-shot queries using session state and resuming.
Streaming input mode enables image uploads attached directly to messages, queued messages that process sequentially with interruption capability, full tool integration with custom MCP servers, hooks support for lifecycle customization, real-time feedback as responses generate, and natural context persistence across turns.
Single message input mode does not support direct image attachments, dynamic message queueing, real-time interruption, or hook integration. Use it when you need stateless operation in environments like lambda functions.

Permissions: Defense in Depth
The permission system provides layered control over tool usage.
Permission modes set global behavior. Default mode requires your canUseTool callback to handle unmatched tools. AcceptEdits auto-approves file operations while still prompting for other actions. BypassPermissions runs everything without prompts, which should only be used in controlled environments. Plan mode prevents tool execution entirely, letting Claude analyze and plan without making changes.
When Claude requests a tool, the SDK checks hooks first, which can allow, deny, or continue. Then it checks permission rules from settings files. Then it applies the active permission mode. Finally, if nothing resolved the request, it calls your canUseTool callback.
The canUseTool callback receives the tool name, input parameters, and context. Return an allow result with potentially modified input, or a deny result with a message explaining why. The callback must return within sixty seconds or Claude assumes denial.

Hooks: Intercepting Agent Behavior
Hooks let you run custom code at key execution points: before and after tool calls, when users submit prompts, when sessions start or end, before conversation compaction, and when permission requests arise.
Each hook has two parts: the callback function containing your logic, and the configuration telling the SDK which event to hook into and which tools to match.
PreToolUse hooks run before tool execution and can block dangerous operations like destructive shell commands. PostToolUse hooks run after execution for logging and auditing. UserPromptSubmit hooks can inject additional context. Stop hooks save session state before exit. PreCompact hooks archive full transcripts before summarization.
Hooks chain in array order. A rate limiter runs first, then authorization, then input sanitization, then logging. If any hook returns deny, the operation blocks regardless of what other hooks return.

Sessions: Maintaining Conversation State
The SDK creates sessions automatically and returns a session ID in the initial system message. Capture this ID to resume sessions later.
Resuming loads conversation history and context automatically, letting Claude continue exactly where it left off. This enables long-running workflows and persisting conversations across application restarts.
Forking creates a new session branch from an existing point. This proves useful for exploring different approaches from the same starting point, testing changes without affecting original history, or maintaining separate conversation paths for experiments.

File Checkpointing: Rewinding Changes
File checkpointing tracks modifications made through Write, Edit, and NotebookEdit tools during a session. You can rewind files to any previous state.
Enable checkpointing in your options, capture checkpoint UUIDs from user messages in the response stream, then call rewindFiles when needed. Rewinding restores files on disk to their state at that checkpoint. Created files get deleted, modified files restore to their previous content.
This enables undoing unwanted changes, exploring alternatives by restoring to checkpoints and trying different approaches, and recovering from incorrect modifications. Changes made through bash commands like echo or sed are not tracked since only the built-in file tools participate in checkpointing.

Structured Outputs: Getting Typed Data Back
Agents return free-form text by default, which works for chat but fails when you need programmatic use of the output. Structured outputs let you define the exact shape of data you want back using JSON Schema.
Define your schema, pass it via the outputFormat option, and the SDK guarantees the final result matches. For full type safety, use Zod in TypeScript or Pydantic in Python to define schemas and get strongly-typed objects back.
The agent can use any tools needed to complete the task. It might search the web, read files, run commands. You still get validated JSON at the end. When the result message arrives, check the subtype field: success means valid output, error_max_structured_output_retries means the agent could not produce valid output after multiple attempts.

Hosting: Deployment Patterns
The SDK differs from traditional stateless LLM APIs because it maintains conversational state and executes commands in a persistent environment. Deployment requires container-based sandboxing for process isolation, resource limits, network control, and ephemeral filesystems.
Each instance needs Python 3.10+ or Node.js 18+, the Claude Code CLI, approximately 1GiB RAM, 5GiB disk, and outbound HTTPS access to api.anthropic.com.
Ephemeral sessions create a new container per user task, then destroy it upon completion. This suits one-off tasks like bug investigation, invoice processing, or translation.
Long-running sessions maintain persistent container instances. This suits proactive agents, site builders, or high-frequency chat bots handling continuous message streams.
Hybrid sessions use ephemeral containers hydrated with history and state from databases or session resumption features. This suits intermittent interaction patterns like project management, deep research, or customer support spanning multiple interactions.
Single containers run multiple Agent SDK processes for agents that must collaborate closely. This is the least common pattern because you must prevent agents from overwriting each other.

MCP Integration: Connecting External Tools
The Model Context Protocol (MCP) is an open standard for connecting agents to external tools and data sources. With MCP, your agent can query databases, integrate with Slack and GitHub, and connect to services without writing custom tool implementations.
MCP servers can run as local stdio processes, connect over HTTP or Server-Sent Events (SSE), or execute directly within your SDK application as SDK MCP servers.
Configure servers in the mcpServers option. Tools follow the naming pattern mcp__servername__toolname. Grant access with allowedTools using wildcards like mcp__github__* for all tools from a server.
Tool search activates automatically when MCP tool descriptions would consume more than ten percent of the context window. Instead of preloading all tools, Claude uses a search tool to discover relevant MCP tools on demand.

Custom Tools: Building Your Own Capabilities
Custom tools extend Claude with your own functionality through in-process MCP servers. Use createSdkMcpServer and tool helper functions to define type-safe tools.
Each tool needs a name, description, input schema defined with Zod, and an async handler function. The handler receives validated arguments and returns content blocks.
Custom MCP tools require streaming input mode. You must use an async generator for the prompt parameter since a simple string will not work with MCP servers.
Error handling should return meaningful feedback rather than throwing. Check response status, validate inputs, and return content blocks with error messages when things go wrong.

Subagents: Parallel and Specialized Work
Subagents are separate agent instances your main agent spawns for focused subtasks. They isolate context, run analyses in parallel, and apply specialized instructions without bloating the main prompt.
Define subagents programmatically with the agents parameter. Each definition includes a description explaining when to use it, a prompt defining behavior, optional tool restrictions, and an optional model override.
Claude decides when to invoke subagents based on descriptions. Write clear descriptions so Claude matches tasks appropriately. You can also explicitly request a subagent by name.
Subagents cannot spawn their own subagents. Do not include the Task tool in a subagent's tools array.
Context isolation means specialized tasks do not pollute the main conversation with irrelevant details. A research-assistant subagent can explore dozens of files and return only relevant findings.
Parallelization means multiple subagents run concurrently. During code review, style-checker, security-scanner, and test-coverage subagents can run simultaneously.

Skills: Specialized Capabilities
Skills extend Claude with capabilities that Claude autonomously invokes when relevant. They are packaged as SKILL.md files containing instructions, descriptions, and optional supporting resources.
Unlike subagents which can be defined programmatically, skills must be created as filesystem artifacts. The SDK loads them from configured filesystem locations when you specify settingSources.
Place project skills in .claude/skills/ for sharing with your team via git. Place personal skills in ~/.claude/skills/ for availability across all your projects.
Claude automatically discovers skills from specified directories and invokes them when relevant to the user's request based on the description field.

Slash Commands: Session Control
Slash commands control sessions with special commands starting with forward slash. Send them through the SDK by including them in your prompt string.
The compact command reduces conversation history by summarizing older messages while preserving important context. The clear command starts fresh by clearing all previous history. The help command provides information about available commands.
You can create custom slash commands as markdown files in .claude/commands/ directories. The filename becomes the command name. Optional YAML frontmatter provides configuration including allowed tools, description, and model override.
Custom commands support arguments using placeholders like $1 and $2. They can execute bash commands and include their output using exclamation mark backtick syntax. They can reference files using the @ prefix.

Cost Tracking: Understanding Token Usage
The SDK provides detailed token usage information for billing. Usage data attaches to assistant messages and includes input tokens, output tokens, cache creation tokens, and cache read tokens.
When Claude sends multiple messages in the same turn like text plus parallel tool calls, they share the same message ID and usage data. Charge only once per unique message ID, not for each individual message.
The final result message contains cumulative usage from all steps including total_cost_usd which is authoritative for billing. The modelUsage field provides per-model breakdown when using multiple models like Haiku for subagents and Opus for the main agent.

The Design Process: Thinking Like Anthropic
When designing an agent, Anthropic recommends thinking through three questions for each capability: What is the best way to search or gather context? What is the best way to take action? What is the best way to verify the work?
Consider a spreadsheet agent. For searching, you might convert to CSV and grep, use AWK for tabular queries, translate to SQLite for SQL queries, search with range syntax like B3:B5 that the model knows well, or search XML since XLSX files are XML internally.
For taking action, you might insert 2D arrays, execute SQL queries, or edit XML directly. The gathering context and taking action APIs often share structure.
For verification, check for null pointers, validate formulas, ensure row counts match expectations. Insert deterministic rules wherever possible since anytime you can verify programmatically improves reliability.
Read transcripts repeatedly. Every time you see the agent running, examine what it does and why. Figure out how to help it. This intuition-building process reveals what your specific domain requires.

Context Engineering: The File System as Memory
Context engineering extends beyond prompts. The file system becomes memory. Scripts become reusable tools. Files become context that the agent can search and reference.
Skills exemplify this approach. They are really just folders the agent can cd into and read, containing detailed instructions and examples. When the agent needs to create a document type, it reads the skill, follows the instructions, and produces consistent results.
Long outputs should go to files rather than staying in context. The agent can then grep across results, check work, and maintain references without polluting the conversation with enormous outputs.
Memory can live in a memories folder where the agent writes insights for future reference. This simple approach leverages the file system rather than requiring specialized memory infrastructure.

Security: The Swiss Cheese Defense
Security comes through multiple layers, each catching what others miss.
Model alignment represents the foundation. Claude models undergo extensive alignment training to avoid harmful actions.
The harness adds permissioning and prompting. A bash parser determines fairly reliably what commands actually do. This is not something you want to build yourself.
Sandboxing provides the final layer. Even if an agent gets compromised, what can it actually do? Network sandboxing prevents exfiltration. File system sandboxing prevents access outside the working directory. Container sandboxing isolates from the host system.
The SDK supports programmatic sandbox configuration for command execution, including network restrictions, excluded commands, and violation handling.

The Future: Simple but Not Easy
Building an agent should be simple. Your final agent should be simple. But simple is not the same as easy.
Start with Claude Code directly. Give it scripts, libraries, and context files. Ask it to accomplish tasks. Watch what it does. Iterate on the prompts, tools, and verification steps. Build something that feels good locally before productionizing.
The amount of code in your agent should not be huge. It does not need to be extremely complex. But it needs to be elegant. It needs to be what the model wants. That interesting insight—"let's turn this spreadsheet into SQL queries"—comes from reading transcripts and understanding how Claude naturally approaches problems.
Simple at the end, but the process of discovering what works requires exploration. The Agent SDK handles the orchestration so you can focus on the domain-specific challenges: designing agentic search interfaces, creating appropriate guardrails, and building verification steps that catch errors before they compound.
The models improve continuously. Rethink and rewrite agent code every six months because assumptions get baked in that no longer apply. We can write code ten times faster now; we should throw out code ten times faster as well. For startups, this represents your largest advantage over larger companies with six-month incubation cycles. Build for the capabilities that exist today.