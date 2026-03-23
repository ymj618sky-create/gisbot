"""Enhanced session manager with context memory and message queue."""

import asyncio
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set
from dataclasses import dataclass, field

from core.utils.json_io import read_json_file, write_json_file


@dataclass
class ContextMemory:
    """Context memory for storing important information across sessions."""

    facts: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_fact(
        self, fact: str, category: str = "general", importance: int = 1
    ) -> None:
        """Add a fact to memory."""
        self.facts.append(
            {
                "id": str(uuid.uuid4()),
                "content": fact,
                "category": category,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.last_updated = datetime.now().isoformat()

    def add_pattern(self, pattern: str, description: str = "") -> None:
        """Add a pattern to memory."""
        self.patterns.append(
            {
                "id": str(uuid.uuid4()),
                "pattern": pattern,
                "description": description,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.last_updated = datetime.now().isoformat()

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        self.preferences[key] = value
        self.last_updated = datetime.now().isoformat()

    def get_relevant_context(self, query: str, limit: int = 5) -> List[str]:
        """Get relevant context items based on query."""
        # Simple keyword matching - can be enhanced with embeddings
        query_lower = query.lower()
        relevant = []

        for fact in sorted(
            self.facts, key=lambda x: x.get("importance", 0), reverse=True
        ):
            if any(
                keyword in query_lower for keyword in fact["content"].lower().split()
            ):
                relevant.append(f"[记忆] {fact['category']}: {fact['content']}")
                if len(relevant) >= limit:
                    break

        return relevant


class MessageQueue:
    """Message queue for handling async message processing."""

    def __init__(self, max_size: int = 1000):
        self._queue: Deque[Dict[str, Any]] = deque(maxlen=max_size)
        self._processing: Set[str] = set()
        self._callbacks: Dict[str, List[callable]] = {}
        self._lock = asyncio.Lock()

    async def push(self, message: Dict[str, Any]) -> str:
        """Push a message to the queue."""
        async with self._lock:
            message_id = str(uuid.uuid4())
            message["id"] = message_id
            message["timestamp"] = datetime.now().isoformat()
            message["status"] = "pending"
            self._queue.append(message)
            return message_id

    async def pop(self) -> Optional[Dict[str, Any]]:
        """Pop a message from the queue."""
        async with self._lock:
            if not self._queue:
                return None
            for msg in self._queue:
                if msg["id"] not in self._processing:
                    msg["status"] = "processing"
                    self._processing.add(msg["id"])
                    return msg
            return None

    async def mark_complete(self, message_id: str, result: Any = None) -> None:
        """Mark a message as complete."""
        async with self._lock:
            self._processing.discard(message_id)
            if message_id in self._callbacks:
                for callback in self._callbacks[message_id]:
                    try:
                        await callback(result)
                    except Exception as e:
                        print(f"Callback error: {e}")
                del self._callbacks[message_id]

    async def register_callback(self, message_id: str, callback: callable) -> None:
        """Register a callback for when a message is complete."""
        async with self._lock:
            if message_id not in self._callbacks:
                self._callbacks[message_id] = []
            self._callbacks[message_id].append(callback)

    def get_status(self) -> Dict[str, int]:
        """Get queue status."""
        return {
            "pending": len([m for m in self._queue if m["id"] not in self._processing]),
            "processing": len(self._processing),
            "total": len(self._queue),
        }


class Session:
    """Enhanced session with context memory and message queue."""

    def __init__(
        self,
        channel: str,
        chat_id: str,
        sender_id: str,
        memory_window: int = 50,
        last_consolidated: int = 0,
        project_id: str = "default",
    ):
        self.id = str(uuid.uuid4())
        self.channel = channel
        self.chat_id = chat_id
        self.sender_id = sender_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.memory_window = memory_window
        self.last_consolidated = last_consolidated
        self.project_id = project_id  # 关联的项目ID
        self.messages: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {}

        # Enhanced features
        self.context_memory: ContextMemory = ContextMemory()
        self.title: str = "新对话"
        self.tags: list[str] = []
        self.is_archived: bool = False

    def add_message(self, message: dict[str, Any]) -> None:
        """Add a message to the session."""
        # Add timestamp if not present (nanobot pattern for append-only logs)
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()

        # Auto-generate title from first user message
        if (
            self.title == "新对话"
            and message.get("role") == "user"
            and len(self.messages) <= 3
        ):
            content = message.get("content", "")
            self.title = content[:50] + "..." if len(content) > 50 else content

        # Trim to memory window if needed
        if len(self.messages) > self.memory_window * 2:
            self._trim_messages()

    def _trim_messages(self) -> None:
        """Trim messages to fit memory window."""
        system_messages = [m for m in self.messages if m.get("role") == "system"]
        other_messages = [m for m in self.messages if m.get("role") != "system"]
        max_other = self.memory_window - len(system_messages)
        if max_other > 0:
            trimmed = system_messages + other_messages[-max_other:]
        else:
            trimmed = system_messages
        self.messages = trimmed

    def get_messages(self, include_system: bool = True) -> list[dict[str, Any]]:
        """Get session messages."""
        if include_system:
            return self.messages.copy()
        return [m for m in self.messages if m.get("role") != "system"]

    def get_context_summary(self) -> str:
        """Get a summary of the conversation context."""
        if not self.messages:
            return "这是一个新的对话。"

        context_parts = []
        context_parts.append(f"对话标题: {self.title}")
        context_parts.append(f"消息数量: {len(self.messages)}")

        # Get recent user messages
        recent_user = [
            m.get("content", "") for m in self.messages[-10:] if m.get("role") == "user"
        ]
        if recent_user:
            context_parts.append(f"最近话题: {', '.join(recent_user[-3:])}")

        # Get relevant context from memory
        if self.context_memory.facts:
            context_parts.append(f"已记住事实: {len(self.context_memory.facts)} 条")

        return "\n".join(context_parts)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set session metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.now().isoformat()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get session metadata."""
        return self.metadata.get(key, default)

    def archive(self) -> None:
        """Archive this session."""
        self.is_archived = True
        self.updated_at = datetime.now().isoformat()

    def unarchive(self) -> None:
        """Unarchive this session."""
        self.is_archived = False
        self.updated_at = datetime.now().isoformat()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the session."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "channel": self.channel,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "memory_window": self.memory_window,
            "last_consolidated": self.last_consolidated,
            "project_id": self.project_id,
            "messages": self.messages,
            "metadata": self.metadata,
            "title": self.title,
            "tags": self.tags,
            "is_archived": self.is_archived,
            "context_memory": self.context_memory.__dict__,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        session = cls(
            channel=data["channel"],
            chat_id=data["chat_id"],
            sender_id=data["sender_id"],
            memory_window=data.get("memory_window", 50),
            last_consolidated=data.get("last_consolidated", 0),
            project_id=data.get("project_id", "default"),
        )
        session.id = data["id"]
        session.created_at = data["created_at"]
        session.updated_at = data["updated_at"]
        session.messages = data.get("messages", [])
        session.metadata = data.get("metadata", {})
        session.title = data.get("title", "新对话")
        session.tags = data.get("tags", [])
        session.is_archived = data.get("is_archived", False)

        # Restore context memory
        if "context_memory" in data:
            cm_data = data["context_memory"]
            session.context_memory = ContextMemory(
                facts=cm_data.get("facts", []),
                patterns=cm_data.get("patterns", []),
                preferences=cm_data.get("preferences", {}),
                last_updated=cm_data.get("last_updated", datetime.now().isoformat()),
            )

        return session


class SessionManager:
    """Enhanced session manager with context memory and message queue."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Session] = {}
        self._message_queue = MessageQueue()
        self._global_memory = ContextMemory()

    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        return self.data_dir / f"{session_id}.json"

    def get_message_queue(self) -> MessageQueue:
        """Get the message queue."""
        return self._message_queue

    def get_global_memory(self) -> ContextMemory:
        """Get global context memory."""
        return self._global_memory

    def create_session(
        self, channel: str, chat_id: str, sender_id: str, memory_window: int = 50,
        project_id: str = "default"
    ) -> Session:
        """Create a new session."""
        session = Session(
            channel=channel,
            chat_id=chat_id,
            sender_id=sender_id,
            memory_window=memory_window,
            project_id=project_id,
        )
        self._sessions[session.id] = session
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID (from cache or disk)."""
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Load from disk
        session_path = self._get_session_path(session_id)
        if not session_path.exists():
            return None

        try:
            data = read_json_file(session_path)
            session = Session.from_dict(data)
            self._sessions[session_id] = session
            return session
        except (FileNotFoundError, OSError):
            return None

    def get_by_channel_chat_id(self, channel: str, chat_id: str) -> Optional[Session]:
        """Get a session by channel and chat ID."""
        for session in self.list_sessions():
            if session.channel == channel and session.chat_id == chat_id:
                return session
        return None

    def save_session(self, session: Session) -> None:
        """Save a session to disk."""
        session_path = self._get_session_path(session.id)
        write_json_file(session_path, session.to_dict())
        self._sessions[session.id] = session

    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        session_path = self._get_session_path(session_id)
        if session_path.exists():
            session_path.unlink()
        self._sessions.pop(session_id, None)

    def list_sessions(
        self,
        limit: int = 100,
        include_archived: bool = False,
        channel: Optional[str] = None,
    ) -> list[Session]:
        """List all sessions."""
        sessions = []

        # Load from disk if not in cache
        for session_file in list(self.data_dir.glob("*.json"))[:limit]:
            try:
                data = read_json_file(session_file)
                session = Session.from_dict(data)

                # Filter by archived status
                if not include_archived and session.is_archived:
                    continue

                # Filter by channel
                if channel and session.channel != channel:
                    continue

                sessions.append(session)
            except (FileNotFoundError, OSError):
                continue

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def search_sessions(self, query: str, limit: int = 20) -> list[Session]:
        """Search sessions by title, messages, or tags."""
        query_lower = query.lower()
        matching = []

        for session in self.list_sessions(limit=limit * 2):
            # Search title
            if query_lower in session.title.lower():
                matching.append(session)
                continue

            # Search tags
            if any(query_lower in tag.lower() for tag in session.tags):
                matching.append(session)
                continue

            # Search messages
            for message in session.messages:
                content = message.get("content", "")
                if query_lower in content.lower():
                    matching.append(session)
                    break

        return matching[:limit]

    def get_context_for_session(self, session_id: str) -> str:
        """Get combined context for a session."""
        session = self.get_session(session_id)
        if not session:
            return ""

        context_parts = [
            session.get_context_summary(),
        ]

        # Add global memory facts if relevant
        if self._global_memory.facts:
            context_parts.append(f"\n全局记忆: {len(self._global_memory.facts)} 条")

        # Add relevant context from memory
        last_user_msg = None
        for msg in reversed(session.messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if last_user_msg:
            relevant = session.context_memory.get_relevant_context(last_user_msg)
            if relevant:
                context_parts.append("\n相关记忆:")
                context_parts.extend(relevant)

        return "\n".join(context_parts)

    def consolidate_memory(self, session_id: str) -> None:
        """Consolidate important information from session into memory."""
        session = self.get_session(session_id)
        if not session:
            return

        # Extract facts from recent messages
        recent_messages = session.messages[-session.memory_window :]

        for msg in recent_messages:
            if msg.get("role") != "assistant":
                continue

            content = msg.get("content", "").lower()

            # Detect facts (statements about preferences, settings, patterns)
            fact_keywords = ["prefer", "use", "always", "remember", "should", "default"]
            for keyword in fact_keywords:
                if keyword in content:
                    # Extract the fact
                    sentences = content.split(". ")
                    for sentence in sentences:
                        if keyword in sentence:
                            session.context_memory.add_fact(
                                fact=msg.get("content", ""),
                                category="preference",
                                importance=2,
                            )
                    break

        self.save_session(session)

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        from datetime import datetime as dt

        cutoff = dt.now().timestamp() - (days * 24 * 60 * 60)
        deleted = 0

        for session_file in self.data_dir.glob("*.json"):
            try:
                data = read_json_file(session_file)
                created_at = datetime.fromisoformat(data["created_at"]).timestamp()

                if created_at < cutoff and not data.get("is_archived", False):
                    session_file.unlink()
                    deleted += 1
            except (FileNotFoundError, OSError, ValueError, KeyError):
                continue

        return deleted
