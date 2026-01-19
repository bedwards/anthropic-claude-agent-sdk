"""Manager agent for orchestrating worker agents."""

from .manager import Manager
from .models import ManagerConfig, WorkerInfo, IssueInfo

__all__ = ["Manager", "ManagerConfig", "WorkerInfo", "IssueInfo"]
