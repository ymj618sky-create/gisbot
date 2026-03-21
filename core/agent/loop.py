"""Agent Loop for processing messages and managing conversations."""

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional
from core.agent.context import ContextBuilder
from core.agent.memory import MemoryStore
from core.agent.skills import SkillsLoader
from core.tools.registry import ToolRegistry
from core.providers.base import LLMProvider
from session.manager import SessionManager


class AgentLoop:
    """
    Main agent loop for processing messages and managing conversations.

    This class orchestrates the agent's interaction flow:
    1. Build context (system prompt + history)
    2. Call LLM with tools
    3. Execute tools if requested
    4. Process results and return response
    """

    def __init__(
        self,
        workspace: Path,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        session_manager: SessionManager,
        context_builder: Optional[ContextBuilder] = None,
        skills_loader: Optional[SkillsLoader] = None,
        memory_store: Optional[MemoryStore] = None,
        max_iterations: int = 15,
        memory_window: int = 50
    ):
        self.workspace = workspace
        self.provider = provider
        self.tool_registry = tool_registry
        self.session_manager = session_manager
        self.context_builder = context_builder or ContextBuilder(workspace)
        self.skills_loader = skills_loader or SkillsLoader(workspace)
        self.memory_store = memory_store or MemoryStore(workspace)
        self.max_iterations = max_iterations
        self.memory_window = memory_window

    async def process_direct(
        self,
        content: str,
        channel: str = "cli",
        chat_id: str = "direct",
        media: Optional[list[str]] = None,
        on_progress: Optional[Callable[[str], None]] = None
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
                memory_window=self.memory_window
            )

        # Run agent loop
        return await self._run_agent_loop(
            session=session,
            current_message=content,
            media=media,
            on_progress=on_progress
        )

    async def _run_agent_loop(
        self,
        session: Any,
        current_message: str,
        media: Optional[list[str]] = None,
        on_progress: Optional[Callable[[str], None]] = None
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
        session.add_message({
            "role": "user",
            "content": current_message
        })

        # Get current message history (excluding system prompt)
        history = [m for m in session.get_messages() if m.get("role") != "system"]

        # Build context with skills summary
        skills_summary = self.skills_loader.build_skills_summary()
        skill_names = self.skills_loader.get_always_skills()

        # Build messages for LLM
        messages = self.context_builder.build_messages(
            history=history,
            current_message=current_message,
            skill_names=skill_names,
            media=media,
            channel=session.channel,
            chat_id=session.chat_id
        )

        # Add skills summary to system prompt if available
        if skills_summary:
            system_msg = messages[0]
            system_msg["content"] += f"\n\n{skills_summary}"

        # Get tool definitions
        tools = self.tool_registry.get_definitions()

        # Main loop
        iteration = 0
        assistant_response = ""

        while iteration < self.max_iterations:
            iteration += 1

            if on_progress:
                on_progress(f"Processing (iteration {iteration}/{self.max_iterations})...")

            # Call LLM
            try:
                llm_response = await self.provider.chat(
                    messages=messages,
                    tools=tools if tools else None
                )
            except Exception as e:
                return f"Error calling LLM: {str(e)}"

            # Extract content
            content = llm_response.get("content", "")
            if not content:
                content = "I'm sorry, I couldn't generate a response."

            # Check for tool calls
            tool_calls = llm_response.get("tool_calls", [])

            if on_progress and tool_calls:
                on_progress(f"Executing {len(tool_calls)} tool(s)...")

            # Add assistant message to session
            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            session.add_message(assistant_msg)

            if not tool_calls:
                # No tool calls, return response
                assistant_response = content
                break

            # Execute tool calls
            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                tool_args_str = tool_call.get("function", {}).get("arguments", "{}")

                try:
                    import json
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute tool
                tool_result = await self.tool_registry.execute(tool_name, tool_args)

                # Add tool result to messages
                messages = self.context_builder.add_tool_result(
                    messages,
                    tool_call_id=tool_call.get("id", ""),
                    tool_name=tool_name,
                    result=tool_result
                )

                # Add to session
                session.add_message({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "content": tool_result
                })

            # Check for CRS issues in results (GIS-specific)
            if assistant_response and ("CRS" in assistant_response or "coordinate" in assistant_response.lower()):
                # CRS was already handled by the tools
                pass

        else:
            # Reached max iterations
            if on_progress:
                on_progress("Reached maximum iterations")
            assistant_response = "I've reached the maximum number of iterations. Let me summarize what we have so far."

        # Save session
        self.session_manager.save_session(session)

        # Check if memory consolidation is needed
        self._check_memory_consolidation(session)

        return assistant_response

    def _check_memory_consolidation(self, session: Any) -> None:
        """Check if memory consolidation is needed."""
        if len(session.messages) > session.memory_window:
            # In a full implementation, this would:
            # 1. Extract unprocessed messages
            # 2. Call LLM with save_memory tool
            # 3. Save to HISTORY.md and MEMORY.md
            # For now, just update the last_consolidated marker
            session.last_consolidated = len(session.messages)

    def stop(self) -> None:
        """Stop the agent loop and clean up resources."""
        # Any cleanup if needed
        pass