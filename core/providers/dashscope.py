"""阿里云百炼（Dashscope）LLM provider."""

import json
from typing import Any
import asyncio
import logging

from aiohttp import ClientSession, ClientResponseError
from core.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class DashscopeProvider(LLMProvider):
    """阿里云百炼 API provider（Qwen 系列模型）。"""

    DEFAULT_MODEL = "qwen3.5-plus"
    DEFAULT_TIMEOUT = 300  # 5 minutes for long-running GIS operations

    def __init__(self, api_key: str | None, model: str | None = None, **kwargs):
        super().__init__(api_key, model)
        self.model = model or self.DEFAULT_MODEL
        self._validate_api_key()

        # 从 kwargs 或使用默认值
        self.max_retries = kwargs.get("max_retries", 5)
        self.timeout = kwargs.get("timeout", self.DEFAULT_TIMEOUT)

        # 记录配置
        logger.info(f"DashscopeProvider initialized: model={self.model}, timeout={self.timeout}s, max_retries={self.max_retries}")

        # Coding Plan 专属 Base URL（兼容 OpenAI 协议）
        self.base_url = kwargs.get(
            "base_url",
            "https://coding.dashscope.aliyuncs.com/v1"
        )

    @property
    def name(self) -> str:
        return "dashscope"

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
        向阿里云百炼 API 发送聊天请求。

        Args:
            messages: 包含 'role' 和 'content' 的消息字典列表
            tools: 可选的 OpenAI 格式工具定义列表
            **kwargs: 额外的 provider 参数

        Returns:
            包含 'content', 'model', 'usage' 等的响应字典
        """
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()
        body = self._build_request_body(messages, tools, **kwargs)

        logger.debug(f"Dashscope chat request: model={self.model}, messages={len(messages)}, timeout={self.timeout}s")

        for attempt in range(self.max_retries):
            try:
                async with ClientSession() as session:
                    async with session.post(
                        url,
                        headers=headers,
                        json=body,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.debug(f"Dashscope response received: attempt {attempt + 1}/{self.max_retries}")
                            return self._parse_response(data)
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"Dashscope API error (attempt {attempt + 1}/{self.max_retries}): "
                                f"Status {response.status}, {error_text}"
                            )
                            if attempt < self.max_retries - 1:
                                # 指数退避：2^attempt 秒
                                delay = 2 ** attempt
                                logger.info(f"Retrying in {delay}s...")
                                await asyncio.sleep(delay)
                                continue
                            raise Exception(
                                f"Dashscope API error: {response.status} - {error_text}"
                            )
            except ClientResponseError as e:
                logger.error(f"Dashscope client error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    await asyncio.sleep(delay)
                    continue
                raise Exception(f"Dashscope client error: {e}")
            except asyncio.TimeoutError:
                logger.error(f"Dashscope timeout after {self.timeout}s (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                raise Exception(f"Dashscope API timeout after {self.timeout}s (max retries exhausted)")
            except Exception as e:
                logger.error(f"Dashscope request error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    await asyncio.sleep(delay)
                    continue
                raise Exception(f"Dashscope request failed: {e}")

        # 如果所有重试都失败
        raise Exception(f"Dashscope API failed after {self.max_retries} attempts")

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        解析 API 响应。

        Args:
            data: 原始 API 响应数据

        Returns:
            标准化后的响应字典
        """
        try:
            choices = data.get("choices", [])
            if not choices:
                logger.warning(f"Dashscope response has no choices: {data}")
                return {
                    "content": "API returned no choices",
                    "model": self.model,
                    "usage": data.get("usage", {}),
                    "finish_reason": "stop",
                    "tool_calls": []
                }

            choice = choices[0]
            message = choice.get("message", {})

            # 提取内容
            content = message.get("content", "")
            if isinstance(content, list):
                # 处理多模态内容（文本 + 图片等）
                content_text = ""
                for item in content:
                    if item.get("type") == "text":
                        content_text += item.get("text", "")
                content = content_text
            elif content is None:
                content = ""

            # 提取工具调用
            tool_calls = message.get("tool_calls", [])

            # Debug logging for tool calls
            if tool_calls:
                logger.debug(f"Tool calls from Dashscope: {tool_calls}")
            else:
                logger.debug(f"No tool calls in response. Content: {content[:200]}...")

            return {
                "content": content,
                "model": data.get("model", self.model),
                "usage": data.get("usage", {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }),
                "finish_reason": choice.get("finish_reason", "stop"),
                "tool_calls": tool_calls
            }
        except Exception as e:
            logger.error(f"Failed to parse Dashscope response: {e}")
            logger.debug(f"Response data: {data}")
            return {
                "content": "Failed to parse API response",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "tool_calls": []
            }

    def _get_headers(self) -> dict[str, str]:
        """获取 API 请求的 HTTP headers。"""
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
        """构建 API 请求体。"""
        body = {
            "model": self.model,
            "messages": messages
        }

        # 添加工具定义 - Dashscope uses tools parameter with function definitions
        if tools:
            body["tools"] = tools
            # 使用 'required' 而非 'auto' 可以避免模型过度依赖工具
            tool_choice = kwargs.get("tool_choice", "auto")
            body["tool_choice"] = tool_choice
            logger.debug(f"Adding {len(tools)} tools to request with tool_choice={tool_choice}")

        # 添加可选参数
        if "max_tokens" in kwargs:
            body["max_tokens"] = kwargs["max_tokens"]
        if "temperature" in kwargs:
            body["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]

        return body