"""
增强版AgentLoop，集成自主执行能力

集成：
- MessageBus: 消息总线架构
- SubagentManager: 子Agent并行执行
- LLMMemoryStore: LLM驱动的智能记忆
- TaskPlanner: 任务规划
"""
import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from core.agent.context import ContextBuilder
from core.agent.memory import MemoryStore
from core.agent.llm_memory import LLMMemoryStore
from core.agent.skills import SkillsLoader
from core.agent.subagent import SubagentManager
from core.tools.registry import ToolRegistry
from core.providers.base import LLMProvider
from core.bus.events import InboundMessage, OutboundMessage
from core.bus.queue import MessageBus
from session.manager import SessionManager

# 导入基础的AgentLoop作为基类
from core.agent.loop import AgentLoop, AgentLoopConfig, _TOOL_RESULT_MAX_CHARS, _MAX_CONSECUTIVE_SAME_TOOL

logger = logging.getLogger(__name__)


@dataclass
class EnhancedAgentLoopConfig(AgentLoopConfig):
    """增强版AgentLoop配置"""

    # 自主执行相关配置
    enable_message_bus: bool = False
    enable_subagent: bool = False
    enable_llm_memory: bool = False
    enable_task_planning: bool = False

    # Subagent配置
    subagent_timeout: float = 30.0

    # MessageBus配置
    message_bus_timeout: float = 5.0


class EnhancedAgentLoop(AgentLoop):
    """
    增强版AgentLoop，集成自主执行能力

    支持以下功能：
    - MessageBus消息总线架构
    - Subagent并行任务执行
    - LLM驱动的智能记忆合并
    - 自动任务规划
    """

    def __init__(
        self,
        workspace: Path,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        session_manager: SessionManager,
        config: Optional[EnhancedAgentLoopConfig] = None,
        context_builder: Optional[ContextBuilder] = None,
        skills_loader: Optional[SkillsLoader] = None,
        memory_store: Optional[MemoryStore] = None,
        max_iterations: int = 15,
        memory_window: int = 50,
    ):
        # 初始化基类
        super().__init__(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager,
            config=config,
            context_builder=context_builder,
            skills_loader=skills_loader,
            memory_store=memory_store,
            max_iterations=max_iterations,
            memory_window=memory_window,
        )

        # 应用增强配置
        if config is not None:
            self._config = config
        else:
            self._config = EnhancedAgentLoopConfig(
                max_iterations=max_iterations,
                memory_window=memory_window,
            )

        # 初始化增强组件
        self._message_bus: Optional[MessageBus] = None
        self._subagent_manager: Optional[SubagentManager] = None
        self._task_planner: Optional[Any] = None

        # 根据配置初始化组件
        if self._config.enable_message_bus:
            self._message_bus = MessageBus()
            logger.info("MessageBus enabled")

        if self._config.enable_subagent:
            self._subagent_manager = SubagentManager(
                timeout=self._config.subagent_timeout
            )
            logger.info("SubagentManager enabled")

        if self._config.enable_llm_memory:
            # 使用LLM驱动的记忆存储替换基础记忆存储
            from core.agent.llm_memory import LLMMemoryStore
            self.memory_store = LLMMemoryStore(workspace, provider)
            self.context_builder = ContextBuilder(
                workspace, memory_store=self.memory_store
            )
            logger.info("LLMMemoryStore enabled")

        if self._config.enable_task_planning:
            from skills.autonomous.task_planning import TaskPlanner
            self._task_planner = TaskPlanner(
                available_tools=[t.name for t in tool_registry._tools.values()]
            )
            logger.info("TaskPlanner enabled")

    async def process_direct(
        self,
        content: str,
        channel: str = "cli",
        chat_id: str = "direct",
        media: Optional[list[str]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        处理直接消息，增强版本支持自主执行

        Args:
            content: 用户消息内容
            channel: 通道名称
            chat_id: 聊天ID
            media: 可选媒体文件列表
            on_progress: 可选进度回调

        Returns:
            Agent响应
        """
        # 如果启用了MessageBus，先发布到消息总线
        if self._message_bus:
            inbound = InboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=content,
            )
            await self._message_bus.publish_inbound(inbound)

        # 如果启用了任务规划，先分析任务
        if self._config.enable_task_planning and self._task_planner:
            plan = self._task_planner.plan(content)
            if on_progress:
                on_progress(f"任务规划完成: {plan['summary']}")

            # 对于复杂任务，考虑使用subagent执行
            if self._config.enable_subagent and len(plan["steps"]) > 1:
                return await self._execute_complex_task(
                    plan, channel, chat_id, on_progress
                )

        # 调用基类处理
        response = await super().process_direct(
            content=content,
            channel=channel,
            chat_id=chat_id,
            media=media,
            on_progress=on_progress,
        )

        # 如果启用了MessageBus，发布出站消息
        if self._message_bus and response:
            outbound = OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=response,
            )
            await self._message_bus.publish_outbound(outbound)

        return response

    async def _execute_complex_task(
        self,
        plan: dict[str, Any],
        channel: str,
        chat_id: str,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        执行复杂任务，使用subagent并行处理

        Args:
            plan: 任务计划
            channel: 通道名称
            chat_id: 聊天ID
            on_progress: 可选进度回调

        Returns:
            执行结果
        """
        if not self._subagent_manager:
            return await super().process_direct(
                content=plan["summary"],
                channel=channel,
                chat_id=chat_id,
                on_progress=on_progress,
            )

        # 将步骤转换为subagent任务
        task_ids = []
        results = {}

        # 按依赖关系分组可并行执行的步骤
        executable_steps = self._get_executable_steps(plan["steps"], results)

        for step in executable_steps:
            task_id = await self._subagent_manager.spawn(
                f"执行步骤: {step['description']}"
            )
            task_ids.append(task_id)

        if on_progress:
            on_progress(f"启动了 {len(task_ids)} 个并行任务")

        # 等待所有任务完成
        for task_id in task_ids:
            task = await self._subagent_manager.get_task(task_id)
            if task and task.result:
                results[task_id] = task.result

        # 生成最终响应
        summary = self._generate_execution_summary(plan, results)

        return summary

    def _get_executable_steps(
        self,
        steps: list[dict[str, Any]],
        results: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        获取当前可执行的步骤（无未完成的依赖）

        Args:
            steps: 所有步骤
            results: 已完成的结果

        Returns:
            可执行的步骤列表
        """
        executable = []

        for step in steps:
            # 检查依赖是否都已满足
            dependencies = step.get("depends_on", [])
            all_deps_satisfied = True

            for dep in dependencies:
                # 检查依赖步骤是否已完成
                dep_found = False
                for result_step_id in results:
                    dep_found = True
                    break
                if not dep_found:
                    all_deps_satisfied = False
                    break

            if all_deps_satisfied and step["id"] not in results:
                executable.append(step)

        return executable

    def _generate_execution_summary(
        self,
        plan: dict[str, Any],
        results: dict[str, Any],
    ) -> str:
        """
        生成执行摘要

        Args:
            plan: 任务计划
            results: 执行结果

        Returns:
            摘要文本
        """
        summary_parts = [
            f"# 任务执行完成\n\n",
            f"**任务**: {plan['summary']}\n\n",
            f"**步骤**: {len(plan['steps'])}\n\n",
            f"**耗时**: {plan.get('estimated_duration', '未知')}\n\n",
            f"## 执行结果\n\n",
        ]

        for step in plan["steps"]:
            status = "✓ 完成" if step["id"] in results else "✗ 未完成"
            summary_parts.append(f"- [{status}] {step['description']}\n")

        if plan.get("risks"):
            summary_parts.append(f"\n## 风险\n\n")
            for risk in plan["risks"]:
                summary_parts.append(f"- {risk}\n")

        if plan.get("success_criteria"):
            summary_parts.append(f"\n## 成功标准\n\n")
            for criterion in plan["success_criteria"]:
                summary_parts.append(f"- {criterion}\n")

        return "".join(summary_parts)

    async def process_from_message_bus(
        self,
        timeout: float = 5.0,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> Optional[str]:
        """
        从MessageBus消费消息并处理

        Args:
            timeout: 超时时间
            on_progress: 可选进度回调

        Returns:
            处理结果，超时返回None
        """
        if not self._message_bus:
            return None

        # 消费入站消息
        inbound = await self._message_bus.consume_inbound(timeout=timeout)
        if not inbound:
            return None

        # 处理消息
        return await self.process_direct(
            content=inbound.content,
            channel=inbound.channel,
            chat_id=inbound.chat_id,
            on_progress=on_progress,
        )

    async def get_outbound_message(
        self,
        timeout: float = 5.0,
    ) -> Optional[OutboundMessage]:
        """
        获取出站消息

        Args:
            timeout: 超时时间

        Returns:
            出站消息，超时返回None
        """
        if not self._message_bus:
            return None

        return await self._message_bus.consume_outbound(timeout=timeout)

    async def spawn_background_task(
        self,
        prompt: str,
    ) -> Optional[str]:
        """
        启动后台任务

        Args:
            prompt: 任务描述

        Returns:
            任务ID，失败返回None
        """
        if not self._subagent_manager:
            return None

        return await self._subagent_manager.spawn(prompt)

    async def get_task_status(
        self,
        task_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典，不存在返回None
        """
        if not self._subagent_manager:
            return None

        task = await self._subagent_manager.get_task(task_id)
        if task:
            return {
                "task_id": task.task_id,
                "prompt": task.prompt,
                "status": task.status.value,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
        return None

    def stop(self) -> None:
        """停止AgentLoop并清理资源"""
        super().stop()

        # 清理subagent
        if self._subagent_manager:
            # 记录需要清理，但不在这里同步等待
            logger.info("SubagentManager cleanup scheduled")

        # 清理message bus
        if self._message_bus:
            # 记录需要清理，但不在这里同步等待
            logger.info("MessageBus cleanup scheduled")

        logger.info("EnhancedAgentLoop stopped")