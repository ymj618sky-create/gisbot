"""Shared status constants for the nanobot framework."""

from enum import Enum


class TaskStatus(str, Enum):
    """Status of a subagent task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionStatus(str, Enum):
    """Status of a session."""
    ACTIVE = "active"
    ARCHIVED = "archived"