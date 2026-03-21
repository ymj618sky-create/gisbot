"""OpenAI LLM provider."""

from typing import Any
from core.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT models)."""

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str | None, model: str | None = None, **kwargs):
        super().__init__(api_key, model)
        self.model = model or self.DEFAULT_MODEL
        self._validate_api_key()
        self.max_retries = kwargs.get("max_retries", 3)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Send a chat completion request to OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions in OpenAI format
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Response dict with 'content', 'model', 'usage', etc.
        """
        # Placeholder implementation - would use openai SDK
        # For testing purposes, return a mock response
        return {
            "content": "This is a placeholder response from OpenAI provider. "
                      "Implement actual API call with openai SDK.",
            "model": self.model,
            "usage": {
                "prompt_tokens": sum(len(str(m.get("content", ""))) for m in messages),
                "completion_tokens": 20,
                "total_tokens": sum(len(str(m.get("content", ""))) for m in messages) + 20
            },
            "finish_reason": "stop",
            "tool_calls": []
        }

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_request_body(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Build request body for API call."""
        body = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": kwargs.get("tool_choice", "auto") if tools else None
        }

        # Add optional parameters
        if "max_tokens" in kwargs:
            body["max_tokens"] = kwargs["max_tokens"]
        if "temperature" in kwargs:
            body["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]

        return body