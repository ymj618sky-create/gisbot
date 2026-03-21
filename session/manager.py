"""Session manager for agent conversations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class Session:
    """Represents a conversation session with the agent."""

    def __init__(
        self,
        channel: str,
        chat_id: str,
        sender_id: str,
        memory_window: int = 50,
        last_consolidated: int = 0
    ):
        self.id = str(uuid.uuid4())
        self.channel = channel
        self.chat_id = chat_id
        self.sender_id = sender_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.memory_window = memory_window
        self.last_consolidated = last_consolidated
        self.messages: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {}

    def add_message(self, message: dict[str, Any]) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()

        # Trim to memory window if needed
        if len(self.messages) > self.memory_window * 2:  # Allow double window before trimming
            self._trim_messages()

    def _trim_messages(self) -> None:
        """Trim messages to fit memory window."""
        # Always keep system message
        system_messages = [m for m in self.messages if m.get("role") == "system"]
        other_messages = [m for m in self.messages if m.get("role") != "system"]

        # Keep last memory_window messages (or less if system messages exist)
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

    def set_metadata(self, key: str, value: Any) -> None:
        """Set session metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.now().isoformat()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get session metadata."""
        return self.metadata.get(key, default)

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
            "messages": self.messages,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        session = cls(
            channel=data["channel"],
            chat_id=data["chat_id"],
            sender_id=data["sender_id"],
            memory_window=data.get("memory_window", 50),
            last_consolidated=data.get("last_consolidated", 0)
        )
        session.id = data["id"]
        session.created_at = data["created_at"]
        session.updated_at = data["updated_at"]
        session.messages = data.get("messages", [])
        session.metadata = data.get("metadata", {})
        return session


class SessionManager:
    """Manages conversation sessions."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        return self.data_dir / f"{session_id}.json"

    def create_session(
        self,
        channel: str,
        chat_id: str,
        sender_id: str,
        memory_window: int = 50
    ) -> Session:
        """Create a new session."""
        session = Session(
            channel=channel,
            chat_id=chat_id,
            sender_id=sender_id,
            memory_window=memory_window
        )
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session_path = self._get_session_path(session_id)
        if not session_path.exists():
            return None

        try:
            data = json.loads(session_path.read_text(encoding="utf-8"))
            return Session.from_dict(data)
        except (json.JSONDecodeError, IOError):
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
        session_path.write_text(
            json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        session_path = self._get_session_path(session_id)
        if session_path.exists():
            session_path.unlink()

    def list_sessions(self, limit: int = 100) -> list[Session]:
        """List all sessions."""
        sessions = []
        for session_file in list(self.data_dir.glob("*.json"))[:limit]:
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                sessions.append(Session.from_dict(data))
            except (json.JSONDecodeError, IOError):
                continue
        return sessions

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        from datetime import datetime as dt

        cutoff = dt.now().timestamp() - (days * 24 * 60 * 60)
        deleted = 0

        for session_file in self.data_dir.glob("*.json"):
            try:
                created_at = datetime.fromisoformat(
                    json.loads(session_file.read_text())["created_at"]
                ).timestamp()

                if created_at < cutoff:
                    session_file.unlink()
                    deleted += 1
            except (json.JSONDecodeError, IOError, ValueError, KeyError):
                continue

        return deleted