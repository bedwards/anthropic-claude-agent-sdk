# Worker Shared Library

Shared components for Claude worker agents.

## Components

- **base_models.py**: Common Pydantic models (LogLevel, LogEntry, NotificationType, BaseWorkerConfig, BaseWorkerStatus)
- **base_status.py**: Generic status management and logging
- **git_ops.py**: Git operations including worktrees for agent isolation
- **github_ops.py**: GitHub API operations (PRs, reviews, CI checks)

## Usage

```python
from worker_shared import (
    BaseWorkerConfig,
    BaseStatusManager,
    GitOperations,
    GitHubOperations,
    LogLevel,
)
```

## Extending for Specific Workers

Each worker type (PR worker, animation worker) extends these base classes with their own:
- Config class extending BaseWorkerConfig
- Status class extending BaseWorkerStatus
- Phase enum specific to their workflow
- Agent class with workflow logic
