"""Tests for Context Builder."""

import pytest
from pathlib import Path
from core.agent.context import ContextBuilder


def test_get_identity():
    """Test building core identity section"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    identity = builder._get_identity()
    assert "GIS AI Agent" in identity
    assert "Workspace" in identity


def test_build_runtime_context():
    """Test building runtime context"""
    runtime = ContextBuilder._build_runtime_context("web", "chat123")
    assert "Current Time:" in runtime
    assert "Channel: web" in runtime
    assert "Chat ID: chat123" in runtime


def test_build_runtime_context_without_channel():
    """Test building runtime context without channel"""
    runtime = ContextBuilder._build_runtime_context(None, None)
    assert "Current Time:" in runtime
    assert "Channel:" not in runtime


def test_build_messages_simple():
    """Test building simple messages without media"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    messages = builder.build_messages(
        history=[],
        current_message="Hello",
        channel="cli",
        chat_id="direct"
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_add_assistant_message():
    """Test adding assistant message"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    messages = [{"role": "user", "content": "Hello"}]
    messages = builder.add_assistant_message(messages, "Hi there!")
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"


def test_add_assistant_message_with_tool_calls():
    """Test adding assistant message with tool calls"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    messages = [{"role": "user", "content": "Hello"}]
    tool_calls = [
        {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test_tool", "arguments": "{}"}
        }
    ]
    messages = builder.add_assistant_message(messages, "Executing", tool_calls=tool_calls)
    assert len(messages) == 2
    assert "tool_calls" in messages[1]


def test_add_tool_result():
    """Test adding tool result"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    messages = []
    messages = builder.add_tool_result(messages, "call_123", "test_tool", "Tool result")
    assert len(messages) == 1
    assert messages[0]["role"] == "tool"
    assert messages[0]["tool_call_id"] == "call_123"


def test_build_messages_with_history():
    """Test building messages with conversation history"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"}
    ]
    messages = builder.build_messages(
        history=history,
        current_message="Second message",
        channel="web",
        chat_id="session1"
    )
    # System prompt + history (2 messages) + current message = 4 total
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "First message"
    assert messages[2]["role"] == "assistant"


def test_build_system_prompt():
    """Test building system prompt"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    system_prompt = builder.build_system_prompt()
    assert "GIS AI Agent" in system_prompt
    assert "Runtime" in system_prompt  # Without colon (actual header)


def test_build_system_prompt_with_skills():
    """Test building system prompt with specific skills"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    # This test verifies skills can be passed (even if empty)
    system_prompt = builder.build_system_prompt(skill_names=[])
    assert "GIS AI Agent" in system_prompt


def test_add_assistant_message_with_reasoning():
    """Test adding assistant message with reasoning content"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    messages = [{"role": "user", "content": "Hello"}]
    messages = builder.add_assistant_message(
        messages,
        "Response",
        reasoning_content="Thinking process..."
    )
    assert len(messages) == 2
    assert messages[1]["reasoning_content"] == "Thinking process..."


def test_add_assistant_message_with_thinking_blocks():
    """Test adding assistant message with thinking blocks"""
    workspace = Path("/tmp/test_workspace")
    builder = ContextBuilder(workspace)
    messages = [{"role": "user", "content": "Hello"}]
    thinking_blocks = [{"id": "block1", "type": "thinking", "content": "Thinking"}]
    messages = builder.add_assistant_message(
        messages,
        "Response",
        thinking_blocks=thinking_blocks
    )
    assert len(messages) == 2
    assert messages[1]["thinking_blocks"] == thinking_blocks