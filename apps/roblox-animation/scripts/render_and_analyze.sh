#!/bin/bash
# Render animation frames and analyze with Gemini
#
# Usage: ./render_and_analyze.sh animation.blend [prompt]
#
# Requires:
#   - Blender
#   - GEMINI_API_KEY environment variable
#   - uv (for running Python)

set -euo pipefail

BLEND_FILE="${1:?Usage: $0 animation.blend [prompt]}"
PROMPT="${2:-Analyze this walk cycle animation for smoothness, timing, and any technical issues.}"

# Create temp directory for frames
FRAMES_DIR=$(mktemp -d)
trap 'rm -rf "$FRAMES_DIR"' EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Rendering frames from $BLEND_FILE ==="
blender --background \
    --python "$PROJECT_DIR/src/blender_scripts/render_frames.py" \
    -- "$BLEND_FILE" "$FRAMES_DIR" --fps 30

echo ""
echo "=== Analyzing frames with Gemini ==="
cd "$PROJECT_DIR"
uv run python -m gemini_analyzer.frame_sequence \
    --frames-dir "$FRAMES_DIR" \
    --prompt "$PROMPT" \
    --fps 30

echo ""
echo "=== Analysis complete ==="
