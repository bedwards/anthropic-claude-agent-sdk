"""
Analyze a sequence of animation frames using Gemini Vision.

Use cases:
- Detect hitches/pops in animation
- Verify timing and weight shift
- Check ground contact accuracy
- Analyze walk cycles for smoothness
"""

import os
import sys
from pathlib import Path

import click
from google import genai
from google.genai import types


def get_client() -> genai.Client:
    """Get configured Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable required")
    return genai.Client(api_key=api_key)


def get_frame_files(frames_dir: Path, pattern: str = "*.png") -> list[Path]:
    """Get sorted list of frame files from directory."""
    frames = sorted(frames_dir.glob(pattern))
    if not frames:
        raise ValueError(f"No frames found matching {pattern} in {frames_dir}")
    return frames


def analyze_frames(
    frames_dir: Path,
    prompt: str,
    fps: int = 30,
    model: str = "gemini-2.0-flash",
    max_frames: int = 60,
    sample_rate: int = 1,
) -> str:
    """
    Analyze a sequence of animation frames using Gemini Vision.

    Args:
        frames_dir: Directory containing frame images (named sequentially)
        prompt: Analysis prompt describing what to look for
        fps: Frames per second of the original animation
        model: Gemini model to use
        max_frames: Maximum number of frames to analyze
        sample_rate: Sample every Nth frame (1 = all frames)

    Returns:
        Analysis text from Gemini
    """
    client = get_client()

    # Get frame files
    frame_files = get_frame_files(frames_dir)

    # Sample frames if needed
    if sample_rate > 1:
        frame_files = frame_files[::sample_rate]

    # Limit to max_frames
    if len(frame_files) > max_frames:
        # Sample evenly across the animation
        step = len(frame_files) // max_frames
        frame_files = frame_files[::step][:max_frames]

    # Build parts list with images
    parts: list[types.Part | str] = []

    # Add context prompt
    context = f"""You are analyzing an animation sequence for a Roblox NPC character.

Animation info:
- Original FPS: {fps}
- Frames provided: {len(frame_files)}
- Sample rate: every {sample_rate} frame(s)

{prompt}

Analyze the sequence for:
1. Smoothness - any hitches, pops, or sudden movements
2. Timing - does the motion feel natural and properly timed
3. Weight - does the character feel grounded with proper weight shift
4. Continuity - any discontinuities between frames
5. Technical issues - clipping, incorrect poses, floating/sliding

For each issue found, specify:
- Frame number(s) where it occurs
- Description of the issue
- Suggested fix

Be specific and actionable."""

    parts.append(context)

    # Add each frame with its number
    for i, frame_path in enumerate(frame_files):
        image_bytes = frame_path.read_bytes()

        suffix = frame_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")

        parts.append(f"\n--- Frame {i + 1} ({frame_path.name}) ---")
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    # Generate response
    response = client.models.generate_content(
        model=model,
        contents=parts,
    )

    return response.text or "No analysis returned"


@click.command()
@click.option(
    "--frames-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing frame images",
)
@click.option(
    "--prompt",
    "-p",
    type=str,
    default="Analyze this animation for smoothness, timing, and any technical issues.",
    help="Analysis prompt",
)
@click.option(
    "--fps",
    type=int,
    default=30,
    help="Original animation FPS",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default="gemini-2.0-flash",
    help="Gemini model to use",
)
@click.option(
    "--max-frames",
    type=int,
    default=60,
    help="Maximum frames to analyze (will sample evenly if exceeded)",
)
@click.option(
    "--sample-rate",
    type=int,
    default=1,
    help="Sample every Nth frame",
)
@click.option(
    "--pattern",
    type=str,
    default="*.png",
    help="Glob pattern for frame files",
)
def main(
    frames_dir: Path,
    prompt: str,
    fps: int,
    model: str,
    max_frames: int,
    sample_rate: int,
    pattern: str,
) -> None:
    """Analyze a sequence of animation frames using Gemini Vision."""
    try:
        result = analyze_frames(
            frames_dir,
            prompt,
            fps=fps,
            model=model,
            max_frames=max_frames,
            sample_rate=sample_rate,
        )
        click.echo(result)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
