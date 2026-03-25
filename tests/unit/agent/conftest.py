"""
pytest fixtures for Agent tests
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from core.agent.llm_memory import LLMMemoryStore
from core.agent.subagent import SubagentManager


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_provider():
    """创建模拟的LLM提供商"""
    provider = MagicMock()
    provider.chat = AsyncMock(return_value={
        "content": "# 用户偏好\n- 使用Python进行GIS分析\n- 使用ArcPy进行高级空间分析"
    })
    return provider


@pytest.fixture
def llm_memory_store(temp_workspace, mock_provider):
    """创建LLMMemoryStore实例用于测试"""
    store = LLMMemoryStore(temp_workspace, mock_provider)
    yield store
    # 清理由temp_workspace处理


@pytest.fixture
def subagent_manager():
    """创建SubagentManager实例用于测试"""
    manager = SubagentManager()
    yield manager
    # 清理
    import asyncio
    asyncio.run(manager.shutdown())
