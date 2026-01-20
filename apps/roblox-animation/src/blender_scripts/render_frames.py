"""
Render animation frames from Blender for Gemini analysis.

Usage:
    blender --background --python render_frames.py -- input.blend output_dir/ [--fps 30]

This script renders each frame of an animation to PNG files for
analysis with Gemini Vision.
"""

import sys
from pathlib import Path


def render_frames(
    input_file: str,
    output_dir: str,
    fps: int = 30,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
) -> None:
    """Render animation frames to PNG files."""
    # Import bpy here since it's only available when running in Blender
    import bpy

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Open the input file
    bpy.ops.wm.open_mainfile(filepath=input_file)

    # Get scene and animation settings
    scene = bpy.context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end

    # Configure render settings
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100
    scene.render.fps = fps

    # Render each frame
    total_frames = frame_end - frame_start + 1
    print(f"Rendering {total_frames} frames to {output_dir}")

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)

        # Set output path for this frame
        frame_filename = f"frame_{frame:04d}.png"
        scene.render.filepath = str(output_path / frame_filename)

        # Render
        bpy.ops.render.render(write_still=True)

        # Progress
        progress = (frame - frame_start + 1) / total_frames * 100
        print(f"Rendered frame {frame}/{frame_end} ({progress:.1f}%)")

    print(f"Done! Rendered {total_frames} frames to {output_dir}")


def main() -> None:
    """Parse arguments and run render."""
    # Get arguments after '--'
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        print("Usage: blender --background --python render_frames.py -- input.blend output_dir/ [--fps 30]")
        sys.exit(1)

    if len(argv) < 2:
        print("Error: Need input.blend and output_dir arguments")
        sys.exit(1)

    input_file = argv[0]
    output_dir = argv[1]

    # Parse optional fps
    fps = 30
    if "--fps" in argv:
        fps_idx = argv.index("--fps")
        if fps_idx + 1 < len(argv):
            fps = int(argv[fps_idx + 1])

    render_frames(input_file, output_dir, fps=fps)


if __name__ == "__main__":
    main()
