"""
SubagentManager单元测试

测试子Agent管理器的核心功能：
- 子Agent创建和管理
- 后台任务执行
- 结果收集和通知
- 超时和取消
"""
import pytest
import asyncio
from datetime import datetime
from core.agent.subagent import SubagentManager, SubagentTask, TaskStatus


class TestSubagentTask:
    """SubagentTask数据模型测试"""

    def test_create_task(self):
        """测试创建任务"""
        task = SubagentTask(
            task_id="task-123",
            prompt="执行数据分析",
            created_at=datetime.now()
        )
        assert task.task_id == "task-123"
        assert task.prompt == "执行数据分析"
        assert task.status == TaskStatus.PENDING

    def test_task_with_result(self):
        """测试带结果的任务"""
        task = SubagentTask(
            task_id="task-123",
            prompt="执行数据分析",
            status=TaskStatus.COMPLETED,
            result="分析完成",
            created_at=datetime.now()
        )
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "分析完成"


class TestSubagentManager:
    """SubagentManager核心功能测试"""

    @pytest.mark.asyncio
    async def test_create_subagent_task(self, subagent_manager):
        """测试创建子Agent任务"""
        # Given - 任务描述
        prompt = "分析landuse数据"

        # When - 创建任务
        task_id = await subagent_manager.spawn(prompt)

        # Then - 任务ID有效
        assert task_id is not None
        assert len(task_id) == 8  # UUID前8位

    @pytest.mark.asyncio
    async def test_get_task_status(self, subagent_manager):
        """测试获取任务状态"""
        # Given - 创建任务
        prompt = "分析landuse数据"
        task_id = await subagent_manager.spawn(prompt)

        # When - 获取任务状态
        task = await subagent_manager.get_task(task_id)

        # Then - 返回任务对象
        assert task is not None
        assert task.task_id == task_id
        assert task.prompt == prompt

    @pytest.mark.asyncio
    async def test_task_status_transitions(self, subagent_manager):
        """测试任务状态转换"""
        # Given - 创建任务
        prompt = "分析landuse数据"
        task_id = await subagent_manager.spawn(prompt)

        # Then - 初始状态为PENDING
        task = await subagent_manager.get_task(task_id)
        assert task.status == TaskStatus.PENDING

        # 模拟任务执行中
        await subagent_manager._update_status(task_id, TaskStatus.RUNNING)
        task = await subagent_manager.get_task(task_id)
        assert task.status == TaskStatus.RUNNING

        # 模拟任务完成
        await subagent_manager._update_status(task_id, TaskStatus.COMPLETED, "完成")
        task = await subagent_manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "完成"

    @pytest.mark.asyncio
    async def test_multiple_concurrent_tasks(self, subagent_manager):
        """测试并发执行多个任务"""
        # Given - 多个任务
        prompts = [f"任务{i}" for i in range(5)]

        # When - 并发创建
        task_ids = await asyncio.gather(*[
            subagent_manager.spawn(p) for p in prompts
        ])

        # Then - 所有任务ID唯一
        assert len(set(task_ids)) == len(task_ids)
        assert len(task_ids) == 5

    @pytest.mark.asyncio
    async def test_cancel_task(self, subagent_manager):
        """测试取消任务"""
        # Given - 创建任务
        task_id = await subagent_manager.spawn("分析数据")

        # When - 取消任务
        await subagent_manager.cancel(task_id)

        # Then - 任务状态为CANCELLED
        task = await subagent_manager.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self, subagent_manager):
        """测试清理已完成任务"""
        # Given - 创建多个任务
        task_ids = []
        for i in range(3):
            tid = await subagent_manager.spawn(f"任务{i}")
            task_ids.append(tid)
            # 标记为完成
            await subagent_manager._update_status(tid, TaskStatus.COMPLETED, f"结果{i}")

        # When - 清理已完成任务
        await subagent_manager.cleanup_completed()

        # Then - 已完成任务被移除
        for tid in task_ids:
            task = await subagent_manager.get_task(tid)
            assert task is None

    @pytest.mark.asyncio
    async def test_get_all_tasks(self, subagent_manager):
        """测试获取所有任务"""
        # Given - 创建多个任务
        await subagent_manager.spawn("任务1")
        await subagent_manager.spawn("任务2")
        await subagent_manager.spawn("任务3")

        # When - 获取所有任务
        tasks = await subagent_manager.get_all_tasks()

        # Then - 返回所有任务
        assert len(tasks) == 3

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """测试任务超时"""
        # Given - 创建超时时间为0.1秒的管理器
        manager = SubagentManager(timeout=0.1)
        task_id = await manager.spawn("长时间任务")

        # When - 等待超时
        await asyncio.sleep(0.3)

        # Then - 任务状态为TIMEOUT
        task = await manager.get_task(task_id)
        assert task.status == TaskStatus.TIMEOUT

        # 清理
        await manager.shutdown()
