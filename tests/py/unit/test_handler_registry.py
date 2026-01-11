"""Tests for handler registry and broadcast functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from trellis.platforms.common.handler_registry import HandlerRegistry
from trellis.platforms.common.messages import ReloadMessage


class TestHandlerRegistry:
    """Tests for HandlerRegistry."""

    def test_registry_starts_empty(self) -> None:
        """New registry has no handlers."""
        registry = HandlerRegistry()
        assert len(registry) == 0

    def test_register_handler(self) -> None:
        """Handler can be registered."""
        registry = HandlerRegistry()
        handler = MagicMock()

        registry.register(handler)

        assert len(registry) == 1

    def test_unregister_handler(self) -> None:
        """Handler can be unregistered."""
        registry = HandlerRegistry()
        handler = MagicMock()

        registry.register(handler)
        registry.unregister(handler)

        assert len(registry) == 0

    def test_unregister_unknown_handler_is_safe(self) -> None:
        """Unregistering unknown handler doesn't raise."""
        registry = HandlerRegistry()
        handler = MagicMock()

        # Should not raise
        registry.unregister(handler)

    def test_register_multiple_handlers(self) -> None:
        """Multiple handlers can be registered."""
        registry = HandlerRegistry()
        handler1 = MagicMock()
        handler2 = MagicMock()

        registry.register(handler1)
        registry.register(handler2)

        assert len(registry) == 2


class TestHandlerRegistryBroadcast:
    """Tests for broadcasting messages to handlers."""

    @pytest.mark.anyio
    async def test_broadcast_sends_to_all_handlers(self) -> None:
        """Broadcast sends message to all registered handlers."""
        registry = HandlerRegistry()

        handler1 = MagicMock()
        handler1.send_message = AsyncMock()
        handler2 = MagicMock()
        handler2.send_message = AsyncMock()

        registry.register(handler1)
        registry.register(handler2)

        msg = ReloadMessage()
        await registry.broadcast(msg)

        handler1.send_message.assert_called_once_with(msg)
        handler2.send_message.assert_called_once_with(msg)

    @pytest.mark.anyio
    async def test_broadcast_to_empty_registry(self) -> None:
        """Broadcast to empty registry doesn't raise."""
        registry = HandlerRegistry()
        msg = ReloadMessage()

        # Should not raise
        await registry.broadcast(msg)

    @pytest.mark.anyio
    async def test_broadcast_continues_on_handler_error(self) -> None:
        """Broadcast continues if a handler's send_message raises."""
        registry = HandlerRegistry()

        handler1 = MagicMock()
        handler1.send_message = AsyncMock(side_effect=Exception("connection lost"))
        handler2 = MagicMock()
        handler2.send_message = AsyncMock()

        registry.register(handler1)
        registry.register(handler2)

        msg = ReloadMessage()
        await registry.broadcast(msg)

        # handler2 should still receive the message
        handler2.send_message.assert_called_once_with(msg)


class TestGlobalHandlerRegistry:
    """Tests for global registry access."""

    def test_get_global_registry_returns_same_instance(self) -> None:
        """get_global_registry returns singleton instance."""
        from trellis.platforms.common.handler_registry import get_global_registry

        registry1 = get_global_registry()
        registry2 = get_global_registry()

        assert registry1 is registry2
