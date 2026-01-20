"""
Render animation frames from a Blender file.

This tool renders each frame of an animation to PNG files for analysis.
"""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RenderResult:
    """Result of frame rendering."""

    frames_dir: Path
    frame_paths: list[Path]
    success: bool
    message: str


RENDER_SCRIPT = '''"""
Render animation frames to PNG files.
"""

import bpy
import os

# Configuration from command line
output_dir = "{output_dir}"
resolution_x = {resolution_x}
resolution_y = {resolution_y}
samples = {samples}

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Configure render settings
scene = bpy.context.scene
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = resolution_x
scene.render.resolution_y = resolution_y
scene.render.resolution_percentage = 100

# Use EEVEE for speed (can change to CYCLES for quality)
scene.render.engine = 'BLENDER_EEVEE_NEXT'
if hasattr(scene.eevee, 'taa_render_samples'):
    scene.eevee.taa_render_samples = samples

# Get frame range
frame_start = scene.frame_start
frame_end = scene.frame_end
total_frames = frame_end - frame_start + 1

print(f"Rendering {{total_frames}} frames to {{output_dir}}")

# Render each frame
for frame in range(frame_start, frame_end + 1):
    scene.frame_set(frame)

    # Set output path for this frame
    frame_filename = f"frame_{{frame:04d}}.png"
    scene.render.filepath = os.path.join(output_dir, frame_filename)

    # Render
    bpy.ops.render.render(write_still=True)

    # Progress
    progress = (frame - frame_start + 1) / total_frames * 100
    print(f"Rendered frame {{frame}}/{{frame_end}} ({{progress:.1f}}%)")

print(f"Done! Rendered {{total_frames}} frames to {{output_dir}}")
'''


def render_frames(
    blend_file: Path | str,
    output_dir: Path | str,
    resolution: tuple[int, int] = (1920, 1080),
    samples: int = 16,
) -> RenderResult:
    """
    Render animation frames from a Blender file.

    Args:
        blend_file: Path to the .blend file
        output_dir: Directory to save rendered frames
        resolution: (width, height) of rendered frames
        samples: Render samples (higher = better quality, slower)

    Returns:
        RenderResult with paths to all rendered frames
    """
    blend_file = Path(blend_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not blend_file.exists():
        return RenderResult(
            frames_dir=output_dir,
            frame_paths=[],
            success=False,
            message=f"Blend file not found: {blend_file}",
        )

    # Generate render script
    script_content = RENDER_SCRIPT.format(
        output_dir=str(output_dir).replace("\\", "/"),
        resolution_x=resolution[0],
        resolution_y=resolution[1],
        samples=samples,
    )

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_content)
        script_path = f.name

    try:
        # Run Blender in headless mode
        result = subprocess.run(
            ["blender", "--background", str(blend_file), "--python", script_path],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout for rendering
        )

        # Collect rendered frames
        frame_paths = sorted(output_dir.glob("frame_*.png"))

        if result.returncode != 0 and not frame_paths:
            return RenderResult(
                frames_dir=output_dir,
                frame_paths=[],
                success=False,
                message=f"Blender render failed: {result.stderr}",
            )

        if not frame_paths:
            return RenderResult(
                frames_dir=output_dir,
                frame_paths=[],
                success=False,
                message="Rendering completed but no frames were created",
            )

        return RenderResult(
            frames_dir=output_dir,
            frame_paths=frame_paths,
            success=True,
            message=f"Rendered {len(frame_paths)} frames to {output_dir}",
        )

    except subprocess.TimeoutExpired:
        # Check if any frames were rendered before timeout
        frame_paths = sorted(output_dir.glob("frame_*.png"))
        return RenderResult(
            frames_dir=output_dir,
            frame_paths=frame_paths,
            success=len(frame_paths) > 0,
            message=f"Render timed out. {len(frame_paths)} frames completed.",
        )
    finally:
        # Clean up temp script
        Path(script_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m animation_tools.render_frames <input.blend> <output_dir>")
        sys.exit(1)

    blend_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    print(f"Rendering frames from: {blend_file}")
    result = render_frames(blend_file, output_dir)

    print(f"\nSuccess: {result.success}")
    print(f"Message: {result.message}")
    if result.frame_paths:
        print(f"Frames: {len(result.frame_paths)}")
        print(f"First: {result.frame_paths[0]}")
        print(f"Last: {result.frame_paths[-1]}")
