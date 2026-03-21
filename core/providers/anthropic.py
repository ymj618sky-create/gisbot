"""Anthropic LLM provider."""

from typing import Any
from core.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str | None = None, model: str | None = None, **kwargs):
        super().__init__(api_key, model)
        self.model = model or self.DEFAULT_MODEL

        # Allow mock mode without API key for testing
        self.mock_mode = kwargs.get("mock_mode", False)
        if not self.mock_mode:
            self._validate_api_key()

        self.max_retries = kwargs.get("max_retries", 3)

    @property
    def name(self) -> str:
        return "anthropic"

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
        Send a chat completion request to Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions in OpenAI format
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Response dict with 'content', 'model', 'usage', etc.
        """
        # Placeholder implementation - would use anthropic SDK
        # For testing purposes, return a mock response
        return {
            "content": "This is a placeholder response from Anthropic provider. "
                      "Implement actual API call with anthropic SDK.",
            "model": self.model,
            "usage": {
                "prompt_tokens": sum(len(str(m.get("content", ""))) for m in messages),
                "completion_tokens": 20,
                "total_tokens": sum(len(str(m.get("content", ""))) for m in messages) + 20
            },
            "stop_reason": "end_turn",
            "tool_calls": []
        }

    def _format_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Format messages for Anthropic API.

        Converts OpenAI-style messages to Anthropic format.
        """
        formatted = []
        for msg in messages:
            formatted_msg = {"role": msg["role"], "content": msg.get("content", "")}

            # Add reasoning_content if present (for extended thinking)
            if "reasoning_content" in msg:
                formatted_msg["content"] = f"<thinking>{msg['reasoning_content']}</thinking>\n\n{formatted_msg['content']}"

            # Add thinking_blocks if present
            if "thinking_blocks" in msg:
                for block in msg["thinking_blocks"]:
                    formatted_msg["content"] = f"<thinking>{block['content']}</thinking>\n\n{formatted_msg['content']}"

            # Add tool_calls if present
            if "tool_calls" in msg:
                formatted_msg["content"] = [{"type": "text", "text": formatted_msg["content"]}]
                for tool_call in msg["tool_calls"]:
                    formatted_msg["content"].append({
                        "type": "tool_use",
                        "id": tool_call.get("id", ""),
                        "name": tool_call["function"]["name"],
                        "input": tool_call["function"]["arguments"]
                    })

            # Add tool_result if present (for tool response messages)
            if "tool_call_id" in msg:
                formatted_msg["content"] = [{
                    "type": "tool_result",
                    "tool_use_id": msg["tool_call_id"],
                    "content": msg.get("content", "")
                }]

            formatted.append(formatted_msg)

        return formatted

    def _format_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Format tools for Anthropic API.

        Converts OpenAI-style tool definitions to Anthropic format.
        """
        formatted = []
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                formatted.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {})
                })
        return formatted