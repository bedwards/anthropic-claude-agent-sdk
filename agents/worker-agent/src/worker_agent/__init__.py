"""
Worker Agent - Autonomous PR lifecycle management using Claude Agent SDK

This agent handles the full PR lifecycle:
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

__version__ = "0.1.0"
