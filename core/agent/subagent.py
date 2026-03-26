"""
SubagentManager - 子Agent管理器

支持后台并行执行复杂任务，任务分解和结果收集
"""
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class SubagentTask:
    """子Agent任务"""
    task_id: str  # 任务ID（UUID前8位）
    prompt: str  # 任务描述
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None  # 执行结果
    error: Optional[str] = None  # 错误信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间


class SubagentManager:
    """
    子Agent管理器

    负责创建、管理和监控后台并行执行的子Agent任务
    支持任务超时、取消和清理
    """

    def __init__(self, timeout: float = 10.0):
        """
        初始化子Agent管理器

        Args:
            timeout: 默认任务超时时间（秒）
        """
        self._tasks: Dict[str, SubagentTask] = {}
        self._task_lock = asyncio.Lock()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._timeout = timeout
        self._shutdown_event = asyncio.Event()

    async def spawn(self, prompt: str) -> str:
        """
        创建并启动子Agent任务

        Args:
            prompt: 任务描述

        Returns:
            任务ID（UUID前8位）
        """
        task_id = str(uuid.uuid4())[:8]

        async with self._task_lock:
            task = SubagentTask(task_id=task_id, prompt=prompt)
            self._tasks[task_id] = task

        # 启动后台任务
        bg_task = asyncio.create_task(self._run_task(task_id))
        self._running_tasks[task_id] = bg_task

        return task_id

    async def get_task(self, task_id: str) -> Optional[SubagentTask]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            SubagentTask对象，不存在返回None
        """
        async with self._task_lock:
            return self._tasks.get(task_id)

    async def get_all_tasks(self) -> list[SubagentTask]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        async with self._task_lock:
            return list(self._tasks.values())

    async def cancel(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False

            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                return True

            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                return True

            return False

    async def cleanup_completed(self) -> int:
        """
        清理已完成的任务

        Returns:
            清理的任务数量
        """
        async with self._task_lock:
            completed_ids = [
                tid for tid, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                                  TaskStatus.CANCELLED, TaskStatus.TIMEOUT)
            ]
            for tid in completed_ids:
                self._tasks.pop(tid, None)
                self._running_tasks.pop(tid, None)

            return len(completed_ids)

    async def shutdown(self) -> None:
        """关闭管理器，取消所有运行中的任务"""
        self._shutdown_event.set()

        # 取消所有运行中的任务
        for task_id, bg_task in self._running_tasks.items():
            bg_task.cancel()
            await self._update_status(task_id, TaskStatus.CANCELLED)

        self._running_tasks.clear()
        self._tasks.clear()

    async def _run_task(self, task_id: str) -> None:
        """
        执行子Agent任务（后台运行）

        Args:
            task_id: 任务ID
        """
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if task is None:
                return

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

        try:
            # 模拟任务执行 - 实际场景会调用AgentLoop
            await asyncio.sleep(0.1)  # 模拟执行时间

            # 检查超时
            if task.started_at:
                elapsed = (datetime.now() - task.started_at).total_seconds()
                if elapsed > self._timeout:
                    await self._update_status(task_id, TaskStatus.TIMEOUT)
                    return

            # 检查是否被取消
            if self._shutdown_event.is_set():
                await self._update_status(task_id, TaskStatus.CANCELLED)
                return

            # 模拟任务成功
            result = f"任务完成: {self._tasks.get(task_id).prompt if task_id in self._tasks else ''}"
            await self._update_status(task_id, TaskStatus.COMPLETED, result)

        except asyncio.CancelledError:
            await self._update_status(task_id, TaskStatus.CANCELLED)
        except Exception as e:
            await self._update_status(task_id, TaskStatus.FAILED, error=str(e))

    async def _update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        更新任务状态（内部方法）

        Args:
            task_id: 任务ID
            status: 新状态
            result: 执行结果（可选）
            error: 错误信息（可选）
        """
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if task is None:
                return

            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error

            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                         TaskStatus.CANCELLED, TaskStatus.TIMEOUT):
                task.completed_at = datetime.now()
                self._running_tasks.pop(task_id, None)

    @property
    def task_count(self) -> int:
        """获取当前任务数量"""
        return len(self._tasks)

    @property
    def running_count(self) -> int:
        """获取运行中任务数量"""
        return len(self._running_tasks)