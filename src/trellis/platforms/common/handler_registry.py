"""Registry for active message handlers.

Provides a way to track connected handlers and broadcast messages to all of them.
Used by watch mode to send reload messages when the bundle is rebuilt.
"""

from __future__ import annotations

import logging
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

    def __init__(self) -> None:
        self._handlers = set()

    def __len__(self) -> int:
        return len(self._handlers)

    def register(self, handler: MessageSender) -> None:
        """Register a handler to receive broadcasts.

        Args:
            handler: Handler with send_message method
        """
        self._handlers.add(handler)
        logger.debug("Handler registered, total: %d", len(self._handlers))

    def unregister(self, handler: MessageSender) -> None:
        """Unregister a handler.

        Safe to call even if handler is not registered.

        Args:
            handler: Handler to remove
        """
        self._handlers.discard(handler)
        logger.debug("Handler unregistered, total: %d", len(self._handlers))

    async def broadcast(self, msg: Message) -> None:
        """Broadcast a message to all registered handlers.

        Continues broadcasting even if individual handlers fail.

        Args:
            msg: Message to send to all handlers
        """
        if not self._handlers:
            return

        logger.debug("Broadcasting %s to %d handlers", type(msg).__name__, len(self._handlers))

        for handler in list(self._handlers):  # Copy to avoid mutation during iteration
            try:
                await handler.send_message(msg)
            except Exception:
                logger.exception("Failed to send message to handler")


# Global registry singleton
_global_registry: HandlerRegistry | None = None


def get_global_registry() -> HandlerRegistry:
    """Get the global handler registry singleton.

    Returns:
        The global HandlerRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = HandlerRegistry()
    return _global_registry
