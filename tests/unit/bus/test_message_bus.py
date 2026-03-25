"""
MessageBus单元测试

测试消息总线的核心功能：
- 消息发布和消费
- 异步队列处理
- 多通道支持
- 上下文传递
"""
import pytest
import asyncio
from datetime import datetime
from core.bus.events import InboundMessage, OutboundMessage
from core.bus.queue import MessageBus


class TestMessageBus:
    """MessageBus核心功能测试"""

    @pytest.mark.asyncio
    async def test_publish_and_consume_single_message(self, message_bus):
        """测试发布和消费单条消息"""
        # Given - 准备入站消息
        inbound = InboundMessage(
            channel="web",
            chat_id="test-chat",
            content="测试消息"
        )

        # When - 发布消息
        await message_bus.publish_inbound(inbound)

        # Then - 能够消费消息
        consumed = await message_bus.consume_inbound()
        assert consumed is not None
        assert consumed.channel == "web"
        assert consumed.chat_id == "test-chat"
        assert consumed.content == "测试消息"

    @pytest.mark.asyncio
    async def test_publish_outbound_message(self, message_bus):
        """测试发布出站消息"""
        # Given - 准备出站消息
        outbound = OutboundMessage(
            channel="web",
            chat_id="test-chat",
            content="回复消息",
            message_id="msg-123"
        )

        # When - 发布消息
        await message_bus.publish_outbound(outbound)

        # Then - 能够消费消息
        consumed = await message_bus.consume_outbound()
        assert consumed is not None
        assert consumed.message_id == "msg-123"
        assert consumed.content == "回复消息"

    @pytest.mark.asyncio
    async def test_multiple_messages_queue(self, message_bus):
        """测试多条消息排队"""
        # Given - 准备多条消息
        messages = [
            InboundMessage(channel="web", chat_id="chat-1", content=f"消息{i}")
            for i in range(3)
        ]

        # When - 发布所有消息
        for msg in messages:
            await message_bus.publish_inbound(msg)

        # Then - 按FIFO顺序消费
        for i in range(3):
            consumed = await message_bus.consume_inbound()
            assert consumed is not None
            assert consumed.content == f"消息{i}"

    @pytest.mark.asyncio
    async def test_timeout_on_empty_queue(self, message_bus):
        """测试空队列超时"""
        # When - 尝试从空队列消费
        result = await message_bus.consume_inbound(timeout=0.1)

        # Then - 应该返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_message_context(self, message_bus):
        """测试消息上下文传递"""
        # Given - 带上下文的消息
        inbound = InboundMessage(
            channel="web",
            chat_id="test-chat",
            content="消息",
            context={"user_id": "user-123", "source": "api"}
        )

        # When - 发布和消费
        await message_bus.publish_inbound(inbound)
        consumed = await message_bus.consume_inbound()

        # Then - 上下文保持不变
        assert consumed.context is not None
        assert consumed.context["user_id"] == "user-123"
        assert consumed.context["source"] == "api"

    @pytest.mark.asyncio
    async def test_message_metadata(self, message_bus):
        """测试消息元数据"""
        # Given - 带元数据的消息
        inbound = InboundMessage(
            channel="web",
            chat_id="test-chat",
            content="消息",
            metadata={"priority": "high", "tags": ["urgent"]}
        )

        # When - 发布和消费
        await message_bus.publish_inbound(inbound)
        consumed = await message_bus.consume_inbound()

        # Then - 元数据保持不变
        assert consumed.metadata is not None
        assert consumed.metadata["priority"] == "high"
        assert consumed.metadata["tags"] == ["urgent"]

    @pytest.mark.asyncio
    async def test_concurrent_publishers(self, message_bus):
        """测试并发发布者"""
        # Given - 准备并发任务
        async def publish_messages(count: int):
            for i in range(count):
                msg = InboundMessage(
                    channel="web",
                    chat_id=f"chat-{i % 3}",
                    content=f"消息{i}"
                )
                await message_bus.publish_inbound(msg)

        # When - 并发发布
        tasks = [publish_messages(10) for _ in range(3)]
        await asyncio.gather(*tasks)

        # Then - 消费所有消息
        consumed_count = 0
        while True:
            msg = await message_bus.consume_inbound(timeout=0.1)
            if msg is None:
                break
            consumed_count += 1

        assert consumed_count == 30

    @pytest.mark.asyncio
    async def test_shutdown_clears_queues(self, message_bus):
        """测试关闭清空队列"""
        # Given - 发布消息
        await message_bus.publish_inbound(
            InboundMessage(channel="web", chat_id="chat", content="消息")
        )

        # When - 关闭总线
        await message_bus.shutdown()

        # Then - 队列为空
        result = await message_bus.consume_inbound(timeout=0.1)
        assert result is None


class TestInboundMessage:
    """InboundMessage数据模型测试"""

    def test_create_minimal_message(self):
        """测试创建最小消息"""
        msg = InboundMessage(
            channel="web",
            chat_id="chat-1",
            content="测试"
        )
        assert msg.channel == "web"
        assert msg.chat_id == "chat-1"
        assert msg.content == "测试"
        assert msg.timestamp is not None
        assert msg.context is None
        assert msg.metadata is None

    def test_message_with_all_fields(self):
        """测试包含所有字段的消息"""
        timestamp = datetime.now()
        msg = InboundMessage(
            channel="web",
            chat_id="chat-1",
            content="测试",
            timestamp=timestamp,
            context={"user_id": "123"},
            metadata={"priority": "high"}
        )
        assert msg.timestamp == timestamp
        assert msg.context == {"user_id": "123"}
        assert msg.metadata == {"priority": "high"}

    def test_message_serialization(self):
        """测试消息序列化"""
        msg = InboundMessage(
            channel="web",
            chat_id="chat-1",
            content="测试"
        )
        data = msg.model_dump()
        assert "channel" in data
        assert "chat_id" in data
        assert "content" in data
        assert "timestamp" in data


class TestOutboundMessage:
    """OutboundMessage数据模型测试"""

    def test_create_minimal_outbound(self):
        """测试创建最小出站消息"""
        msg = OutboundMessage(
            channel="web",
            chat_id="chat-1",
            content="回复"
        )
        assert msg.channel == "web"
        assert msg.chat_id == "chat-1"
        assert msg.content == "回复"
        assert msg.message_id is None

    def test_outbound_with_message_id(self):
        """测试带消息ID的出站消息"""
        msg = OutboundMessage(
            channel="web",
            chat_id="chat-1",
            content="回复",
            message_id="msg-123"
        )
        assert msg.message_id == "msg-123"

    def test_outbound_serialization(self):
        """测试出站消息序列化"""
        msg = OutboundMessage(
            channel="web",
            chat_id="chat-1",
            content="回复",
            message_id="msg-123"
        )
        data = msg.model_dump()
        assert "message_id" in data
        assert data["message_id"] == "msg-123"