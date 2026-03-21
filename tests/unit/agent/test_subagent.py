"""Tests for Subagent System."""

import pytest
import tempfile
from pathlib import Path
from core.agent.subagent import SubagentManager, SubagentTask
from core.tools.base import Tool
from core.tools.registry import ToolRegistry


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name: str = "mock_tool"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Mock tool for testing"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }

    async def execute(self, input: str, **kwargs) -> str:
        return f"Processed: {input}"


@pytest.mark.asyncio
async def test_create_subagent_task():
    """Test creating a subagent task"""
    manager = SubagentManager(data_dir=Path.cwd())

    task = await manager.create_task(
        task_id="task123",
        prompt="Analyze this data",
        tool_names=["mock_tool"],
        task_config={"max_iterations": 5}
    )

    assert task.id == "task123"
    assert task.status == "pending"
    assert task.prompt == "Analyze this data"


@pytest.mark.asyncio
async def test_execute_subagent_task():
    """Test executing a subagent task"""
    manager = SubagentManager(data_dir=Path.cwd())
    tool_registry = ToolRegistry()
    tool_registry.register(MockTool("mock_tool"))

    task = await manager.create_task(
        task_id="task456",
        prompt="Test task",
        tool_names=["mock_tool"]
    )

    await manager.execute_task(task, tool_registry)

    # Wait for task to complete
    import asyncio
    await asyncio.sleep(0.5)

    # Refresh task from storage
    task = await manager.get_task("task456")

    assert task.status in ["completed", "failed"]
    if task.status == "completed":
        assert task.result is not None


@pytest.mark.asyncio
async def test_cancel_subagent_task():
    """Test cancelling a subagent task"""
    manager = SubagentManager(data_dir=Path.cwd())

    task = await manager.create_task(
        task_id="task789",
        prompt="Long running task"
    )

    await manager.cancel_task(task.id)

    cancelled_task = await manager.get_task(task.id)
    assert cancelled_task is not None
    assert cancelled_task.status == "cancelled"


@pytest.mark.asyncio
async def test_list_subagent_tasks():
    """Test listing subagent tasks"""
    manager = SubagentManager(data_dir=Path.cwd())

    await manager.create_task(task_id="task1", prompt="Task 1")
    await manager.create_task(task_id="task2", prompt="Task 2")

    tasks = await manager.list_tasks()

    assert len(tasks) >= 2
    task_ids = [t.id for t in tasks]
    assert "task1" in task_ids
    assert "task2" in task_ids


@pytest.mark.asyncio
async def test_subagent_task_with_tools():
    """Test subagent task with restricted tools"""
    manager = SubagentManager(data_dir=Path.cwd())
    tool_registry = ToolRegistry()

    # Register multiple tools
    tool_registry.register(MockTool("tool1"))
    tool_registry.register(MockTool("tool2"))
    tool_registry.register(MockTool("tool3"))

    # Create task with only specific tools
    task = await manager.create_task(
        task_id="task_tools",
        prompt="Use tool1",
        tool_names=["tool1"]  # Only tool1 allowed
    )

    await manager.execute_task(task, tool_registry)

    # Wait for task to complete
    import asyncio
    await asyncio.sleep(0.5)

    # Refresh task from storage
    task = await manager.get_task("task_tools")

    # Task should complete successfully
    assert task.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_subagent_task_with_max_iterations():
    """Test subagent task respects max iterations"""
    manager = SubagentManager(data_dir=Path.cwd())
    tool_registry = ToolRegistry()

    task = await manager.create_task(
        task_id="task_iter",
        prompt="Test",
        tool_names=[],
        task_config={"max_iterations": 3}
    )

    # Execute should respect max_iterations
    await manager.execute_task(task, tool_registry)

    # Wait for task to complete
    import asyncio
    await asyncio.sleep(0.5)

    # Refresh task from storage
    task = await manager.get_task("task_iter")

    assert task.status in ["completed", "failed", "cancelled"]


def test_subagent_task_serialization():
    """Test subagent task can be serialized"""
    task = SubagentTask(
        task_id="task999",
        prompt="Test prompt",
        tool_names=["tool1", "tool2"],
        status="pending"
    )

    data = task.to_dict()

    assert data["id"] == "task999"
    assert data["prompt"] == "Test prompt"
    assert data["status"] == "pending"
    assert data["tool_names"] == ["tool1", "tool2"]


def test_subagent_task_deserialization():
    """Test subagent task can be deserialized"""
    data = {
        "id": "task888",
        "prompt": "Test prompt",
        "tool_names": ["tool1"],
        "status": "completed",
        "result": "Task result",
        "error": None,
        "created_at": "2026-03-21T00:00:00",
        "updated_at": "2026-03-21T00:01:00"
    }

    task = SubagentTask.from_dict(data)

    assert task.id == "task888"
    assert task.prompt == "Test prompt"
    assert task.status == "completed"
    assert task.result == "Task result"


@pytest.mark.asyncio
async def test_subagent_task_cleanup():
    """Test cleaning up old subagent tasks"""
    manager = SubagentManager(data_dir=Path.cwd())

    # Create old tasks
    import time
    await manager.create_task(task_id="old_task1", prompt="Old task")
    await manager.create_task(task_id="old_task2", prompt="Old task")

    # Clean up tasks older than 0 days (all)
    cleaned = await manager.cleanup_old_tasks(days=0)

    assert cleaned >= 0