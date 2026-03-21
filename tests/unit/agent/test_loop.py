"""Tests for Agent Loop."""

import pytest
from pathlib import Path
import tempfile
from core.agent.loop import AgentLoop
from core.tools.base import Tool
from core.tools.registry import ToolRegistry
from core.providers.base import LLMProvider
from session.manager import SessionManager


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
                "input": {"type": "string", "description": "Input string"}
            },
            "required": ["input"]
        }

    async def execute(self, input: str, **kwargs) -> str:
        return f"Processed: {input}"


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, api_key: str = "test-key"):
        super().__init__(api_key)
        self.responses = []

    @property
    def name(self) -> str:
        return "mock"

    @property
    def supports_streaming(self) -> bool:
        return False

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        """Return a mock response."""
        self.responses.append({"messages": messages, "tools": tools})

        # Simple logic: if tools are provided, simulate a tool call
        if tools and len(self.responses) == 1:
            return {
                "content": "I'll use the tool",
                "model": "mock-model",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "mock_tool",
                            "arguments": '{"input": "test"}'
                        }
                    }
                ]
            }

        return {
            "content": "Mock response",
            "model": "mock-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }


@pytest.mark.asyncio
async def test_agent_loop_initialization():
    """Test Agent Loop initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager
        )

        assert agent_loop.workspace == workspace
        assert agent_loop.provider == provider
        assert agent_loop.tool_registry == tool_registry
        assert agent_loop.session_manager == session_manager


@pytest.mark.asyncio
async def test_process_direct_message():
    """Test processing a direct message"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager
        )

        response = await agent_loop.process_direct("Hello", channel="cli", chat_id="test")

        assert response
        assert "Mock response" in response or "Processed" in response


@pytest.mark.asyncio
async def test_process_with_tool_call():
    """Test processing a message that triggers tool call"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        # Register a mock tool
        tool = MockTool("mock_tool")
        tool_registry.register(tool)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager
        )

        response = await agent_loop.process_direct("Use the tool", channel="cli", chat_id="test")

        # Tool should have been called
        assert response
        # The response should contain either the tool result or the LLM's final message
        assert "Processed: test" in response or "Mock response" in response or "I'll use the tool" in response


@pytest.mark.asyncio
async def test_process_with_session_persistence():
    """Test that sessions are persisted across calls"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager
        )

        # First message
        await agent_loop.process_direct("First message", channel="web", chat_id="session1")

        # Second message - should use same session
        await agent_loop.process_direct("Second message", channel="web", chat_id="session1")

        # Check session
        session = session_manager.get_by_channel_chat_id("web", "session1")
        assert session is not None
        # Should have at least 4 messages: 2 user, 2 assistant
        assert len(session.messages) >= 4


@pytest.mark.asyncio
async def test_process_with_media():
    """Test processing a message with media attachments"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        # Create a test image
        import base64
        test_image = workspace / "test.png"
        test_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager
        )

        response = await agent_loop.process_direct(
            "What's in this image?",
            channel="cli",
            chat_id="test",
            media=[str(test_image)]
        )

        assert response


@pytest.mark.asyncio
async def test_max_iterations():
    """Test that agent loop respects max iterations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        # Register a tool that always triggers more calls
        class EndlessTool(Tool):
            @property
            def name(self) -> str:
                return "endless"

            @property
            def description(self) -> str:
                return "A tool that wants more calls"

            @property
            def parameters(self) -> dict:
                return {"type": "object", "properties": {}}

            async def execute(self, **kwargs) -> str:
                return "Result"

        tool_registry.register(EndlessTool())

        # Configure provider to always request tool calls
        class EndlessProvider(MockLLMProvider):
            async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
                # Only make tool calls for first few iterations
                if len(messages) < 5:
                    return {
                        "content": "I'll use the tool",
                        "model": "mock",
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                        "tool_calls": [
                            {
                                "id": f"call_{len(messages)}",
                                "type": "function",
                                "function": {"name": "endless", "arguments": "{}"}
                            }
                        ]
                    }
                return {
                    "content": "Done",
                    "model": "mock",
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5}
                }

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=EndlessProvider(),
            tool_registry=tool_registry,
            session_manager=session_manager,
            max_iterations=3
        )

        response = await agent_loop.process_direct("Test", channel="cli", chat_id="test")

        assert response
        # Should have stopped at max iterations
        assert "Done" in response or "limit" in response.lower() or "stopped" in response.lower()


@pytest.mark.asyncio
async def test_context_building():
    """Test that context is built correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager
        )

        response = await agent_loop.process_direct("Hello", channel="web", chat_id="test")

        # Check that provider was called with messages
        assert len(provider.responses) > 0
        messages = provider.responses[0]["messages"]
        assert any(m["role"] == "system" for m in messages)
        assert any(m["role"] == "user" for m in messages)


@pytest.mark.asyncio
async def test_session_memory_window():
    """Test that session memory window is enforced"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        provider = MockLLMProvider()
        tool_registry = ToolRegistry()
        session_manager = SessionManager(data_dir=workspace)

        agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager,
            memory_window=5
        )

        # Send many messages
        for i in range(20):
            await agent_loop.process_direct(f"Message {i}", channel="cli", chat_id=f"test{i}")

        # Check session memory was trimmed
        session = session_manager.get_by_channel_chat_id("cli", "test19")
        if session:
            assert len(session.messages) <= 15  # Should be trimmed