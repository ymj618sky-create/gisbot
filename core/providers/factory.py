"""Provider Factory for creating LLM provider instances."""

from typing import Optional
from core.providers.base import LLMProvider
from core.providers.anthropic import AnthropicProvider
from core.providers.openai import OpenAIProvider
from core.providers.dashscope import DashscopeProvider
from config import settings


class ProviderFactory:
    """
    Provider 工厂，用于创建和管理 LLM provider 实例。
    """

    _providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "dashscope": DashscopeProvider,
    }

    @classmethod
    def get_provider(
        cls,
        provider_name: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs
    ) -> LLMProvider:
        """
        获取指定的 provider 实例。

        Args:
            provider_name: Provider 名称 (anthropic, openai, dashscope)
            model: 模型 ID，如未指定则使用默认模型
            api_key: API Key，如未指定则从环境变量读取
            **kwargs: 额外的 provider 参数

        Returns:
            LLMProvider 实例

        Raises:
            ValueError: Provider 不支持或未找到
        """
        # 如果未指定 provider，使用默认值
        if not provider_name:
            provider_name = getattr(settings, 'DEFAULT_PROVIDER', 'dashscope')

        # 查找 provider 类
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Available providers: {available}"
            )

        # 获取 API Key
        if not api_key:
            api_key = cls._get_api_key(provider_name)

        # 创建 provider 实例
        return provider_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def _get_api_key(cls, provider_name: str) -> str:
        """从环境变量获取 API Key。"""
        env_key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "dashscope": "DASHSCOPE_API_KEY",
        }
        env_key = env_key_map.get(provider_name.lower())
        return getattr(settings, env_key, "")

    @classmethod
    def get_default_model(cls, provider_name: str) -> str:
        """获取 provider 的默认模型 ID。"""
        provider_class = cls._providers.get(provider_name.lower())
        if provider_class and hasattr(provider_class, 'DEFAULT_MODEL'):
            return provider_class.DEFAULT_MODEL
        return ""

    @classmethod
    def list_providers(cls) -> list[str]:
        """列出所有可用的 provider 名称。"""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """
        注册一个新的 provider。

        Args:
            name: Provider 名称
            provider_class: Provider 类（必须继承自 LLMProvider）
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(f"{provider_class} must inherit from LLMProvider")
        cls._providers[name.lower()] = provider_class


# 便捷函数
def create_provider(
    provider_name: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    **kwargs
) -> LLMProvider:
    """
    便捷函数：创建 provider 实例。

    Args:
        provider_name: Provider 名称 (anthropic, openai, dashscope)
        model: 模型 ID
        api_key: API Key
        **kwargs: 额外的 provider 参数

    Returns:
        LLMProvider 实例
    """
    return ProviderFactory.get_provider(
        provider_name=provider_name,
        model=model,
        api_key=api_key,
        **kwargs
    )