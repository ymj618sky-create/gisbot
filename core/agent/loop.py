"""Agent Loop for processing messages and managing conversations."""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from core.agent.context import ContextBuilder
from core.agent.memory import MemoryStore
from core.agent.skills import SkillsLoader
from core.tools.registry import ToolRegistry
from core.providers.base import LLMProvider
from session.manager import SessionManager


# Maximum characters for tool results to prevent context bloat
_TOOL_RESULT_MAX_CHARS = 50000

logger = logging.getLogger(__name__)


@dataclass
class AgentLoopConfig:
    """Configuration for AgentLoop."""

    max_iterations: int = 15
    memory_window: int = 50

    # Optional components (will use defaults if None)
    context_builder: Optional[ContextBuilder] = None
    skills_loader: Optional[SkillsLoader] = None
    memory_store: Optional[MemoryStore] = None


class AgentLoop:
    """
    Main agent loop for processing messages and managing conversations.

    This class orchestrates the agent's interaction flow:
    1. Build context (system prompt + history)
    2. Call LLM with tools
    3. Execute tools if requested
    4. Process results and return response
    """

    # Cache for expensive operations - NOTE: These are class-level caches, so they persist
    # across instances. They must be reset when tools or skills change.
    _skills_summary: str | None = None
    _tools_definitions: list[dict[str, Any]] | None = None

    # Async memory consolidation tracking (nanobot pattern)
    _consolidating: set[str] = set()
    _consolidation_locks: dict[str, asyncio.Lock] = {}
    _consolidation_tasks: set[asyncio.Task] = set()

    @classmethod
    def reset_cache(cls) -> None:
        """Reset the class-level cache. Call this when tools or skills change."""
        cls._skills_summary = None
        cls._tools_definitions = None
        # Also reset context builder cache
        ContextBuilder.invalidate_bootstrap_cache()

    def __init__(
        self,
        workspace: Path,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        session_manager: SessionManager,
        config: Optional[AgentLoopConfig] = None,
        context_builder: Optional[ContextBuilder] = None,
        skills_loader: Optional[SkillsLoader] = None,
        memory_store: Optional[MemoryStore] = None,
        max_iterations: int = 15,
        memory_window: int = 50,
    ):
        self.workspace = workspace
        self.provider = provider
        self.tool_registry = tool_registry
        self.session_manager = session_manager

        # Support both new config-based and legacy init
        if config is not None:
            self.max_iterations = config.max_iterations
            self.memory_window = config.memory_window
            self.context_builder = config.context_builder or ContextBuilder(
                workspace, memory_store=config.memory_store
            )
            self.skills_loader = config.skills_loader or SkillsLoader(workspace)
            self.memory_store = config.memory_store or MemoryStore(workspace)
        else:
            # Legacy init path for backward compatibility
            self.memory_store = memory_store or MemoryStore(workspace)
            self.context_builder = context_builder or ContextBuilder(
                workspace, memory_store=self.memory_store
            )
            self.skills_loader = skills_loader or SkillsLoader(workspace)
            self.max_iterations = max_iterations
            self.memory_window = memory_window

    async def process_direct(
        self,
        content: str,
        channel: str = "cli",
        chat_id: str = "direct",
        media: Optional[list[str]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Process a direct message from user.

        Args:
            content: User message content
            channel: Channel name (cli, web, etc.)
            chat_id: Chat identifier
            media: Optional list of media file paths
            on_progress: Optional callback for progress updates

        Returns:
            Agent response
        """
        # Get or create session
        session = self.session_manager.get_by_channel_chat_id(channel, chat_id)
        if not session:
            session = self.session_manager.create_session(
                channel=channel,
                chat_id=chat_id,
                sender_id="direct",
                memory_window=self.memory_window,
            )

        # Run agent loop
        return await self._run_agent_loop(
            session=session,
            current_message=content,
            media=media,
            on_progress=on_progress,
        )

    async def _run_agent_loop(
        self,
        session: Any,
        current_message: str,
        media: Optional[list[str]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Execute the main agent conversation loop.

        Args:
            session: Session object
            current_message: Current user message
            media: Optional media attachments
            on_progress: Optional progress callback

        Returns:
            Final agent response
        """
        if on_progress:
            on_progress("Building context...")

        # Add current user message to session first
        session.add_message({"role": "user", "content": current_message})

        # Get current message history (excluding system prompt)
        history = [m for m in session.get_messages() if m.get("role") != "system"]

        # Use cached tools definitions (build once per process)
        if AgentLoop._tools_definitions is None:
            AgentLoop._tools_definitions = self.tool_registry.get_definitions()
        tools = AgentLoop._tools_definitions

        # Use cached skills summary (build once per agent instance)
        if AgentLoop._skills_summary is None:
            AgentLoop._skills_summary = self.skills_loader.build_skills_summary()
        skills_summary = AgentLoop._skills_summary

        skill_names = self.skills_loader.get_always_skills()

        # Build messages for LLM
        # Clean runtime context prefix from user message (nanobot pattern)
        clean_current_message = self._clean_runtime_context(current_message)

        messages = self.context_builder.build_messages(
            history=history,
            current_message=clean_current_message,
            skill_names=skill_names,
            media=media,
            channel=session.channel,
            chat_id=session.chat_id,
        )

        # Add skills summary to system prompt if available
        if skills_summary:
            system_msg = messages[0]
            system_msg["content"] += f"\n\n{skills_summary}"

        # Main loop
        iteration = 0
        assistant_response = ""
        # Track recent tool calls for loop detection
        recent_tool_calls: list[str] = []
        # Track if tools were needed in this request
        tools_needed = False

        while iteration < self.max_iterations:
            iteration += 1

            if on_progress:
                on_progress(
                    f"Processing (iteration {iteration}/{self.max_iterations})..."
                )

            # Call LLM - only send tools in first iteration or if tools were previously needed
            try:
                if on_progress:
                    on_progress(
                        f"正在调用模型分析 (迭代 {iteration}/{self.max_iterations})..."
                    )
                # Performance optimization: only send tools in first iteration
                # or if tools were already used in this request
                tools_to_send = tools if iteration == 1 or tools_needed else None
                llm_response = await self.provider.chat(
                    messages=messages, tools=tools_to_send
                )
            except Exception as e:
                error_msg = f"模型调用失败: {str(e)}"
                if on_progress:
                    on_progress(error_msg)
                return error_msg

            # Check for error response (nanobot pattern: finish_reason == "error" indicates invalid response)
            finish_reason = llm_response.get("finish_reason")
            if finish_reason == "error":
                logger.error(f"LLM returned error response at iteration {iteration}")
                # Don't add the error response to messages to prevent context pollution
                # Force a response without tools to break out of the loop
                try:
                    error_response = await self.provider.chat(
                        messages=messages
                        + [
                            {
                                "role": "system",
                                "content": "The previous response was invalid. Please provide a direct answer to the user's question without using any tools.",
                            }
                        ],
                        tools=None,
                    )
                    assistant_response = error_response.get("content", "")
                    if assistant_response and assistant_response.strip():
                        session.add_message(
                            {"role": "assistant", "content": assistant_response}
                        )
                        break
                except Exception as e:
                    logger.error(f"Failed to recover from error response: {e}")
                assistant_response = "抱歉，遇到了技术问题。请重新提问或提供更多信息。"
                break

            # Extract content
            content = llm_response.get("content", "")
            if not content:
                content = "I'm sorry, I couldn't generate a response."

            # Check for tool calls
            tool_calls = llm_response.get("tool_calls", [])

            if on_progress and tool_calls:
                tool_names = [tc.get("function", {}).get("name") for tc in tool_calls]
                on_progress(f"执行工具: {', '.join(tool_names)}")

            # Debug logging
            if tool_calls:
                logger.info(
                    f"Iteration {iteration}: {len(tool_calls)} tool(s) requested: {[tc.get('function', {}).get('name') for tc in tool_calls]}"
                )
                tools_needed = True
            else:
                logger.info(f"Iteration {iteration}: No tool calls, content length: {len(content)}")

            # If no tool calls, return the response immediately
            if not tool_calls:
                # Filter out empty responses
                if not content or not content.strip():
                    logger.warning(f"Iteration {iteration}: Empty response with no tools")
                    # Try one more time with a system prompt
                    if iteration < self.max_iterations:
                        messages.append({
                            "role": "system",
                            "content": "Please provide a direct answer. If you need to use tools, call them explicitly. Don't return empty responses."
                        })
                        continue
                    assistant_response = "抱歉，无法生成响应。请重新提问或提供更具体的信息."
                else:
                    assistant_response = content

                # Add assistant message to session before returning
                assistant_msg = {"role": "assistant", "content": content}
                messages.append(assistant_msg)
                session.add_message(assistant_msg)
                break

            # Add assistant message to messages for next LLM call
            # Note: content can be empty if tool_calls are present (nanobot pattern)
            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            # Also add to session
            session.add_message(assistant_msg)

            # Execute tool calls
            # Check for loop before executing tools
            if tool_calls:
                current_tools = [tc.get('function', {}).get('name') for tc in tool_calls]
                recent_tool_calls.extend(current_tools)
                if len(recent_tool_calls) > 10:
                    recent_tool_calls = recent_tool_calls[-10:]

                # Simple loop detection: if same tool called 3+ times consecutively
                loop_detected = False
                for tool_name in current_tools:
                    if recent_tool_calls[-3:] == [tool_name, tool_name, tool_name]:
                        logger.warning(f"Detected tool loop: {tool_name} called 3+ times")
                        # Add a system message to break the loop
                        messages.append({
                            "role": "system",
                            "content": f"工具 {tool_name} 已被重复调用多次。请使用已获取的工具结果完成任务，不要再调用此工具。"
                        })
                        loop_detected = True
                        break

                if loop_detected:
                    # Skip all tool execution and continue to next iteration
                    continue

            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                tool_args_str = tool_call.get("function", {}).get("arguments", "{}")

                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute tool
                if on_progress:
                    on_progress(f"执行: {tool_name}")
                try:
                    tool_result = await self.tool_registry.execute(tool_name, tool_args)
                    if on_progress:
                        on_progress(f"完成: {tool_name}")
                except Exception as e:
                    tool_result = f"工具执行失败: {str(e)}"
                    if on_progress:
                        on_progress(f"失败: {tool_name} - {str(e)}")
                    logger.error(f"Tool {tool_name} failed: {e}")

                # Truncate tool result if too large (nanobot pattern)
                tool_result = self._truncate_tool_result(tool_result)

                # Add tool result to messages - this must come immediately after assistant with tool_calls
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_name,
                        "content": tool_result,
                    }
                )

                # Add to session
                session.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_name,
                        "content": tool_result,
                    }
                )

        else:
            # Reached max iterations
            if on_progress:
                on_progress("Reached maximum iterations")
            assistant_response = "I've reached the maximum number of iterations. Let me summarize what we have so far."

        # Save session
        self.session_manager.save_session(session)

        # Trigger async memory consolidation (nanobot pattern)
        self._schedule_memory_consolidation(session)

        return assistant_response

    @staticmethod
    def _clean_runtime_context(message: str) -> str:
        """Remove runtime context prefix from user message."""
        runtime_tag = ContextBuilder._RUNTIME_CONTEXT_TAG
        if runtime_tag in message:
            # Remove everything up to and including the runtime context
            idx = message.find(runtime_tag)
            # Find the end of the runtime context (next newline after the block)
            if idx != -1:
                remaining = message[idx:]
                # Find the double newline that ends the runtime context
                end_idx = remaining.find("\n\n")
                if end_idx != -1:
                    return remaining[end_idx + 2 :].strip()
        return message

    @staticmethod
    def _truncate_tool_result(result: str) -> str:
        """Truncate tool result if it exceeds maximum characters."""
        if len(result) > _TOOL_RESULT_MAX_CHARS:
            truncated = result[:_TOOL_RESULT_MAX_CHARS]
            truncated += f"\n\n[Result truncated: {len(result) - _TOOL_RESULT_MAX_CHARS} characters omitted]"
            return truncated
        return result

    def _schedule_memory_consolidation(self, session: Any) -> None:
        """Schedule async memory consolidation if needed."""
        unconsolidated = len(session.messages) - session.last_consolidated

        # Only consolidate if we've accumulated enough new messages
        if (
            unconsolidated >= self.memory_window
            and session.key not in self._consolidating
        ):
            session_key = getattr(
                session, "key", f"{session.channel}:{session.chat_id}"
            )
            self._consolidating.add(session_key)

            # Get or create lock for this session
            lock = self._consolidation_locks.setdefault(session_key, asyncio.Lock())

            async def _consolidate_and_unlock():
                try:
                    async with lock:
                        await self._consolidate_memory_async(session)
                finally:
                    self._consolidating.discard(session_key)
                    task = asyncio.current_task()
                    if task:
                        self._consolidation_tasks.discard(task)

            task = asyncio.create_task(_consolidate_and_unlock())
            self._consolidation_tasks.add(task)

    async def _consolidate_memory_async(self, session: Any) -> None:
        """Async memory consolidation (nanobot pattern)."""
        try:
            # Extract important information from recent messages
            recent_messages = session.messages[-self.memory_window :]
            messages_to_consolidate = []

            # Find assistant messages that contain valuable information
            for msg in recent_messages:
                if msg.get("role") == "assistant" and msg.get("content"):
                    content = msg.get("content", "")
                    # Flag messages that might contain learned information
                    if any(
                        keyword in content.lower()
                        for keyword in [
                            "learned",
                            "preference",
                            "remember",
                            "default",
                            "user prefers",
                            "workflow",
                            "pattern",
                            "approach",
                        ]
                    ):
                        messages_to_consolidate.append(msg)

            if messages_to_consolidate:
                # Write to HISTORY.md with timestamp
                from datetime import datetime

                timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
                history_entry = f"{timestamp}\n### Memory Consolidation\n"

                for msg in messages_to_consolidate:
                    history_entry += f"From: {msg.get('content')[:200]}...\n\n"

                self.memory_store.append_history(history_entry)

                # Write consolidated summary to MEMORY.md
                consolidated = self._consolidate_to_memory(messages_to_consolidate)
                if consolidated:
                    current_memory = self.memory_store.read_long_term()
                    if current_memory:
                        new_memory = current_memory + "\n\n" + consolidated
                    else:
                        new_memory = consolidated
                    self.memory_store.write_long_term(new_memory)

            session.last_consolidated = len(session.messages)
            logger.info(
                f"Memory consolidation completed for session {getattr(session, 'key', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")

    def _consolidate_to_memory(self, messages: list[dict[str, Any]]) -> str:
        """Consolidate messages into a memory entry."""
        if not messages:
            return ""

        from datetime import datetime

        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")

        # Extract key information from messages
        consolidated_parts = [f"## {timestamp}\n\n### Learned Information"]

        for msg in messages:
            content = msg.get("content", "")
            if content:
                # Extract sentences that contain valuable information
                sentences = [s.strip() for s in content.split(".") if s.strip()]
                valuable = [
                    s
                    for s in sentences
                    if any(
                        keyword in s.lower()
                        for keyword in [
                            "prefer",
                            "use",
                            "always",
                            "remember",
                            "note",
                            "important",
                            "workflow",
                            "pattern",
                            "approach",
                            "best practice",
                        ]
                    )
                ]
                if valuable:
                    consolidated_parts.extend(valuable)

        if len(consolidated_parts) > 1:
            return "\n".join(consolidated_parts) + "\n"
        return ""

    def stop(self) -> None:
        """Stop the agent loop and clean up resources."""
        # Any cleanup if needed
        pass
