"""
MessageBus事件模型

定义消息总线中使用的数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InboundMessage:
    """入站消息（从通道到Agent）"""
    channel: str  # 通道名称
    chat_id: str  # 聊天ID
    content: str  # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    context: dict | None = None  # 上下文信息
    metadata: dict | None = None  # 元数据

    def model_dump(self) -> dict:
        """将消息转换为字典"""
        return {
            "channel": self.channel,
            "chat_id": self.chat_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "metadata": self.metadata,
        }


@dataclass
class OutboundMessage:
    """出站消息（从Agent到通道）"""
    channel: str  # 通道名称
    chat_id: str  # 聊天ID
    content: str  # 消息内容
    message_id: str | None = None  # 消息ID（可选）

    def model_dump(self) -> dict:
        """将消息转换为字典"""
        return {
            "channel": self.channel,
            "chat_id": self.chat_id,
            "content": self.content,
            "message_id": self.message_id,
        }
