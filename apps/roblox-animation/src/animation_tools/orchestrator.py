"""
Animation workflow orchestrator for Claude worker agents.

This module provides a high-level interface for the animation creation loop:
1. Create animation from prompt + feedback
2. Render frames
3. Analyze with Gemini (provides authoritative verdict)
4. Repeat until done

The key principle: Gemini's verdict is authoritative. Claude should not
second-guess whether an animation is "done" - that's Gemini's job.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .analyze_animation import AnimationAnalysisResult, analyze_animation
from .create_animation import AnimationResult, create_animation
from .render_frames import RenderResult, render_frames


@dataclass
class IterationResult:
    """Result of a single animation iteration."""

    iteration: int
    animation: AnimationResult
    render: RenderResult
    analysis: AnimationAnalysisResult
    is_complete: bool


@dataclass
class AnimationWorkflowResult:
    """Final result of the animation workflow."""

    success: bool
    iterations: list[IterationResult]
    final_blend_file: Path | None
    final_frames_dir: Path | None
    final_quality_score: int
    message: str


@dataclass
class AnimationWorkflowConfig:
    """Configuration for animation workflow."""

    output_dir: Path
    max_iterations: int = 10
    quality_threshold: int = 85
    fps: int = 30
    duration: float = 2.0
    render_resolution: tuple[int, int] = (1280, 720)
    render_samples: int = 16


def run_animation_workflow(
    prompt: str,
    requirements: str,
    config: AnimationWorkflowConfig,
    generate_animation_code: Callable[[str, list[str]], str] | None = None,
    on_iteration: Callable[[IterationResult], None] | None = None,
) -> AnimationWorkflowResult:
    """
    Run the complete animation workflow.

    Args:
        prompt: What animation to create (e.g., "A camel walking through desert")
        requirements: Quality requirements for Gemini analysis
        config: Workflow configuration
        generate_animation_code: Optional callback to generate Blender code.
            Signature: (prompt, feedback) -> blender_python_code
            If not provided, uses placeholder animation.
        on_iteration: Optional callback called after each iteration

    Returns:
        AnimationWorkflowResult with final status and all iterations
    """
    config.output_dir.mkdir(parents=True, exist_ok=True)

    iterations: list[IterationResult] = []
    feedback: list[str] = []

    for i in range(config.max_iterations):
        iteration_num = i + 1
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration_num}/{config.max_iterations}")
        print(f"{'='*60}")

        # Paths for this iteration
        blend_file = config.output_dir / f"animation_v{iteration_num}.blend"
        frames_dir = config.output_dir / f"frames_v{iteration_num}"

        # Step 1: Generate animation code (Claude's job)
        print("\n[1/3] Creating animation...")
        if generate_animation_code:
            animation_code = generate_animation_code(prompt, feedback)
        else:
            animation_code = None  # Use placeholder

        animation_result = create_animation(
            prompt=prompt,
            output_path=blend_file,
            feedback=feedback if feedback else None,
            animation_code=animation_code,
            fps=config.fps,
            duration=config.duration,
        )

        if not animation_result.success:
            print(f"Animation creation failed: {animation_result.message}")
            return AnimationWorkflowResult(
                success=False,
                iterations=iterations,
                final_blend_file=None,
                final_frames_dir=None,
                final_quality_score=0,
                message=f"Animation creation failed at iteration {iteration_num}: {animation_result.message}",
            )

        # Step 2: Render frames
        print("\n[2/3] Rendering frames...")
        render_result = render_frames(
            blend_file=blend_file,
            output_dir=frames_dir,
            resolution=config.render_resolution,
            samples=config.render_samples,
        )

        if not render_result.success:
            print(f"Rendering failed: {render_result.message}")
            return AnimationWorkflowResult(
                success=False,
                iterations=iterations,
                final_blend_file=blend_file,
                final_frames_dir=None,
                final_quality_score=0,
                message=f"Rendering failed at iteration {iteration_num}: {render_result.message}",
            )

        # Step 3: Analyze with Gemini (authoritative verdict)
        print("\n[3/3] Analyzing with Gemini...")
        analysis_result = analyze_animation(
            frame_paths=render_result.frame_paths,
            requirements=requirements,
            quality_threshold=config.quality_threshold,
        )

        print(f"\nVerdict: {analysis_result.verdict.upper()}")
        print(f"Quality Score: {analysis_result.quality_score}/100")

        # Record this iteration
        iteration_result = IterationResult(
            iteration=iteration_num,
            animation=animation_result,
            render=render_result,
            analysis=analysis_result,
            is_complete=(analysis_result.verdict == "done"),
        )
        iterations.append(iteration_result)

        # Callback
        if on_iteration:
            on_iteration(iteration_result)

        # Check if done
        if analysis_result.verdict == "done":
            print(f"\n{'='*60}")
            print("ANIMATION COMPLETE!")
            print(f"{'='*60}")
            return AnimationWorkflowResult(
                success=True,
                iterations=iterations,
                final_blend_file=blend_file,
                final_frames_dir=frames_dir,
                final_quality_score=analysis_result.quality_score,
                message=f"Animation completed after {iteration_num} iteration(s). Quality: {analysis_result.quality_score}/100",
            )

        # Prepare feedback for next iteration
        print(f"\nIssues found: {len(analysis_result.issues)}")
        for issue in analysis_result.issues:
            print(f"  - {issue}")

        print(f"\nSuggestions: {len(analysis_result.suggestions)}")
        feedback = analysis_result.suggestions
        for suggestion in feedback:
            print(f"  - {suggestion}")

    # Max iterations reached
    final_iter = iterations[-1] if iterations else None
    return AnimationWorkflowResult(
        success=False,
        iterations=iterations,
        final_blend_file=final_iter.animation.blend_file if final_iter else None,
        final_frames_dir=final_iter.render.frames_dir if final_iter else None,
        final_quality_score=final_iter.analysis.quality_score if final_iter else 0,
        message=f"Max iterations ({config.max_iterations}) reached without meeting quality threshold",
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m animation_tools.orchestrator <output_dir> <prompt>")
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    prompt = sys.argv[2]
    requirements = "Create a smooth, appealing animation suitable for a Roblox game"

    config = AnimationWorkflowConfig(
        output_dir=output_dir,
        max_iterations=3,  # Limit for testing
    )

    result = run_animation_workflow(prompt, requirements, config)

    print(f"\n{'='*60}")
    print(f"WORKFLOW RESULT")
    print(f"{'='*60}")
    print(f"Success: {result.success}")
    print(f"Iterations: {len(result.iterations)}")
    print(f"Final Quality: {result.final_quality_score}/100")
    print(f"Message: {result.message}")
