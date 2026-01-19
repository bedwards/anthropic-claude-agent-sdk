"""
Main worker agent implementation using Claude Agent SDK.
Handles full PR lifecycle from issue to merge to main branch verification.
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock

from .git_manager import GitManager
from .github_manager import GitHubManager
from .models import (
    CIStatus,
    LogLevel,
    NotificationType,
    ReviewStatus,
    WorkerConfig,
    WorkerPhase,
)
from .status_manager import StatusManager


class WorkerAgent:
    """
    Autonomous worker agent that handles full PR lifecycle:
    1. Implement feature from GitHub issue
    2. Validate locally (lint, typecheck, test)
    3. Create PR
    4. Wait for Claude GitHub integration review
    5. Address blocking feedback, create issues for non-blocking
    6. Wait for CI
    7. Resolve merge conflicts
    8. Merge when green
    9. Verify main branch build succeeds post-merge
    10. Report to manager if main fails
    """

    def __init__(self, config: WorkerConfig, issue_number: int) -> None:
        self.config = config
        self.issue_number = issue_number

        # Managers will be initialized in run()
        self.status_manager: StatusManager | None = None
        self.git_manager: GitManager | None = None
        self.github_manager: GitHubManager | None = None

    async def run(self) -> bool:
        """
        Run the full worker agent lifecycle.
        Returns True if successful (PR merged and main green), False otherwise.
        """
        branch = f"worker/issue-{self.issue_number}"
        worktree_path = self.config.worktree_base_dir / f"issue-{self.issue_number}"

        # Initialize managers
        self.status_manager = StatusManager(
            self.config,
            self.issue_number,
            branch,
            str(worktree_path),
        )
        await self.status_manager.initialize()

        self.git_manager = GitManager(
            self.config.base_dir,
            self.config.worktree_base_dir,
            self.issue_number,
            self.status_manager,
        )

        self.github_manager = GitHubManager(self.config, self.status_manager)

        try:
            # Phase 1: Initialize worktree
            await self.status_manager.set_phase(WorkerPhase.INITIALIZING)
            await self.git_manager.initialize_worktree()

            # Phase 2: Implement the feature using Claude Agent SDK
            await self.status_manager.set_phase(WorkerPhase.IMPLEMENTING)
            success = await self._implement_feature()
            if not success:
                await self.status_manager.set_blocked("Failed to implement feature")
                return False

            # Phase 3: Validate (lint, typecheck, test)
            await self.status_manager.set_phase(WorkerPhase.VALIDATING)
            validation_passed = await self._validate()
            if not validation_passed:
                # Try to fix validation issues
                fixed = await self._fix_validation_issues()
                if not fixed:
                    await self.status_manager.set_blocked("Validation failed after retries")
                    return False

            # Phase 4: Create PR
            await self.status_manager.set_phase(WorkerPhase.CREATING_PR)
            pr_info = await self._create_pr()
            if not pr_info:
                await self.status_manager.set_blocked("Failed to create PR")
                return False

            pr_number = pr_info["number"]

            # Phase 5-8: Review/CI/Merge loop
            max_iterations = self.config.max_retries
            for iteration in range(max_iterations):
                self.status_manager.log(
                    LogLevel.INFO,
                    f"Review/merge iteration {iteration + 1}/{max_iterations}",
                )

                # Wait for Claude review
                await self.status_manager.set_phase(WorkerPhase.AWAITING_REVIEW)
                review = await self.github_manager.wait_for_claude_review(
                    pr_number,
                    self.config.review_timeout_seconds,
                )

                if review:
                    if review.state == "CHANGES_REQUESTED":
                        # Address blocking feedback
                        await self.status_manager.set_phase(WorkerPhase.ADDRESSING_FEEDBACK)
                        blocking_comments = [c for c in review.comments if c.is_blocking]
                        non_blocking_comments = [c for c in review.comments if not c.is_blocking]

                        # Create issues for non-blocking feedback
                        for comment in non_blocking_comments:
                            await self.github_manager.create_issue_from_feedback(
                                self.issue_number,
                                pr_number,
                                comment,
                            )

                        # Fix blocking issues
                        if blocking_comments:
                            fixed = await self._address_review_feedback(blocking_comments)
                            if not fixed:
                                continue  # Try again next iteration

                        # Push fixes
                        await self.git_manager.push()
                        continue  # Wait for new review

                    elif review.state == "APPROVED":
                        self.status_manager.log(LogLevel.INFO, "Review approved!")
                    # For COMMENTED state, proceed to CI check

                # Check CI
                await self.status_manager.set_phase(WorkerPhase.CHECKING_CI)
                ci_status = await self.github_manager.wait_for_ci(
                    pr_number,
                    self.config.ci_timeout_seconds,
                )

                if ci_status == CIStatus.FAILURE:
                    # Try to fix CI failures
                    fixed = await self._fix_ci_failures()
                    if fixed:
                        await self.git_manager.push()
                        continue
                    else:
                        await self.status_manager.set_blocked("CI failed after retries")
                        return False

                # Check for merge conflicts
                await self.status_manager.set_phase(WorkerPhase.RESOLVING_CONFLICTS)
                has_conflicts = await self.github_manager.has_merge_conflicts(pr_number)
                if has_conflicts:
                    rebased = await self.git_manager.rebase_on_main()
                    if rebased:
                        await self.git_manager.push()
                        continue  # Re-run CI after rebase
                    else:
                        await self.status_manager.set_blocked(
                            "Merge conflicts require manual resolution"
                        )
                        return False

                # All checks passed - merge!
                await self.status_manager.set_phase(WorkerPhase.MERGING)
                merged = await self.github_manager.merge_pr(pr_number)
                if not merged:
                    continue  # Try again

                # Phase 9: Verify main branch build
                await self.status_manager.set_phase(WorkerPhase.VERIFYING_MAIN)
                main_status = await self.github_manager.wait_for_main_branch_build(
                    self.config.main_build_timeout_seconds
                )

                if main_status == CIStatus.FAILURE:
                    # Main branch failed! Report to manager
                    await self.status_manager.set_main_branch_verified(False)
                    await self.status_manager.notify_manager(
                        NotificationType.MAIN_BRANCH_FAILED,
                        f"Main branch build failed after merging PR #{pr_number} for issue #{self.issue_number}",
                        requires_response=True,
                        metadata={
                            "pr_number": pr_number,
                            "issue_number": self.issue_number,
                        },
                    )
                    await self.status_manager.set_phase(WorkerPhase.FAILED)
                    return False

                # Success!
                await self.status_manager.set_main_branch_verified(True)
                await self.status_manager.set_phase(WorkerPhase.COMPLETED)
                await self.status_manager.notify_manager(
                    NotificationType.COMPLETED,
                    f"Successfully merged PR #{pr_number} for issue #{self.issue_number}. Main branch build verified.",
                    requires_response=False,
                )
                return True

            # Exhausted retries
            await self.status_manager.set_blocked("Exhausted retry attempts")
            return False

        except Exception as e:
            if self.status_manager:
                self.status_manager.log(LogLevel.ERROR, f"Worker agent failed: {e}")
                await self.status_manager.notify_manager(
                    NotificationType.FAILED,
                    f"Worker agent crashed: {e}",
                    requires_response=True,
                )
            raise
        finally:
            # Cleanup worktree on completion
            if self.git_manager and self.status_manager:
                status = self.status_manager.get_status()
                if status.phase in (WorkerPhase.COMPLETED, WorkerPhase.FAILED):
                    await self.git_manager.cleanup()

    async def _implement_feature(self) -> bool:
        """Use Claude Agent SDK to implement the feature."""
        if not self.github_manager or not self.git_manager or not self.status_manager:
            return False

        # Get issue details
        issue = await self.github_manager.get_issue(self.issue_number)
        worktree_path = self.git_manager.get_worktree_path()

        prompt = f"""You are implementing a feature for a GitHub issue.

## Issue #{self.issue_number}: {issue['title']}

{issue['body']}

## Instructions

1. Read the existing codebase to understand the structure and patterns
2. Implement the feature described in the issue
3. Write or update tests for the new functionality
4. Commit your changes frequently with descriptive messages
5. Do NOT modify lint, typecheck, or test configuration unless absolutely necessary
   - If you believe config changes are needed, explain why but do NOT make them
6. Follow existing code style and patterns

Work in the current directory. Make incremental progress and commit often."""

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            permission_mode="acceptEdits",
            cwd=str(worktree_path),
            max_turns=50,
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Log Claude's progress
                                text = block.text[:200] + "..." if len(block.text) > 200 else block.text
                                self.status_manager.log(LogLevel.DEBUG, f"Claude: {text}")

                    if isinstance(message, ResultMessage):
                        if message.is_error:
                            self.status_manager.log(
                                LogLevel.ERROR,
                                f"Claude failed: {message.result}",
                            )
                            return False

            # Commit any remaining changes
            await self.git_manager.commit(f"Implement feature for issue #{self.issue_number}")
            await self.git_manager.push()
            return True

        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Claude SDK error: {e}")
            return False

    async def _validate(self) -> bool:
        """Run validation (lint, typecheck, test)."""
        if not self.git_manager or not self.status_manager:
            return False

        worktree_path = self.git_manager.get_worktree_path()

        # Check what validation tools are available
        package_json = worktree_path / "package.json"
        pyproject = worktree_path / "pyproject.toml"

        commands: list[tuple[str, str]] = []

        if package_json.exists():
            # Node.js project
            commands = [
                ("lint", "npm run lint"),
                ("typecheck", "npm run typecheck"),
                ("test", "npm test -- --run"),
            ]
        elif pyproject.exists():
            # Python project
            commands = [
                ("lint", "uv run ruff check ."),
                ("typecheck", "uv run mypy ."),
                ("test", "uv run pytest"),
            ]

        all_passed = True
        for name, cmd in commands:
            self.status_manager.log(LogLevel.INFO, f"Running {name}...")
            try:
                import subprocess

                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode != 0:
                    self.status_manager.log(
                        LogLevel.WARN,
                        f"{name} failed: {result.stderr[:500]}",
                    )
                    all_passed = False
                else:
                    self.status_manager.log(LogLevel.INFO, f"{name} passed")
            except Exception as e:
                self.status_manager.log(LogLevel.ERROR, f"{name} error: {e}")
                all_passed = False

        return all_passed

    async def _fix_validation_issues(self) -> bool:
        """Use Claude to fix validation issues."""
        if not self.git_manager or not self.status_manager:
            return False

        worktree_path = self.git_manager.get_worktree_path()

        prompt = """Validation (lint/typecheck/test) failed. Please:

1. Read the error output from the validation commands
2. Fix the issues in the code
3. Do NOT modify lint, typecheck, or test configuration
4. Run the validation again to verify fixes

If you cannot fix the issues without config changes, explain why."""

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            permission_mode="acceptEdits",
            cwd=str(worktree_path),
            max_turns=20,
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                async for message in client.receive_response():
                    if isinstance(message, ResultMessage) and message.is_error:
                        return False

            await self.git_manager.commit("Fix validation issues")
            return await self._validate()  # Re-run validation
        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to fix validation: {e}")
            return False

    async def _create_pr(self) -> dict[str, int | str] | None:
        """Create a PR for the implementation."""
        if not self.github_manager or not self.git_manager:
            return None

        issue = await self.github_manager.get_issue(self.issue_number)

        return await self.github_manager.create_pr(
            branch=self.git_manager.get_branch(),
            issue_number=self.issue_number,
            title=issue["title"],
            body=f"Implementation for issue #{self.issue_number}\n\n{issue['body']}",
        )

    async def _address_review_feedback(self, comments: list) -> bool:
        """Use Claude to address review feedback."""
        if not self.git_manager or not self.status_manager:
            return False

        worktree_path = self.git_manager.get_worktree_path()

        feedback_text = "\n".join(
            f"- **{c.path}:{c.line}**: {c.body}" for c in comments
        )

        prompt = f"""The code review requested changes. Please address this feedback:

{feedback_text}

Fix the issues and commit your changes."""

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            permission_mode="acceptEdits",
            cwd=str(worktree_path),
            max_turns=20,
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                async for message in client.receive_response():
                    if isinstance(message, ResultMessage) and message.is_error:
                        return False

            await self.git_manager.commit("Address review feedback")
            return True
        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to address feedback: {e}")
            return False

    async def _fix_ci_failures(self) -> bool:
        """Use Claude to fix CI failures."""
        if not self.git_manager or not self.status_manager:
            return False

        worktree_path = self.git_manager.get_worktree_path()

        prompt = """CI checks failed. Please:

1. Check the GitHub Actions output (use gh CLI if needed)
2. Identify what failed
3. Fix the issues in the code
4. Do NOT modify CI configuration unless absolutely necessary

Commit your fixes."""

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            permission_mode="acceptEdits",
            cwd=str(worktree_path),
            max_turns=20,
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                async for message in client.receive_response():
                    if isinstance(message, ResultMessage) and message.is_error:
                        return False

            await self.git_manager.commit("Fix CI failures")
            return True
        except Exception as e:
            self.status_manager.log(LogLevel.ERROR, f"Failed to fix CI: {e}")
            return False
