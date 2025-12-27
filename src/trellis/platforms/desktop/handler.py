"""PyTauri message handler for desktop platform.

Uses channel-based communication with the same message protocol as WebSocket.
Messages are received via an async queue (populated by trellis_send command)
and sent via PyTauri channel, allowing the standard MessageHandler.run() loop.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import msgspec

from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import Message

if TYPE_CHECKING:
    from pytauri.ipc import Channel

    from trellis.core.components.base import Component


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

    def __init__(
        self,
        root_component: Component,
        channel: Channel,
        batch_delay: float = 1.0 / 30,
    ) -> None:
        """Create a PyTauri message handler.

        Args:
            root_component: The root Trellis component to render
            channel: The PyTauri channel for sending messages to client
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
        """
        super().__init__(root_component, batch_delay=batch_delay)
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
