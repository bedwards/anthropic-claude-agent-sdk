#!/bin/bash
# Full animation pipeline: Blender -> FBX -> KeyframeSequence -> Analysis
#
# Usage: ./full_pipeline.sh animation.blend output_dir/
#
# This script:
# 1. Exports animation from Blender to FBX
# 2. Converts FBX to Roblox KeyframeSequence (.rbxm)
# 3. Renders frames for analysis
# 4. Analyzes frames with Gemini
#
# Requires:
#   - Blender
#   - anim2rbx (cargo install anim2rbx)
#   - GEMINI_API_KEY environment variable
#   - uv (for running Python)

set -euo pipefail

# Set library path for anim2rbx (assimp@5 is keg-only)
export DYLD_LIBRARY_PATH="/usr/local/opt/assimp@5/lib:${DYLD_LIBRARY_PATH:-}"

BLEND_FILE="${1:?Usage: $0 animation.blend output_dir/}"
OUTPUT_DIR="${2:?Usage: $0 animation.blend output_dir/}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get base name
BASE_NAME=$(basename "$BLEND_FILE" .blend)
FBX_FILE="$OUTPUT_DIR/${BASE_NAME}.fbx"
RBXM_FILE="$OUTPUT_DIR/${BASE_NAME}.rbxm"
FRAMES_DIR="$OUTPUT_DIR/frames"

echo "=== Step 1: Export to FBX ==="
blender --background \
    --python "$PROJECT_DIR/src/blender_scripts/export_animation.py" \
    -- "$BLEND_FILE" "$FBX_FILE"

echo ""
echo "=== Step 2: Convert to KeyframeSequence ==="
if command -v anim2rbx &> /dev/null; then
    anim2rbx "$FBX_FILE" -o "$RBXM_FILE"
    echo "Created: $RBXM_FILE"
else
    echo "Warning: anim2rbx not found, skipping conversion"
    echo "Install with: cargo install anim2rbx"
fi

echo ""
echo "=== Step 3: Render frames ==="
mkdir -p "$FRAMES_DIR"
blender --background \
    --python "$PROJECT_DIR/src/blender_scripts/render_frames.py" \
    -- "$BLEND_FILE" "$FRAMES_DIR" --fps 30

echo ""
echo "=== Step 4: Analyze with Gemini ==="
if [ -n "${GEMINI_API_KEY:-}" ]; then
    cd "$PROJECT_DIR"
    uv run python -m gemini_analyzer.frame_sequence \
        --frames-dir "$FRAMES_DIR" \
        --prompt "Analyze this animation for smoothness, timing, weight distribution, and any technical issues." \
        --fps 30
else
    echo "Warning: GEMINI_API_KEY not set, skipping analysis"
fi

echo ""
echo "=== Pipeline complete ==="
echo "Outputs:"
echo "  FBX: $FBX_FILE"
[ -f "$RBXM_FILE" ] && echo "  KeyframeSequence: $RBXM_FILE"
echo "  Frames: $FRAMES_DIR/"
