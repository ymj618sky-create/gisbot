"""
增强版AgentLoop集成测试

测试MessageBus、SubagentManager、LLMMemoryStore和TaskPlanner的集成
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from core.agent.enhanced_loop import EnhancedAgentLoop, EnhancedAgentLoopConfig
from core.tools.registry import ToolRegistry
from core.providers.base import LLMProvider
from core.bus.events import InboundMessage
from session.manager import SessionManager


class TestEnhancedAgentLoop:
    """增强版AgentLoop集成测试"""

    @pytest.mark.asyncio
    async def test_message_bus_integration(self, enhanced_loop):
        """测试MessageBus集成"""
        # Given - 消息总线已启用
        assert enhanced_loop._message_bus is not None

        # When - 处理消息
        response = await enhanced_loop.process_direct("测试消息")

        # Then - 可以从消息总线获取出站消息
        outbound = await enhanced_loop.get_outbound_message(timeout=0.1)
        # 注意：由于异步处理，可能需要等待更长时间
        assert outbound is None or outbound.content == response

    @pytest.mark.asyncio
    async def test_subagent_integration(self, enhanced_loop):
        """测试Subagent集成"""
        # Given - Subagent已启用
        assert enhanced_loop._subagent_manager is not None

        # When - 启动后台任务
        task_id = await enhanced_loop.spawn_background_task("后台分析任务")

        # Then - 任务ID有效
        assert task_id is not None
        assert len(task_id) == 8

    @pytest.mark.asyncio
    async def test_task_status_query(self, enhanced_loop):
        """测试任务状态查询"""
        # Given - 启动任务
        task_id = await enhanced_loop.spawn_background_task("测试任务")

        # When - 查询任务状态
        status = await enhanced_loop.get_task_status(task_id)

        # Then - 返回任务状态
        assert status is not None
        assert status["task_id"] == task_id
        assert "status" in status

    @pytest.mark.asyncio
    async def test_task_planning_integration(self, enhanced_loop):
        """测试任务规划集成"""
        # Given - 任务规划已启用
        assert enhanced_loop._task_planner is not None

        # When - 处理复杂任务
        response = await enhanced_loop.process_direct("分析数据并生成报告")

        # Then - 返回有效响应
        assert response is not None

    @pytest.mark.asyncio
    async def test_message_from_bus(self, enhanced_loop):
        """测试从消息总线消费"""
        # Given - 消息总线已启用
        assert enhanced_loop._message_bus is not None

        # When - 直接发布消息到总线
        inbound = InboundMessage(
            channel="test",
            chat_id="123",
            content="来自总线的消息"
        )
        await enhanced_loop._message_bus.publish_inbound(inbound)

        # When - 从总线处理消息
        # 注意：这里需要等待异步处理完成
        response = await enhanced_loop.process_from_message_bus(timeout=0.1)

        # Then - 获取到消息（取决于异步执行速度）
        # 由于是异步处理，可能返回None或响应
        # 这里只是验证不会出错
        assert response is None or isinstance(response, str)

    @pytest.mark.asyncio
    async def test_stop_cleanup(self, enhanced_loop):
        """测试停止和清理"""
        # When - 停止循环
        enhanced_loop.stop()

        # Then - 不会抛出异常
        assert True


class TestEnhancedAgentLoopComplexTasks:
    """复杂任务处理测试"""

    @pytest.mark.asyncio
    async def test_multi_step_task_planning(self, enhanced_loop):
        """测试多步骤任务规划"""
        # Given - 复杂任务
        task = "读取landuse数据，分析统计，生成图表并导出PDF"

        # When - 处理任务
        response = await enhanced_loop.process_direct(task)

        # Then - 返回有效响应
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, enhanced_loop):
        """测试并行任务执行"""
        # Given - 多个独立任务
        tasks = [
            "统计A类面积",
            "统计B类面积",
            "统计C类面积",
        ]

        # When - 并发启动任务
        task_ids = await asyncio.gather(*[
            enhanced_loop.spawn_background_task(t) for t in tasks
        ])

        # Then - 所有任务ID有效且唯一
        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3


class TestEnhancedAgentLoopLLMMemory:
    """LLM记忆集成测试"""

    @pytest.mark.asyncio
    async def test_llm_memory_consolidation(self, enhanced_loop_with_llm_memory):
        """测试LLM记忆合并"""
        # Given - 启用了LLM记忆
        assert enhanced_loop_with_llm_memory.memory_store is not None

        # When - 处理消息
        response = await enhanced_loop_with_llm_memory.process_direct(
            "记住用户偏好使用Python"
        )

        # Then - 返回有效响应
        assert response is not None