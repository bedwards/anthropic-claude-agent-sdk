"""
Analyze animation frames using Gemini Vision.

This tool is responsible for:
1. Analyzing rendered animation frames
2. Providing a verdict: "done" or "needs_work"
3. Listing specific issues found
4. Providing actionable suggestions for improvement

The verdict is authoritative - Claude should not second-guess it.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from google import genai
from google.genai import types


@dataclass
class AnimationAnalysisResult:
    """Result of animation analysis."""

    verdict: Literal["done", "needs_work"]
    quality_score: int  # 0-100
    issues: list[str]  # Specific problems found
    suggestions: list[str]  # Actionable fixes
    frame_notes: dict[str, str]  # Per-frame observations (frame_name -> note)
    summary: str  # Overall assessment


def get_gemini_client() -> genai.Client:
    """Get Gemini client from environment or .env file."""
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        # Try reading from .env in various locations
        for env_path in [".env", "../.env", "../../.env"]:
            if Path(env_path).exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1]
                            break
                if api_key:
                    break

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment or .env file. "
            "Set it with: export GEMINI_API_KEY=your-key"
        )

    return genai.Client(api_key=api_key)


ANALYSIS_PROMPT = """You are an expert animation analyst reviewing animation frames for a Roblox game.

ANIMATION REQUIREMENTS:
{requirements}

QUALITY CRITERIA:
1. **Smoothness**: No pops, hitches, or sudden jumps between frames
2. **Timing**: Motion feels natural with proper acceleration/deceleration
3. **Weight**: Character appears grounded with believable physics
4. **Poses**: Each pose is clear, readable, and anatomically reasonable
5. **Appeal**: Animation has life, personality, and visual interest
6. **Loop**: If looping, the start and end frames blend seamlessly

YOUR TASK:
Analyze these {num_frames} frames and provide:

1. **VERDICT**: Either "DONE" (animation meets requirements and quality bar) or "NEEDS_WORK" (has issues that must be fixed)

2. **QUALITY_SCORE**: 0-100 rating
   - 90-100: Professional quality, ready to ship
   - 70-89: Good but minor polish needed
   - 50-69: Acceptable but noticeable issues
   - Below 50: Significant problems

3. **ISSUES**: List each specific problem found. Be precise:
   - BAD: "Animation looks weird"
   - GOOD: "Frame 12-15: Left front leg clips through body during stride"

4. **SUGGESTIONS**: Actionable fixes for each issue:
   - BAD: "Make it better"
   - GOOD: "Reduce left front leg rotation by ~15 degrees at frame 13"

5. **FRAME_NOTES**: For any problematic frames, note the specific issue

6. **SUMMARY**: One paragraph overall assessment

IMPORTANT:
- Be specific about frame numbers
- A score of 85+ with no blocking issues = DONE
- Any score below 70 or blocking issues = NEEDS_WORK
- "Blocking issues" include: clipping, broken poses, obvious pops, unnatural motion

Respond in this exact JSON format:
{{
    "verdict": "DONE" or "NEEDS_WORK",
    "quality_score": <0-100>,
    "issues": ["issue 1", "issue 2", ...],
    "suggestions": ["suggestion 1", "suggestion 2", ...],
    "frame_notes": {{"frame_001.png": "note", ...}},
    "summary": "Overall assessment paragraph"
}}
"""


def analyze_animation(
    frame_paths: list[Path] | list[str],
    requirements: str,
    model: str = "gemini-2.0-flash",
    quality_threshold: int = 85,
) -> AnimationAnalysisResult:
    """
    Analyze animation frames and return a verdict.

    Args:
        frame_paths: List of paths to frame images (in order)
        requirements: Description of what the animation should achieve
        model: Gemini model to use
        quality_threshold: Minimum score for "done" verdict (default 85)

    Returns:
        AnimationAnalysisResult with verdict, score, issues, and suggestions
    """
    client = get_gemini_client()

    # Convert to Path objects and sort
    frames = sorted([Path(p) for p in frame_paths])

    if not frames:
        return AnimationAnalysisResult(
            verdict="needs_work",
            quality_score=0,
            issues=["No frames provided for analysis"],
            suggestions=["Render animation frames first"],
            frame_notes={},
            summary="Cannot analyze: no frames provided.",
        )

    # Build the prompt
    prompt = ANALYSIS_PROMPT.format(requirements=requirements, num_frames=len(frames))

    # Build parts with images
    parts: list[types.Part | str] = [prompt]

    for frame_path in frames:
        if not frame_path.exists():
            continue

        image_bytes = frame_path.read_bytes()
        suffix = frame_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        mime_type = mime_types.get(suffix, "image/png")

        parts.append(f"\n--- {frame_path.name} ---")
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    # Call Gemini
    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    # Parse response
    import json

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
        else:
            return AnimationAnalysisResult(
                verdict="needs_work",
                quality_score=0,
                issues=["Failed to parse Gemini response"],
                suggestions=["Retry analysis"],
                frame_notes={},
                summary=f"Parse error. Raw response: {response.text[:500]}",
            )

    # Normalize verdict
    verdict_raw = result.get("verdict", "NEEDS_WORK").upper()
    quality_score = int(result.get("quality_score", 0))

    # Apply quality threshold
    if verdict_raw == "DONE" and quality_score < quality_threshold:
        verdict = "needs_work"
    else:
        verdict = "done" if verdict_raw == "DONE" else "needs_work"

    return AnimationAnalysisResult(
        verdict=verdict,
        quality_score=quality_score,
        issues=result.get("issues", []),
        suggestions=result.get("suggestions", []),
        frame_notes=result.get("frame_notes", {}),
        summary=result.get("summary", "No summary provided."),
    )


if __name__ == "__main__":
    # CLI for testing
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m animation_tools.analyze_animation <frames_dir> <requirements>")
        sys.exit(1)

    frames_dir = Path(sys.argv[1])
    requirements = sys.argv[2]

    frames = sorted(frames_dir.glob("*.png"))
    print(f"Analyzing {len(frames)} frames...")

    result = analyze_animation(frames, requirements)

    print(f"\nVerdict: {result.verdict.upper()}")
    print(f"Quality Score: {result.quality_score}/100")
    print(f"\nIssues ({len(result.issues)}):")
    for issue in result.issues:
        print(f"  - {issue}")
    print(f"\nSuggestions ({len(result.suggestions)}):")
    for suggestion in result.suggestions:
        print(f"  - {suggestion}")
    print(f"\nSummary: {result.summary}")
