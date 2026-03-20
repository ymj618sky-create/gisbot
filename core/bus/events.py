"""Event definitions for message bus."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class InboundMessage:
    """Incoming message from a channel."""
    channel: str
    sender_id: str
    chat_id: str
    content: str
    media: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def session_key(self) -> str:
        """Unique session identifier."""
        return f"{self.channel}:{self.chat_id}"


@dataclass
class OutboundMessage:
    """Outgoing message to a channel."""
    channel: str
    chat_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())