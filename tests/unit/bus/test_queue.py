"""Tests for Message Bus."""

import pytest
import asyncio
from core.bus.queue import MessageBus
from core.bus.events import InboundMessage, OutboundMessage


@pytest.mark.asyncio
async def test_publish_inbound():
    """Test publishing inbound message"""
    bus = MessageBus()
    msg = InboundMessage(channel="test", sender_id="user", chat_id="1", content="Hello")
    await bus.publish_inbound(msg)
    received = await bus.consume_inbound()
    assert received.content == "Hello"


@pytest.mark.asyncio
async def test_publish_outbound():
    """Test publishing outbound message"""
    bus = MessageBus()
    msg = OutboundMessage(channel="test", chat_id="1", content="Response")
    await bus.publish_outbound(msg)
    messages = bus.get_outbound_messages()
    assert len(messages) == 1
    assert messages[0].content == "Response"


@pytest.mark.asyncio
async def test_session_key_generation():
    """Test session key generation"""
    msg = InboundMessage(channel="web", sender_id="user", chat_id="123", content="Test")
    assert msg.session_key == "web:123"


@pytest.mark.asyncio
async def test_consume_inbound_blocks():
    """Test that consume_inbound blocks until message is available"""
    bus = MessageBus()

    async def delayed_publish():
        await asyncio.sleep(0.1)
        msg = InboundMessage(channel="test", sender_id="user", chat_id="1", content="Delayed")
        await bus.publish_inbound(msg)

    # Start delayed publish in background
    asyncio.create_task(delayed_publish())

    # consume should block and then return the message
    received = await bus.consume_inbound()
    assert received.content == "Delayed"


@pytest.mark.asyncio
async def test_consume_inbound_fifo():
    """Test that messages are consumed in FIFO order"""
    bus = MessageBus()
    await bus.publish_inbound(InboundMessage(channel="test", sender_id="user", chat_id="1", content="First"))
    await bus.publish_inbound(InboundMessage(channel="test", sender_id="user", chat_id="1", content="Second"))
    await bus.publish_inbound(InboundMessage(channel="test", sender_id="user", chat_id="1", content="Third"))

    first = await bus.consume_inbound()
    second = await bus.consume_inbound()
    third = await bus.consume_inbound()

    assert first.content == "First"
    assert second.content == "Second"
    assert third.content == "Third"


@pytest.mark.asyncio
async def test_multiple_outbound_messages():
    """Test publishing multiple outbound messages"""
    bus = MessageBus()
    await bus.publish_outbound(OutboundMessage(channel="test", chat_id="1", content="Msg1"))
    await bus.publish_outbound(OutboundMessage(channel="test", chat_id="1", content="Msg2"))
    await bus.publish_outbound(OutboundMessage(channel="test", chat_id="1", content="Msg3"))

    messages = bus.get_outbound_messages()
    assert len(messages) == 3
    assert messages[0].content == "Msg1"
    assert messages[1].content == "Msg2"
    assert messages[2].content == "Msg3"


@pytest.mark.asyncio
async def test_outbound_messages_includes_metadata():
    """Test that outbound message metadata is preserved"""
    bus = MessageBus()
    msg = OutboundMessage(
        channel="test",
        chat_id="1",
        content="Response",
        metadata={"priority": "high", "source": "agent"}
    )
    await bus.publish_outbound(msg)

    messages = bus.get_outbound_messages()
    assert messages[0].metadata == {"priority": "high", "source": "agent"}


@pytest.mark.asyncio
async def test_inbound_message_with_media():
    """Test inbound message with media attachments"""
    bus = MessageBus()
    msg = InboundMessage(
        channel="test",
        sender_id="user",
        chat_id="1",
        content="Look at this",
        media=["image1.jpg", "image2.png"]
    )
    await bus.publish_inbound(msg)

    received = await bus.consume_inbound()
    assert received.media == ["image1.jpg", "image2.png"]


@pytest.mark.asyncio
async def test_outbound_message_timestamp():
    """Test that outbound message has default timestamp"""
    import re
    msg = OutboundMessage(channel="test", chat_id="1", content="Response")
    # ISO format timestamp
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", msg.timestamp)


@pytest.mark.asyncio
async def test_get_outbound_returns_copy():
    """Test that get_outbound_messages returns a copy, not the internal list"""
    bus = MessageBus()
    await bus.publish_outbound(OutboundMessage(channel="test", chat_id="1", content="Msg1"))

    messages1 = bus.get_outbound_messages()
    messages1.append("fake")  # Try to modify returned list

    messages2 = bus.get_outbound_messages()
    assert len(messages2) == 1  # Should not be affected by modification
    assert "fake" not in messages2