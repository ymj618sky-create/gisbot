"""
pytest fixtures for integration tests
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from core.agent.enhanced_loop import EnhancedAgentLoop, EnhancedAgentLoopConfig
from core.tools.registry import ToolRegistry
from core.providers.base import LLMProvider
from session.manager import SessionManager


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_provider():
    """创建模拟的LLM提供商"""
    provider = MagicMock(spec=LLMProvider)
    provider.chat = AsyncMock(return_value={
        "content": "测试响应",
        "role": "assistant"
    })
    return provider


@pytest.fixture
def tool_registry():
    """创建工具注册表"""
    registry = ToolRegistry()
    return registry


@pytest.fixture
def session_manager(temp_workspace):
    """创建会话管理器"""
    manager = SessionManager(temp_workspace / "workspace" / "data" / "sessions")
    return manager


@pytest.fixture
def enhanced_loop(temp_workspace, mock_provider, tool_registry, session_manager):
    """创建增强版AgentLoop"""
    config = EnhancedAgentLoopConfig(
        enable_message_bus=True,
        enable_subagent=True,
        enable_task_planning=True,
        max_iterations=5,
        memory_window=10,
    )

    loop = EnhancedAgentLoop(
        workspace=temp_workspace,
        provider=mock_provider,
        tool_registry=tool_registry,
        session_manager=session_manager,
        config=config,
    )

    yield loop

    # 清理
    loop.stop()


@pytest.fixture
def enhanced_loop_with_llm_memory(temp_workspace, mock_provider, tool_registry, session_manager):
    """创建带LLM记忆的增强版AgentLoop"""
    config = EnhancedAgentLoopConfig(
        enable_message_bus=True,
        enable_subagent=True,
        enable_llm_memory=True,
        enable_task_planning=True,
        max_iterations=5,
        memory_window=10,
    )

    loop = EnhancedAgentLoop(
        workspace=temp_workspace,
        provider=mock_provider,
        tool_registry=tool_registry,
        session_manager=session_manager,
        config=config,
    )

    yield loop

    # 清理
    loop.stop()
