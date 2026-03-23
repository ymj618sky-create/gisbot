"""Workspace management for multi-project isolation."""

from .manager import (
    WorkspaceManager,
    Project,
    get_workspace_manager,
    init_workspace_manager
)
from .memory import (
    ProjectMemory,
    ProjectMemoryManager,
    ProjectFact,
    ProjectPreference,
    ProjectWorkflow,
    ProjectStats,
    get_memory_manager,
    init_memory_manager
)

__all__ = [
    "WorkspaceManager",
    "Project",
    "get_workspace_manager",
    "init_workspace_manager",
    "ProjectMemory",
    "ProjectMemoryManager",
    "ProjectFact",
    "ProjectPreference",
    "ProjectWorkflow",
    "ProjectStats",
    "get_memory_manager",
    "init_memory_manager"
]