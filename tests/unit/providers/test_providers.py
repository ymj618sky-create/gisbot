"""Tests for LLM Providers."""

import pytest
from core.providers.base import LLMProvider
from core.providers.anthropic import AnthropicProvider
from core.providers.openai import OpenAIProvider


class MockLLMProvider(LLMProvider):
    """Mock provider for testing base class."""

    def __init__(self, api_key: str = "test-key"):
        super().__init__(api_key)

    @property
    def name(self) -> str:
        return "mock"

    @property
    def supports_streaming(self) -> bool:
        return False

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, **kwargs) -> dict:
        return {
            "content": "Mock response",
            "model": "mock-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }


def test_base_provider_name():
    """Test base provider has name property"""
    provider = MockLLMProvider()
    assert provider.name == "mock"


def test_base_provider_supports_streaming():
    """Test base provider has streaming support property"""
    provider = MockLLMProvider()
    assert provider.supports_streaming is False


@pytest.mark.asyncio
async def test_base_provider_chat():
    """Test base provider chat method"""
    provider = MockLLMProvider()
    messages = [{"role": "user", "content": "Hello"}]

    response = await provider.chat(messages)

    assert "content" in response
    assert response["content"] == "Mock response"
    assert "model" in response
    assert "usage" in response


def test_anthropic_provider_properties():
    """Test Anthropic provider has required properties"""
    provider = AnthropicProvider(api_key="test-key")
    assert provider.name == "anthropic"
    assert provider.supports_streaming is True


def test_openai_provider_properties():
    """Test OpenAI provider has required properties"""
    provider = OpenAIProvider(api_key="test-key")
    assert provider.name == "openai"
    assert provider.supports_streaming is True


@pytest.mark.asyncio
async def test_chat_with_empty_messages():
    """Test chat with empty messages"""
    provider = MockLLMProvider()
    response = await provider.chat([])
    assert "content" in response


@pytest.mark.asyncio
async def test_chat_with_tools():
    """Test chat with tools parameter"""
    provider = MockLLMProvider()
    messages = [{"role": "user", "content": "Test"}]
    tools = [{"type": "function", "function": {"name": "test_tool"}}]

    response = await provider.chat(messages, tools=tools)

    assert "content" in response


def test_anthropic_provider_default_model():
    """Test Anthropic provider uses default model"""
    provider = AnthropicProvider(api_key="test-key")
    assert provider.model == "claude-sonnet-4-20250514"  # Default model


def test_openai_provider_default_model():
    """Test OpenAI provider uses default model"""
    provider = OpenAIProvider(api_key="test-key")
    assert provider.model == "gpt-4o"  # Default model


def test_provider_custom_model():
    """Test provider accepts custom model"""
    provider = AnthropicProvider(api_key="test-key", model="claude-opus-4-20250514")
    assert provider.model == "claude-opus-4-20250514"


def test_anthropic_provider_requires_api_key():
    """Test Anthropic provider validates API key"""
    # Using empty string instead of None
    with pytest.raises(ValueError, match="requires an API key"):
        AnthropicProvider(api_key="")


def test_openai_provider_requires_api_key():
    """Test OpenAI provider validates API key"""
    with pytest.raises(ValueError, match="requires an API key"):
        OpenAIProvider(api_key="")