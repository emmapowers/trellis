"""Registry for active message handlers.

Provides a way to track connected handlers and broadcast messages to all of them.
Used by watch mode to send reload messages when the bundle is rebuilt.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from trellis.platforms.common.messages import Message

logger = logging.getLogger(__name__)


class MessageSender(Protocol):
    """Protocol for objects that can send messages."""

    async def send_message(self, msg: Message) -> None:
        """Send a message."""
        ...


class HandlerRegistry:
    """Registry of active message handlers.

    Tracks connected handlers and provides broadcast functionality.
    Thread-safe for registration/unregistration.
    """

    _handlers: set[MessageSender]
    _lock: threading.Lock

    def __init__(self) -> None:
        self._handlers = set()
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._handlers)

    def register(self, handler: MessageSender) -> None:
        """Register a handler to receive broadcasts.

        Args:
            handler: Handler with send_message method
        """
        with self._lock:
            self._handlers.add(handler)
            count = len(self._handlers)
        logger.debug("Handler registered, total: %d", count)

    def unregister(self, handler: MessageSender) -> None:
        """Unregister a handler.

        Safe to call even if handler is not registered.

        Args:
            handler: Handler to remove
        """
        with self._lock:
            self._handlers.discard(handler)
            count = len(self._handlers)
        logger.debug("Handler unregistered, total: %d", count)

    async def broadcast(self, msg: Message) -> None:
        """Broadcast a message to all registered handlers.

        Continues broadcasting even if individual handlers fail.

        Args:
            msg: Message to send to all handlers
        """
        with self._lock:
            handlers = list(self._handlers)

        if not handlers:
            return

        logger.debug("Broadcasting %s to %d handlers", type(msg).__name__, len(handlers))

        for handler in handlers:
            try:
                await handler.send_message(msg)
            except Exception:
                logger.exception("Failed to send message to handler")


# Global registry singleton (eager initialization for thread safety)
_global_registry = HandlerRegistry()


def get_global_registry() -> HandlerRegistry:
    """Get the global handler registry singleton.

    Returns:
        The global HandlerRegistry instance
    """
    return _global_registry
