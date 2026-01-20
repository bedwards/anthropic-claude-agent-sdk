"""
Animation tools for Claude worker agents.

These tools are designed to be called by a Claude worker agent, with Gemini
providing visual analysis. The key principle: Gemini is a tool, not an agent.
Claude owns the workflow; Gemini provides verdicts.

Tools:
- create_animation: Generate/modify Blender animation from a prompt
- render_frames: Render animation frames to images
- analyze_animation: Analyze frames with Gemini, returns done/needs_work verdict

Usage:
    from animation_tools import create_animation, render_frames, analyze_animation

    # Claude worker loop
    while True:
        anim_path = create_animation(prompt, feedback=previous_feedback)
        frames = render_frames(anim_path, output_dir)
        result = analyze_animation(frames, criteria)

        if result["verdict"] == "done":
            break
        previous_feedback = result["suggestions"]
"""

from .create_animation import create_animation, AnimationResult
from .render_frames import render_frames, RenderResult
from .analyze_animation import analyze_animation, AnimationAnalysisResult
from .orchestrator import (
    run_animation_workflow,
    AnimationWorkflowConfig,
    AnimationWorkflowResult,
    IterationResult,
)

__all__ = [
    "create_animation",
    "AnimationResult",
    "render_frames",
    "RenderResult",
    "analyze_animation",
    "AnimationAnalysisResult",
    "run_animation_workflow",
    "AnimationWorkflowConfig",
    "AnimationWorkflowResult",
    "IterationResult",
]
