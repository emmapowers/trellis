"""Browser runtime for Trellis apps.

This module provides a lightweight runtime that replaces FastAPI/WebSocket
for running Trellis apps entirely in the browser via Pyodide.
"""

from __future__ import annotations

import asyncio
import typing as tp
from collections.abc import Callable

from trellis.core.message_handler import MessageHandler
from trellis.core.messages import EventMessage, Message, RenderMessage
from trellis.core.rendering import IComponent

__all__ = ["BrowserRuntime", "PlaygroundMessageHandler"]


class PlaygroundMessageHandler(MessageHandler):
    """Playground transport - queue-based messaging via Pyodide.

    Uses an async queue for receiving events from JavaScript,
    and a callback for sending render updates back.

    Example usage from JavaScript (via Pyodide):
        ```javascript
        const handler = pyodide.runPython(`
            from trellis_playground import PlaygroundMessageHandler
            from my_app import App
            PlaygroundMessageHandler(App)
        `);

        // Register callback for render updates
        handler.set_render_callback((tree) => {
            renderToDOM(tree.toJs());
        });

        // Start the message loop
        handler.run();

        // When user clicks a button:
        handler.post_event("e5:onClick", [eventData]);
        ```
    """

    _inbox: asyncio.Queue[Message]
    _on_render: Callable[[dict[str, tp.Any]], None] | None

    def __init__(self, root_component: IComponent) -> None:
        """Create a new playground message handler.

        Args:
            root_component: The root Trellis component to render
        """
        super().__init__(root_component)
        self._inbox = asyncio.Queue()
        self._on_render = None

    def set_render_callback(self, callback: Callable[[dict[str, tp.Any]], None]) -> None:
        """Register callback to receive render updates.

        Args:
            callback: Function called with tree dict on each render
        """
        self._on_render = callback

    async def send_message(self, msg: Message) -> None:
        """Push render updates to JS via callback."""
        if isinstance(msg, RenderMessage) and self._on_render is not None:
            self._on_render(msg.tree)

    async def receive_message(self) -> Message:
        """Wait for JS to post a message."""
        return await self._inbox.get()

    def post_event(self, callback_id: str, args: list[tp.Any] | None = None) -> None:
        """Post an event from JavaScript.

        Args:
            callback_id: The callback ID to invoke (e.g., "e5:onClick")
            args: Arguments to pass to the callback
        """
        self._inbox.put_nowait(EventMessage(callback_id=callback_id, args=args or []))


# Backwards-compatible alias
BrowserRuntime = PlaygroundMessageHandler
