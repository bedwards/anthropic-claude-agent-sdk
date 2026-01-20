"""
Main animation worker agent implementation using Claude Agent SDK.

This agent creates Roblox animations by:
1. Reading requirements from a GitHub issue
2. Using Claude Agent SDK to generate Blender animation code
3. Rendering frames and analyzing with Gemini vision
4. Iterating until quality threshold is met
5. Exporting to Roblox format
"""

import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock

from .models import AnimationPhase, AnimationWorkerConfig, LogLevel, NotificationType
from .status_manager import AnimationStatusManager

# Add the animation tools to the path
ANIMATION_TOOLS_PATH = Path(__file__).parent.parent.parent.parent.parent / "apps/roblox-animation/src"
if str(ANIMATION_TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(ANIMATION_TOOLS_PATH))


class AnimationWorkerAgent:
    """
    Autonomous animation worker agent that creates Roblox animations.

    Workflow:
    1. Read GitHub issue for animation requirements
    2. Use Claude to generate Blender Python animation code
    3. Run Blender headlessly to create animation
    4. Render frames
    5. Analyze frames with Gemini vision (authoritative verdict)
    6. If "needs_work", use Claude to improve based on Gemini feedback
    7. Repeat until Gemini says "done" or max iterations reached
    8. Export to Roblox format using anim2rbx
    """

    def __init__(self, config: AnimationWorkerConfig, issue_number: int) -> None:
        self.config = config
        self.issue_number = issue_number

        # Managers will be initialized in run()
        self.status_manager: AnimationStatusManager | None = None

    async def run(self) -> bool:
        """
        Run the full animation worker lifecycle.
        Returns True if successful, False otherwise.
        """
        branch = f"animation/issue-{self.issue_number}"
        worktree_path = self.config.worktree_base_dir / f"animation-{self.issue_number}"

        # Initialize status manager
        self.status_manager = AnimationStatusManager(
            self.config,
            self.issue_number,
            branch,
            str(worktree_path),
        )
        await self.status_manager.initialize()

        try:
            # Phase 1: Initialize
            await self.status_manager.set_phase(AnimationPhase.INITIALIZING)
            self.config.output_dir.mkdir(parents=True, exist_ok=True)

            # Phase 2: Read requirements from GitHub issue
            await self.status_manager.set_phase(AnimationPhase.READING_REQUIREMENTS)
            requirements = await self._get_animation_requirements()
            if not requirements:
                await self.status_manager.set_blocked("Failed to read animation requirements")
                return False

            prompt = requirements["prompt"]
            quality_requirements = requirements["quality_requirements"]

            self.status_manager.log(LogLevel.INFO, f"Animation prompt: {prompt}")
            self.status_manager.log(LogLevel.INFO, f"Quality requirements: {quality_requirements}")

            # Import animation tools
            try:
                from animation_tools import (
                    analyze_animation,
                    create_animation,
                    render_frames,
                )
            except ImportError as e:
                await self.status_manager.set_blocked(f"Failed to import animation tools: {e}")
                return False

            # Animation iteration loop
            feedback: list[str] = []

            for iteration in range(1, self.config.max_iterations + 1):
                self.status_manager.log(
                    LogLevel.INFO,
                    f"Starting iteration {iteration}/{self.config.max_iterations}",
                )

                # Paths for this iteration
                blend_file = self.config.output_dir / f"animation_v{iteration}.blend"
                frames_dir = self.config.output_dir / f"frames_v{iteration}"

                # Phase 3: Generate animation code with Claude
                await self.status_manager.set_phase(AnimationPhase.GENERATING_CODE)
                animation_code = await self._generate_animation_code(prompt, feedback)
                if not animation_code:
                    self.status_manager.log(LogLevel.WARN, "Using placeholder animation code")

                # Phase 4: Create animation in Blender
                await self.status_manager.set_phase(AnimationPhase.CREATING_ANIMATION)
                animation_result = create_animation(
                    prompt=prompt,
                    output_path=blend_file,
                    feedback=feedback if feedback else None,
                    animation_code=animation_code,
                    fps=self.config.fps,
                    duration=self.config.duration,
                )

                if not animation_result.success:
                    self.status_manager.log(
                        LogLevel.ERROR, f"Animation creation failed: {animation_result.message}"
                    )
                    continue  # Try again next iteration

                # Phase 5: Render frames
                await self.status_manager.set_phase(AnimationPhase.RENDERING_FRAMES)
                render_result = render_frames(
                    blend_file=blend_file,
                    output_dir=frames_dir,
                    resolution=self.config.render_resolution,
                    samples=self.config.render_samples,
                )

                if not render_result.success:
                    self.status_manager.log(
                        LogLevel.ERROR, f"Rendering failed: {render_result.message}"
                    )
                    continue  # Try again next iteration

                # Phase 6: Analyze with Gemini (authoritative verdict)
                await self.status_manager.set_phase(AnimationPhase.ANALYZING_QUALITY)
                analysis_result = analyze_animation(
                    frame_paths=render_result.frame_paths,
                    requirements=quality_requirements,
                    quality_threshold=self.config.quality_threshold,
                )

                # Record iteration
                await self.status_manager.record_iteration(
                    iteration_number=iteration,
                    quality_score=analysis_result.quality_score,
                    verdict=analysis_result.verdict,
                    issues=analysis_result.issues,
                    suggestions=analysis_result.suggestions,
                    blend_file=str(blend_file),
                    frames_dir=str(frames_dir),
                )

                # Check if done (Gemini's verdict is authoritative)
                if analysis_result.verdict == "done":
                    self.status_manager.log(
                        LogLevel.INFO,
                        f"Animation complete! Quality: {analysis_result.quality_score}/100",
                    )

                    # Set final result
                    await self.status_manager.set_final_result(
                        quality_score=analysis_result.quality_score,
                        blend_file=str(blend_file),
                        frames_dir=str(frames_dir),
                    )

                    # Phase 7: Export to Roblox format
                    await self.status_manager.set_phase(AnimationPhase.EXPORTING_ROBLOX)
                    roblox_path = await self._export_to_roblox(blend_file)
                    if roblox_path:
                        await self.status_manager.set_final_result(
                            quality_score=analysis_result.quality_score,
                            blend_file=str(blend_file),
                            frames_dir=str(frames_dir),
                            roblox_export=str(roblox_path),
                        )

                    # Success!
                    await self.status_manager.set_phase(AnimationPhase.COMPLETED)
                    await self.status_manager.notify_manager(
                        NotificationType.COMPLETED,
                        f"Animation complete for issue #{self.issue_number}. "
                        f"Quality: {analysis_result.quality_score}/100 after {iteration} iteration(s).",
                        requires_response=False,
                        metadata={
                            "iterations": iteration,
                            "quality_score": analysis_result.quality_score,
                            "blend_file": str(blend_file),
                            "roblox_export": str(roblox_path) if roblox_path else None,
                        },
                    )
                    return True

                # Prepare feedback for next iteration
                await self.status_manager.set_phase(AnimationPhase.IMPROVING_ANIMATION)
                feedback = analysis_result.suggestions
                self.status_manager.log(
                    LogLevel.INFO,
                    f"Gemini feedback: {len(analysis_result.issues)} issues, "
                    f"{len(analysis_result.suggestions)} suggestions",
                )

            # Max iterations reached
            await self.status_manager.set_phase(AnimationPhase.FAILED)
            await self.status_manager.notify_manager(
                NotificationType.FAILED,
                f"Animation failed after {self.config.max_iterations} iterations "
                f"without meeting quality threshold ({self.config.quality_threshold})",
                requires_response=True,
            )
            return False

        except Exception as e:
            if self.status_manager:
                self.status_manager.log(LogLevel.ERROR, f"Animation worker failed: {e}")
                await self.status_manager.notify_manager(
                    NotificationType.FAILED,
                    f"Animation worker crashed: {e}",
                    requires_response=True,
                )
            raise

    async def _get_animation_requirements(self) -> dict[str, str] | None:
        """Get animation requirements from GitHub issue."""
        if not self.status_manager:
            return None

        try:
            from github import Github

            github = Github(self.config.github_token)
            repo = github.get_repo(f"{self.config.repo_owner}/{self.config.repo_name}")
            issue = repo.get_issue(self.issue_number)

            # Parse issue body for animation requirements
            body = issue.body or ""

            # Default to issue title as prompt if no specific section found
            prompt = issue.title
            quality_requirements = "Smooth, natural animation suitable for Roblox game"

            # Look for specific sections in the issue body
            if "## Animation Description" in body or "## Prompt" in body:
                # Extract prompt from section
                lines = body.split("\n")
                in_prompt_section = False
                prompt_lines = []
                for line in lines:
                    if "## Animation Description" in line or "## Prompt" in line:
                        in_prompt_section = True
                        continue
                    if in_prompt_section:
                        if line.startswith("## "):
                            break
                        prompt_lines.append(line)
                if prompt_lines:
                    prompt = "\n".join(prompt_lines).strip()

            if "## Quality Requirements" in body:
                lines = body.split("\n")
                in_quality_section = False
                quality_lines = []
                for line in lines:
                    if "## Quality Requirements" in line:
                        in_quality_section = True
                        continue
                    if in_quality_section:
                        if line.startswith("## "):
                            break
                        quality_lines.append(line)
                if quality_lines:
                    quality_requirements = "\n".join(quality_lines).strip()

            return {
                "prompt": prompt,
                "quality_requirements": quality_requirements,
            }

        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to get issue: {e}")
            return None

    async def _generate_animation_code(
        self, prompt: str, feedback: list[str]
    ) -> str | None:
        """Use Claude to generate Blender animation code."""
        if not self.status_manager:
            return None

        feedback_text = "\n".join(f"- {f}" for f in feedback) if feedback else "None"

        claude_prompt = f"""Generate Blender Python code to create this animation:

## Animation Request
{prompt}

## Previous Feedback (if any)
{feedback_text}

## Requirements
- Use Blender's Python API (bpy)
- Animation should be {self.config.duration} seconds at {self.config.fps} fps
- Total frames: {int(self.config.fps * self.config.duration)}
- Create smooth, appealing movement suitable for Roblox
- Use keyframe animation
- Include proper lighting and camera setup
- Output ONLY the Python code, no explanations

## Code Structure
The code will be inserted into a template that:
- Clears the scene
- Sets up fps and frame range
- Saves the .blend file

Your code should:
1. Create the objects/armature needed
2. Set up animation keyframes
3. Add lighting
4. Position camera

Output only valid Python code that uses bpy."""

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],  # Read-only for code generation
            permission_mode="acceptEdits",
            max_turns=10,
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(claude_prompt)

                code_text = ""
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                code_text += block.text

                    if isinstance(message, ResultMessage) and message.is_error:
                        self.status_manager.log(
                            LogLevel.ERROR, f"Claude failed to generate code: {message.result}"
                        )
                        return None

                # Extract Python code from response
                if "```python" in code_text:
                    # Extract code block
                    start = code_text.find("```python") + 9
                    end = code_text.find("```", start)
                    if end > start:
                        return code_text[start:end].strip()

                # If no code block markers, return as-is if it looks like Python
                if "import bpy" in code_text or "bpy." in code_text:
                    return code_text.strip()

                self.status_manager.log(LogLevel.WARN, "Could not extract Python code from response")
                return None

        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Claude SDK error: {e}")
            return None

    async def _export_to_roblox(self, blend_file: Path) -> Path | None:
        """Export animation to Roblox format using anim2rbx."""
        if not self.status_manager:
            return None

        import subprocess

        fbx_file = blend_file.with_suffix(".fbx")
        rbx_file = blend_file.with_suffix(".rbxmx")

        try:
            # First export to FBX from Blender
            export_script = f'''
import bpy
bpy.ops.export_scene.fbx(
    filepath="{fbx_file}",
    use_selection=False,
    bake_anim=True,
    add_leaf_bones=False,
)
print("Exported to FBX: {fbx_file}")
'''
            result = subprocess.run(
                ["blender", "--background", str(blend_file), "--python-expr", export_script],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if not fbx_file.exists():
                self.status_manager.log(LogLevel.WARN, "FBX export failed, skipping Roblox export")
                return None

            # Then convert FBX to Roblox using anim2rbx
            # Note: anim2rbx needs DYLD_LIBRARY_PATH for assimp
            import os

            env = os.environ.copy()
            env["DYLD_LIBRARY_PATH"] = "/usr/local/opt/assimp@5/lib"

            result = subprocess.run(
                ["anim2rbx", str(fbx_file), str(rbx_file)],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )

            if rbx_file.exists():
                self.status_manager.log(LogLevel.INFO, f"Exported to Roblox: {rbx_file}")
                return rbx_file
            else:
                self.status_manager.log(
                    LogLevel.WARN, f"anim2rbx failed: {result.stderr or result.stdout}"
                )
                return None

        except Exception as e:
            self.status_manager.log(LogLevel.WARN, f"Roblox export failed: {e}")
            return None
