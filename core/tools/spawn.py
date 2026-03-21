"""Spawn tool for creating subagents."""

from typing import Any
from pathlib import Path
from core.tools.base import Tool


class SpawnTool(Tool):
    """
    Tool for spawning subagents.

    Creates independent subagent processes for parallel execution.
    Subagents have restricted tool sets and limited iterations.
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace

    @property
    def name(self) -> str:
        return "spawn"

    @property
    def description(self) -> str:
        return (
            "Create a subagent for parallel task execution. "
            "Subagents have restricted tool sets and cannot create further subagents."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Task prompt/instructions for the subagent"
                },
                "tool_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tools the subagent can use (cannot include spawn or message)"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Maximum iterations for the subagent (default: 15)",
                    "default": 15
                }
            },
            "required": ["prompt", "tool_names"]
        }

    async def execute(self, prompt: str, tool_names: list[str], max_iterations: int = 15, **kwargs) -> str:
        try:
            import asyncio
            from core.agent.subagent import SubagentManager
            from core.tools.registry import ToolRegistry

            # Validate tool_names - exclude spawn and message
            forbidden_tools = ["spawn", "message"]
            for tool_name in tool_names:
                if tool_name in forbidden_tools:
                    return f"Error: Subagents cannot use the '{tool_name}' tool"

            # Get data directory
            data_dir = self.workspace / "data"

            # Create subagent manager
            manager = SubagentManager(data_dir=data_dir)

            # Create task
            task = await manager.create_task(
                prompt=prompt,
                tool_names=tool_names,
                task_config={"max_iterations": max_iterations}
            )

            # Execute task
            tool_registry = ToolRegistry()
            await manager.execute_task(task, tool_registry)

            # Wait for task completion
            max_wait = 30  # seconds
            waited = 0
            interval = 0.5

            while waited < max_wait:
                await asyncio.sleep(interval)
                waited += interval

                task = await manager.get_task(task.id)
                if task.status in ["completed", "failed", "cancelled"]:
                    break

            # Return result
            if task.status == "completed":
                return f"""Subagent task completed:
- Task ID: {task.id}
- Result: {task.result}
- Tools used: {', '.join(tool_names)}"""
            elif task.status == "failed":
                return f"Subagent task failed: {task.error}"
            elif task.status == "cancelled":
                return f"Subagent task cancelled: {task.id}"
            else:
                return f"Subagent task timed out: {task.id} (status: {task.status})"

        except ImportError:
            return "Error: Subagent manager not available"
        except Exception as e:
            return f"Error spawning subagent: {str(e)}"