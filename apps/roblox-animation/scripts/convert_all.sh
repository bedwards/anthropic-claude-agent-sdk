#!/bin/bash
# Convert all FBX files in a directory to Roblox KeyframeSequence (.rbxm)
#
# Usage: ./convert_all.sh input_dir/ output_dir/
#
# Requires: anim2rbx (cargo install anim2rbx)

set -euo pipefail

# Set library path for anim2rbx (assimp@5 is keg-only)
export DYLD_LIBRARY_PATH="/usr/local/opt/assimp@5/lib:${DYLD_LIBRARY_PATH:-}"

INPUT_DIR="${1:?Usage: $0 input_dir/ output_dir/}"
OUTPUT_DIR="${2:?Usage: $0 input_dir/ output_dir/}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check for anim2rbx
if ! command -v anim2rbx &> /dev/null; then
    echo "Error: anim2rbx not found. Install with: cargo install anim2rbx"
    exit 1
fi

# Convert each FBX file
count=0
for fbx in "$INPUT_DIR"/*.fbx "$INPUT_DIR"/*.FBX; do
    # Skip if no matches
    [ -e "$fbx" ] || continue

    # Get base name without extension
    base=$(basename "$fbx" | sed 's/\.[fF][bB][xX]$//')
    output="$OUTPUT_DIR/${base}.rbxm"

    echo "Converting: $fbx -> $output"
    anim2rbx "$fbx" -o "$output"

    ((count++))
done

echo "Done! Converted $count files."
