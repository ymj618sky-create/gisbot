"""
pytest fixtures for MessageBus tests
"""
import pytest
from core.bus.queue import MessageBus


@pytest.fixture
def message_bus():
    """创建一个MessageBus实例用于测试"""
    bus = MessageBus()
    yield bus
    # 清理
    import asyncio
    asyncio.run(bus.shutdown())