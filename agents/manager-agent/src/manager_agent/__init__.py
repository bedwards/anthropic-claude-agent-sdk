"""Manager agent for orchestrating worker agents."""

from .manager import Manager
from .models import IssueInfo, ManagerConfig, WorkerInfo

__all__ = ["Manager", "ManagerConfig", "WorkerInfo", "IssueInfo"]
