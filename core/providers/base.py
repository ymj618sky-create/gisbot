"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    LLM providers are responsible for communicating with various
    language model APIs (Anthropic, OpenAI, Dashscope, etc.).
    """

    def __init__(self, api_key: str | None, model: str | None = None):
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'anthropic', 'openai')."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether the provider supports streaming responses."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions in OpenAI format
            **kwargs: Additional provider-specific parameters

        Returns:
            Response dict with 'content', 'model', 'usage', etc.
        """
        pass

    def _validate_api_key(self) -> None:
        """Validate that API key is present."""
        if not self.api_key:
            raise ValueError(f"{self.name} provider requires an API key")