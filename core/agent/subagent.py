"""Subagent Manager for parallel task execution."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List

from core.agent.loop import AgentLoop
from core.tools.registry import ToolRegistry
from core.constants import TaskStatus
from core.utils.json_io import read_json_file, write_json_file


class SubagentTask:
    """Represents a subagent task."""

    def __init__(
        self,
        task_id: str,
        prompt: str,
        tool_names: List[str],
        status: TaskStatus | str = TaskStatus.PENDING,
        result: Optional[str] = None,
        error: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.id = task_id
        self.prompt = prompt
        self.tool_names = tool_names
        # Convert string to enum if needed
        if isinstance(status, str):
            status = TaskStatus(status)
        self.status = status
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "tool_names": self.tool_names,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubagentTask":
        """Create task from dictionary."""
        # Handle legacy string status or new enum value
        status_value = data.get("status", "pending")
        if isinstance(status_value, str):
            try:
                status = TaskStatus(status_value)
            except ValueError:
                status = TaskStatus.PENDING
        else:
            status = TaskStatus.PENDING

        return cls(
            task_id=data["id"],
            prompt=data["prompt"],
            tool_names=data.get("tool_names", []),
            status=status,
            result=data.get("result"),
            error=data.get("error"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class SubagentManager:
    """
    Manager for subagent tasks.

    Subagents are independent agent instances that can execute tasks
    in parallel. They have restricted tool sets (no spawn, no message)
    and limited iterations.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "subagent_tasks"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._running_tasks: dict[str, asyncio.Task] = {}

    def _get_task_path(self, task_id: str) -> Path:
        """Get file path for a task."""
        return self.data_dir / f"{task_id}.json"

    async def create_task(
        self,
        task_id: Optional[str] = None,
        prompt: str = "",
        tool_names: Optional[List[str]] = None,
        task_config: Optional[dict[str, Any]] = None
    ) -> SubagentTask:
        """
        Create a new subagent task.

        Args:
            task_id: Optional custom task ID
            prompt: Task prompt/instructions
            tool_names: List of tools this subagent can use
            task_config: Optional task configuration (max_iterations, etc.)

        Returns:
            SubagentTask instance
        """
        task_id = task_id or str(uuid.uuid4())
        tool_names = tool_names or []

        task = SubagentTask(
            task_id=task_id,
            prompt=prompt,
            tool_names=tool_names,
            status=TaskStatus.PENDING
        )

        # Save task
        await self._save_task(task)

        return task

    async def execute_task(
        self,
        task: SubagentTask,
        tool_registry: ToolRegistry,
        agent_loop: Optional[AgentLoop] = None,
        task_config: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Execute a subagent task asynchronously.

        Args:
            task: SubagentTask to execute
            tool_registry: Tool registry with available tools
            agent_loop: Optional AgentLoop instance
            task_config: Optional task configuration
        """
        # Update status
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.now().isoformat()
        await self._save_task(task)

        # Create async task
        async_task = asyncio.create_task(
            self._run_task(task, tool_registry, agent_loop, task_config)
        )
        self._running_tasks[task.id] = async_task

        # Don't wait for completion - let it run in background

    async def _run_task(
        self,
        task: SubagentTask,
        tool_registry: ToolRegistry,
        agent_loop: Optional[AgentLoop],
        task_config: Optional[dict[str, Any]]
    ) -> None:
        """
        Actually run the subagent task.

        This method runs in a separate task and updates the task status.
        """
        try:
            # Get task configuration
            config = task_config or {}
            max_iterations = config.get("max_iterations", 15)

            # Create a filtered tool registry with only allowed tools
            filtered_registry = ToolRegistry()
            for tool_name in task.tool_names:
                tool = tool_registry.get(tool_name)
                if tool:
                    filtered_registry.register(tool)

            # Execute the task
            # In a real implementation, this would create a new AgentLoop
            # with the filtered tool registry and execute the prompt
            # For now, simulate execution

            # Simulate task execution
            await asyncio.sleep(0.1)  # Simulate processing

            # Update task with result
            task.status = TaskStatus.COMPLETED
            task.result = f"Task '{task.prompt}' completed with tools: {', '.join(task.tool_names)}"
            task.updated_at = datetime.now().isoformat()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.updated_at = datetime.now().isoformat()

        finally:
            # Save task state
            await self._save_task(task)
            # Remove from running tasks
            self._running_tasks.pop(task.id, None)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running subagent task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        async_task = self._running_tasks.get(task_id)
        if async_task:
            async_task.cancel()
            task = await self.get_task(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
                task.updated_at = datetime.now().isoformat()
                await self._save_task(task)
            return True
        else:
            # Task not running, mark as cancelled anyway
            task = await self.get_task(task_id)
            if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.status = TaskStatus.CANCELLED
                task.updated_at = datetime.now().isoformat()
                await self._save_task(task)
                return True
        return False

    async def get_task(self, task_id: str) -> Optional[SubagentTask]:
        """Get a task by ID."""
        task_path = self._get_task_path(task_id)
        if not task_path.exists():
            return None

        try:
            data = read_json_file(task_path)
            return SubagentTask.from_dict(data)
        except (FileNotFoundError, OSError):
            return None

    async def list_tasks(self, status: Optional[str] = None) -> List[SubagentTask]:
        """List all tasks, optionally filtered by status."""
        tasks = []
        for task_file in self.data_dir.glob("*.json"):
            try:
                data = read_json_file(task_file)
                task = SubagentTask.from_dict(data)

                # Filter by status if specified (convert string to enum for comparison)
                if status is None:
                    tasks.append(task)
                else:
                    # Compare with TaskStatus enum or string value
                    task_status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
                    if task_status == status:
                        tasks.append(task)
            except (FileNotFoundError, OSError):
                continue

        # Sort by created_at (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks

    async def _save_task(self, task: SubagentTask) -> None:
        """Save task to disk."""
        task_path = self._get_task_path(task.id)
        write_json_file(task_path, task.to_dict())

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        task_path = self._get_task_path(task_id)
        if task_path.exists():
            task_path.unlink()
            return True
        return False

    async def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        Clean up tasks older than specified days.

        Args:
            days: Number of days before tasks are considered old

        Returns:
            Number of tasks cleaned up
        """
        from datetime import datetime as dt

        cutoff = dt.now().timestamp() - (days * 24 * 60 * 60)
        deleted = 0

        for task_file in self.data_dir.glob("*.json"):
            try:
                data = read_json_file(task_file)
                created_at = datetime.fromisoformat(data.get("created_at", "")).timestamp()

                if created_at < cutoff:
                    task_file.unlink()
                    deleted += 1
            except (FileNotFoundError, OSError, ValueError, KeyError):
                continue

        return deleted