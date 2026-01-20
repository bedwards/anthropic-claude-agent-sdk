# Animation Worker Agent

Autonomous animation worker using Claude Agent SDK with Gemini vision analysis for Roblox animations.

## Purpose

This agent is invoked to handle the complete lifecycle of creating a Roblox animation from a GitHub issue through quality verification.

## Key Principle

**Gemini's verdict is authoritative.** Claude orchestrates the workflow and generates animation code, but Gemini determines when the animation meets quality standards. Claude should not second-guess Gemini's "done" or "needs_work" verdicts.

## Lifecycle

1. **Initialize**: Set up output directories
2. **Read Requirements**: Parse GitHub issue for animation description
3. **Generate Code**: Claude generates Blender Python animation code
4. **Create Animation**: Run Blender headlessly to create .blend file
5. **Render Frames**: Render animation to PNG frames
6. **Analyze Quality**: Gemini vision analyzes frames, provides verdict
7. **Iterate**: If "needs_work", feed feedback to Claude for improvements
8. **Export**: Convert final animation to Roblox format

## Usage

```bash
# Run animation worker for an issue
animation-worker run 68 --repo owner/repo

# Check status
animation-worker status 68

# List all animation workers
animation-worker list-workers
```

## Configuration

Environment variables:
- `GITHUB_TOKEN`: Required for GitHub API access
- `GEMINI_API_KEY`: Required for Gemini vision analysis

CLI options:
- `--output-dir`: Where to save animation files
- `--max-iterations`: Maximum iterations (default: 10)
- `--quality-threshold`: Minimum quality score (default: 85)
- `--fps`: Animation frames per second (default: 30)
- `--duration`: Animation duration in seconds (default: 2.0)

## Dependencies

System tools (must be in PATH):
- `blender`: Blender 4.x with Python API
- `anim2rbx`: FBX to Roblox KeyframeSequence converter
- `assimp@5`: Required library for anim2rbx (set DYLD_LIBRARY_PATH)

Python packages:
- `claude-agent-sdk`: Claude AI integration
- `google-genai`: Gemini vision API
- `pygithub`: GitHub API

## Development

```bash
cd agents/animation-worker
uv sync
uv run animation-worker --help
```

## Animation Tools

This worker uses the animation tools from `apps/roblox-animation/src/animation_tools/`:
- `create_animation`: Generate Blender animation from code
- `render_frames`: Render animation to PNG frames
- `analyze_animation`: Gemini vision analysis with verdict

## Status Monitoring

Status files are written to `--status-dir` as JSON:
- `animation-worker-{issue}.json`: Full status including phase, iterations, quality scores

Manager notifications written to `--notification-file`:
- `iteration_complete`: After each iteration with quality score
- `completed`: Animation finished successfully
- `failed`: Max iterations reached without meeting threshold
- `blocked`: Cannot proceed (missing dependencies, etc.)

## Key Behaviors

1. **Trusts Gemini's verdict**: Does not override "done" or "needs_work"
2. **Iterates until quality met**: Keeps improving until threshold reached
3. **Reports progress**: Logs each iteration's quality score
4. **Exports to Roblox**: Converts final animation to .rbxmx format
