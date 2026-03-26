"""Tests for LLM Providers."""

import pytest
from core.providers.base import LLMProvider
from core.providers.anthropic import AnthropicProvider
from core.providers.openai import OpenAIProvider
from core.providers.dashscope import DashscopeProvider
from core.providers.factory import ProviderFactory, create_provider


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


def test_dashscope_provider_properties():
    """Test Dashscope provider has required properties"""
    provider = DashscopeProvider(api_key="test-key")
    assert provider.name == "dashscope"
    assert provider.supports_streaming is True


def test_dashscope_provider_default_model():
    """Test Dashscope provider uses default model"""
    provider = DashscopeProvider(api_key="test-key")
    assert provider.model == "qwen-coding-plus"


def test_dashscope_provider_requires_api_key():
    """Test Dashscope provider validates API key"""
    with pytest.raises(ValueError, match="requires an API key"):
        DashscopeProvider(api_key="")


# Provider Factory Tests
def test_factory_create_anthropic_provider():
    """Test factory creates Anthropic provider"""
    provider = ProviderFactory.get_provider("anthropic", api_key="test-key")
    assert isinstance(provider, AnthropicProvider)


def test_factory_create_openai_provider():
    """Test factory creates OpenAI provider"""
    provider = ProviderFactory.get_provider("openai", api_key="test-key")
    assert isinstance(provider, OpenAIProvider)


def test_factory_create_dashscope_provider():
    """Test factory creates Dashscope provider"""
    provider = ProviderFactory.get_provider("dashscope", api_key="test-key")
    assert isinstance(provider, DashscopeProvider)


def test_factory_unsupported_provider():
    """Test factory raises error for unsupported provider"""
    with pytest.raises(ValueError, match="Unsupported provider"):
        ProviderFactory.get_provider("unsupported_provider", api_key="test-key")


def test_factory_list_providers():
    """Test factory lists all available providers"""
    providers = ProviderFactory.list_providers()
    assert "anthropic" in providers
    assert "openai" in providers
    assert "dashscope" in providers


def test_create_provider_function():
    """Test convenience function for creating provider"""
    provider = create_provider("anthropic", api_key="test-key")
    assert isinstance(provider, AnthropicProvider)


def test_factory_get_default_model():
    """Test factory gets default model for provider"""
    anthropic_model = ProviderFactory.get_default_model("anthropic")
    dashscope_model = ProviderFactory.get_default_model("dashscope")
    assert anthropic_model != ""
    assert dashscope_model == "qwen-coding-plus"