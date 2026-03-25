"""
MessageBus队列实现

基于asyncio.Queue的异步消息队列，支持并发发布和消费
"""
import asyncio
from typing import Optional

from core.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    消息总线 - 基于asyncio.Queue实现

    支持入站和出站消息的异步发布和消费
    提供超时控制和优雅关闭
    """

    def __init__(self):
        """初始化消息总线，创建入站和出站队列"""
        self._inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self._outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._shutdown_event = asyncio.Event()

    async def publish_inbound(self, message: InboundMessage) -> None:
        """
        发布入站消息到队列

        Args:
            message: 入站消息对象
        """
        await self._inbound.put(message)

    async def consume_inbound(self, timeout: float = 5.0) -> Optional[InboundMessage]:
        """
        从入站队列消费消息

        Args:
            timeout: 超时时间（秒），超过返回None

        Returns:
            InboundMessage对象，超时返回None
        """
        try:
            return await asyncio.wait_for(self._inbound.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def publish_outbound(self, message: OutboundMessage) -> None:
        """
        发布出站消息到队列

        Args:
            message: 出站消息对象
        """
        await self._outbound.put(message)

    async def consume_outbound(self, timeout: float = 5.0) -> Optional[OutboundMessage]:
        """
        从出站队列消费消息

        Args:
            timeout: 超时时间（秒），超过返回None

        Returns:
            OutboundMessage对象，超时返回None
        """
        try:
            return await asyncio.wait_for(self._outbound.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def shutdown(self) -> None:
        """
        关闭消息总线，清空所有队列

        此方法会：
        1. 标记总线为已关闭
        2. 清空所有待处理消息
        3. 取消所有等待中的消费者
        """
        self._shutdown_event.set()

        # 清空队列
        while not self._inbound.empty():
            try:
                self._inbound.get_nowait()
            except asyncio.QueueEmpty:
                break

        while not self._outbound.empty():
            try:
                self._outbound.get_nowait()
            except asyncio.QueueEmpty:
                break

    def is_shutdown(self) -> bool:
        """检查总线是否已关闭"""
        return self._shutdown_event.is_set()

    @property
    def inbound_size(self) -> int:
        """获取入站队列大小"""
        return self._inbound.qsize()

    @property
    def outbound_size(self) -> int:
        """获取出站队列大小"""
        return self._outbound.qsize()