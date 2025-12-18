"""Browser message handler for Pyodide platform.

Uses a JS bridge for communication - messages are sent via bridge callbacks
and received via an async queue that the bridge populates.
"""

from __future__ import annotations

import asyncio
import typing as tp
from collections.abc import Callable

from trellis.core.message_handler import MessageHandler
from trellis.core.messages import (
    EventMessage,
    HelloMessage,
    Message,
)
from trellis.core.rendering import IComponent

__all__ = ["BrowserMessageHandler"]


class BrowserMessageHandler(MessageHandler):
    """Bridge-based transport for Pyodide browser platform.

    Uses an async queue for receiving messages from JavaScript,
    and a callback for sending messages back to JavaScript.

    The JS bridge is registered as a module before Python code runs,
    and BrowserPlatform.run() connects this handler to the bridge.
    """

    _inbox: asyncio.Queue[Message]
    _send_callback: Callable[[tp.Any], None] | None
    _serializer: Callable[[dict[str, tp.Any]], tp.Any]

    def __init__(self, root_component: IComponent) -> None:
        """Create a browser message handler.

        Args:
            root_component: The root Trellis component to render
        """
        super().__init__(root_component)
        self._inbox = asyncio.Queue()
        self._send_callback = None
        # Default serializer just returns dict as-is (for tests)
        self._serializer = lambda x: x

    def set_send_callback(
        self,
        callback: Callable[[tp.Any], None],
        serializer: Callable[[dict[str, tp.Any]], tp.Any] | None = None,
    ) -> None:
        """Register callback for sending messages to JavaScript.

        Args:
            callback: Function called with serialized message for each outgoing message
            serializer: Optional function to convert dict to JS-compatible format.
                       If not provided, dicts are passed directly (for tests).
        """
        self._send_callback = callback
        if serializer is not None:
            self._serializer = serializer

    async def send_message(self, msg: Message) -> None:
        """Send message to JavaScript via callback."""
        if self._send_callback is None:
            return

        # Convert msgspec struct to dict for JavaScript
        msg_dict = _message_to_dict(msg)

        # Serialize (converts to JS object in Pyodide, or passes dict in tests)
        serialized = self._serializer(msg_dict)
        self._send_callback(serialized)

    async def receive_message(self) -> Message:
        """Receive message from queue (populated by enqueue_message)."""
        return await self._inbox.get()

    def enqueue_message(self, msg_dict: dict[str, tp.Any]) -> None:
        """Enqueue a message from JavaScript.

        Called by the JS bridge when it receives a message from BrowserClient.

        Args:
            msg_dict: Message as dict with 'type' field (may be JsProxy in Pyodide)
        """
        # In Pyodide, msg_dict may be a JsProxy - convert to native Python dict
        if hasattr(msg_dict, "to_py"):
            msg_dict = msg_dict.to_py()
        msg = _dict_to_message(msg_dict)
        self._inbox.put_nowait(msg)

    def post_event(self, callback_id: str, args: list[tp.Any] | None = None) -> None:
        """Convenience method to post an event message.

        Args:
            callback_id: The callback ID to invoke
            args: Arguments to pass to the callback
        """
        self._inbox.put_nowait(EventMessage(callback_id=callback_id, args=args or []))


def _message_to_dict(msg: Message) -> dict[str, tp.Any]:
    """Convert a msgspec Message struct to a plain dict for JavaScript."""
    # Get the tag (message type) from the struct config
    msg_type = msg.__struct_config__.tag

    # Build dict from struct fields
    result: dict[str, tp.Any] = {"type": msg_type}
    for field in msg.__struct_fields__:
        result[field] = getattr(msg, field)

    return result


def _dict_to_message(msg_dict: dict[str, tp.Any]) -> Message:
    """Convert a dict from JavaScript to a msgspec Message struct."""
    msg_type = msg_dict.get("type")

    if msg_type == "hello":
        return HelloMessage(client_id=msg_dict.get("client_id", ""))
    if msg_type == "event":
        callback_id = msg_dict.get("callback_id")
        if callback_id is None:
            raise ValueError("Event message missing required 'callback_id' field")
        return EventMessage(
            callback_id=callback_id,
            args=msg_dict.get("args", []),
        )
    raise ValueError(f"Unknown message type: {msg_type}")
