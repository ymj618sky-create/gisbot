"""Message tool for sending messages to other channels."""

from typing import Any
from pathlib import Path
from core.tools.base import Tool


class MessageTool(Tool):
    """
    Tool for sending messages to other channels.

    Allows the agent to send messages to different chat channels or IDs.
    Useful for cross-channel communication and multi-party conversations.
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace

    @property
    def name(self) -> str:
        return "message"

    @property
    def description(self) -> str:
        return (
            "Send a message to a specific channel and chat ID. "
            "Use this to communicate with other conversations or channels."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Target channel (e.g., 'web', 'cli', 'slack')"
                },
                "chat_id": {
                    "type": "string",
                    "description": "Target chat ID within the channel"
                },
                "content": {
                    "type": "string",
                    "description": "Message content to send"
                },
                "media": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of media file paths"
                }
            },
            "required": ["channel", "chat_id", "content"]
        }

    async def execute(
        self,
        channel: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        **kwargs
    ) -> str:
        """Send a message to the specified channel and chat ID."""
        try:
            from core.bus.queue import MessageBus
            from core.bus.events import OutboundMessage

            # Create outbound message
            message = OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=content,
                metadata={"media": media or []}
            )

            # Publish to message bus
            bus = MessageBus()
            await bus.publish_outbound(message)

            return f"Message sent to {channel}:{chat_id}"

        except ImportError:
            return "Error: MessageBus not available"
        except Exception as e:
            return f"Error sending message: {str(e)}"