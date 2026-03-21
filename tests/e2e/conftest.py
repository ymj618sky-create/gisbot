"""
E2E Test Configuration and Fixtures

Provides shared fixtures for API end-to-end tests.
"""
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Mock the config module before importing routes
sys.modules['config'] = MagicMock(settings=MagicMock(
    ANTHROPIC_API_KEY='test-key',
    ANTHROPIC_MODEL=None,
    WORKSPACE_DIR=str(Path(__file__).parent.parent.parent / "test_workspace"),
    MAX_ITERATIONS=15,
    MEMORY_WINDOW=50
))

from api.routes.agent_nanobot import router
from core.agent.loop import AgentLoop
from core.agent.memory import MemoryStore
from core.agent.skills import SkillsLoader
from core.tools.registry import ToolRegistry
from core.tools.data.read import ReadDataTool
from core.tools.data.write import WriteDataTool
from core.tools.data.convert import ConvertDataTool
from core.tools.gis.proximity import BufferTool
from core.providers.base import LLMProvider
from session.manager import SessionManager


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)

    async def mock_chat(*args, **kwargs):
        return {
            "content": "Test response from mock LLM",
            "role": "assistant",
            "tool_calls": []
        }

    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """Create tool registry with core tools."""
    registry = ToolRegistry()
    registry.register(ReadDataTool())
    registry.register(WriteDataTool())
    registry.register(ConvertDataTool())
    registry.register(BufferTool())
    return registry


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    data_dir = workspace / "data"
    data_dir.mkdir(exist_ok=True)
    return workspace


@pytest.fixture
def session_manager(workspace: Path) -> SessionManager:
    """Create session manager with temporary data directory."""
    data_dir = workspace / "data"
    return SessionManager(data_dir=data_dir)


@pytest.fixture
def agent_loop(
    mock_provider: MagicMock,
    tool_registry: ToolRegistry,
    workspace: Path,
    session_manager: SessionManager
) -> AgentLoop:
    """Create AgentLoop instance for testing."""
    loop = AgentLoop(
        workspace=workspace,
        provider=mock_provider,
        tool_registry=tool_registry,
        session_manager=session_manager,
        max_iterations=5,
        memory_window=10
    )
    return loop


@pytest.fixture
def test_client(agent_loop: AgentLoop) -> TestClient:
    """
    Create FastAPI TestClient with mocked AgentLoop.

    This patches the global _agent_loop singleton in agent_nanobot module.
    """
    import api.routes.agent_nanobot as nanobot_routes

    def mock_get_agent_loop():
        return agent_loop

    with patch.object(
        nanobot_routes,
        'get_agent_loop',
        side_effect=mock_get_agent_loop
    ):
        # Import here to avoid issues with patch
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")
        client = TestClient(app)
        yield client

        # Reset global state
        nanobot_routes._agent_loop = None


@pytest.fixture
def chat_id() -> str:
    """Generate unique chat ID for tests."""
    import uuid
    return f"test-chat-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def channel() -> str:
    """Default channel name for tests."""
    return "test"


@pytest.fixture
def sample_chat_request(channel: str, chat_id: str) -> dict:
    """Sample chat request payload."""
    return {
        "message": "Hello, can you help me with GIS data?",
        "channel": channel,
        "chat_id": chat_id,
        "media": None
    }


class MockAsyncContext:
    """Helper for mocking async context managers."""
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def event_loop_policy() -> Generator:
    """Set event loop policy for async tests."""
    policy = asyncio.WindowsSelectorEventLoopPolicy() if sys.platform == 'win32' else asyncio.DefaultEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()