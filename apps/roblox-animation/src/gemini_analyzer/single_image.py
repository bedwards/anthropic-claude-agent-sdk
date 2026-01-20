"""
Analyze a single image using Gemini Vision.

Use cases:
- Check animation frames for mesh clipping
- Verify pose correctness
- Compare against reference images
- Analyze screenshots from Roblox
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


def analyze_image(
    image_path: Path,
    prompt: str,
    model: str = "gemini-2.0-flash",
    resolution: str = "medium",
) -> str:
    """
    Analyze a single image using Gemini Vision.

    Args:
        image_path: Path to the image file
        prompt: Analysis prompt describing what to look for
        model: Gemini model to use
        resolution: Image resolution (low, medium, high, ultra_high)

    Returns:
        Analysis text from Gemini
    """
    client = get_client()

    # Read image bytes
    image_bytes = image_path.read_bytes()

    # Determine MIME type from extension
    suffix = image_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/png")

    # Create image part with resolution config
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    # Build the prompt with context
    full_prompt = f"""You are analyzing an animation frame for a Roblox NPC character.

{prompt}

Provide specific, actionable feedback. If you identify issues, describe:
1. What the issue is
2. Where in the frame it occurs
3. How it might be fixed

Be concise but thorough."""

    # Generate response
    response = client.models.generate_content(
        model=model,
        contents=[full_prompt, image_part],
    )

    return response.text or "No analysis returned"


@click.command()
@click.option(
    "--image",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to image file",
)
@click.option(
    "--prompt",
    "-p",
    type=str,
    default="Analyze this animation frame for any issues with pose, clipping, or visual quality.",
    help="Analysis prompt",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default="gemini-2.0-flash",
    help="Gemini model to use",
)
@click.option(
    "--resolution",
    "-r",
    type=click.Choice(["low", "medium", "high", "ultra_high"]),
    default="medium",
    help="Image resolution for analysis",
)
def main(image: Path, prompt: str, model: str, resolution: str) -> None:
    """Analyze a single image using Gemini Vision."""
    try:
        result = analyze_image(image, prompt, model, resolution)
        click.echo(result)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
