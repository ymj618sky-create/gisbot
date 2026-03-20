"""Message queue for inter-component communication."""

import asyncio
from typing import Optional
from core.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """Simple in-memory message bus for agent communication."""

    def __init__(self):
        self._inbound_queue: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self._outbound_messages: list[OutboundMessage] = []

    async def publish_inbound(self, message: InboundMessage) -> None:
        """Publish an inbound message."""
        await self._inbound_queue.put(message)

    async def consume_inbound(self) -> InboundMessage:
        """Consume an inbound message (blocking)."""
        return await self._inbound_queue.get()

    async def publish_outbound(self, message: OutboundMessage) -> None:
        """Publish an outbound message."""
        self._outbound_messages.append(message)

    def get_outbound_messages(self) -> list[OutboundMessage]:
        """Get all published outbound messages (for testing)."""
        return self._outbound_messages.copy()