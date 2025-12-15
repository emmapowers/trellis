"""PyTauri message handler for desktop platform.

Uses channel-based communication with the same message protocol as WebSocket.
Messages are received via an async queue (populated by trellis_send command)
and sent via PyTauri channel, allowing the standard MessageHandler.run() loop.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import msgspec

from trellis.core.message_handler import MessageHandler
from trellis.core.messages import Message

if TYPE_CHECKING:
    from pytauri.ipc import Channel

    from trellis.core.rendering import IComponent


class PyTauriMessageHandler(MessageHandler):
    """Channel-based transport for PyTauri desktop platform.

    Uses an async queue for receiving messages, allowing the standard
    MessageHandler.run() loop to work. The trellis_send command enqueues
    messages, and receive_message() pulls from the queue.
    """

    _channel: Channel
    _queue: asyncio.Queue[bytes]
    _encoder: msgspec.msgpack.Encoder
    _decoder: msgspec.msgpack.Decoder[Message]

    def __init__(self, root_component: IComponent, channel: Channel) -> None:
        """Create a PyTauri message handler.

        Args:
            root_component: The root Trellis component to render
            channel: The PyTauri channel for sending messages to client
        """
        super().__init__(root_component)
        self._channel = channel
        self._queue = asyncio.Queue()
        self._encoder = msgspec.msgpack.Encoder()
        self._decoder = msgspec.msgpack.Decoder(Message)

    async def send_message(self, msg: Message) -> None:
        """Send message to client via channel."""
        data = self._encoder.encode(msg)
        self._channel.send(bytes(data))

    async def receive_message(self) -> Message:
        """Receive message from queue (populated by trellis_send command)."""
        data = await self._queue.get()
        return self._decoder.decode(data)

    def enqueue(self, data: bytes) -> None:
        """Enqueue incoming message data from trellis_send command."""
        self._queue.put_nowait(data)
