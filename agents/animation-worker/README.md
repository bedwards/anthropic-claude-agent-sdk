# Animation Worker Agent

Autonomous animation worker agent using Claude Agent SDK with Gemini vision analysis for creating Roblox animations.

## Purpose

This agent creates high-quality Roblox animations by:
1. Reading requirements from a GitHub issue
2. Using Claude to generate Blender animation code
3. Rendering frames and analyzing with Gemini vision
4. Iterating until quality threshold is met
5. Exporting to Roblox format using anim2rbx

## Key Principle

**Gemini's verdict is authoritative.** Claude should not second-guess whether an animation is "done" - that's Gemini's job. Claude owns the workflow; Gemini provides verdicts.

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
- `--max-iterations`: Maximum iterations before failing
- `--quality-threshold`: Minimum quality score (0-100)
- `--fps`: Animation frames per second
- `--duration`: Animation duration in seconds

## Workflow

1. **Read Requirements**: Parse GitHub issue for animation description and quality requirements
2. **Generate Code**: Use Claude to generate Blender Python animation code
3. **Create Animation**: Run Blender headlessly to create .blend file
4. **Render Frames**: Render animation frames to PNG files
5. **Analyze Quality**: Gemini vision analyzes frames and provides verdict
6. **Iterate**: If "needs_work", feed Gemini's suggestions back to Claude
7. **Export**: Convert final animation to Roblox format using anim2rbx

## GitHub Issue Format

For best results, create issues with this structure:

```markdown
## Animation Description
A camel walking gracefully through a desert landscape...

## Quality Requirements
- Smooth leg movement with realistic gait
- Natural head and neck motion
- Appropriate timing and pacing
```

## Development

```bash
cd agents/animation-worker
uv sync
uv run animation-worker --help
```

## Dependencies

- **Claude Agent SDK**: For Claude AI integration
- **google-genai**: For Gemini vision analysis
- **Blender**: For animation creation (must be in PATH)
- **anim2rbx**: For Roblox format conversion
- **assimp@5**: Library required by anim2rbx

## Status Files

Status files are written to `--status-dir` as JSON:
- `animation-worker-{issue}.json`: Full status including iterations, quality scores, logs
