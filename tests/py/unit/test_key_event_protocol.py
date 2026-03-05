"""Tests for key event response protocol."""

from __future__ import annotations

from unittest.mock import AsyncMock

import msgspec
import pytest

from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import KeyEventResponseMessage, Message


class TestKeyEventResponseMessage:
    def test_encode_decode(self):
        msg = KeyEventResponseMessage(request_id="req-123", handled=True)
        encoded = msgspec.json.encode(msg)
        decoded = msgspec.json.decode(encoded, type=Message)
        assert isinstance(decoded, KeyEventResponseMessage)
        assert decoded.request_id == "req-123"
        assert decoded.handled is True

    def test_handled_false(self):
        msg = KeyEventResponseMessage(request_id="req-456", handled=False)
        encoded = msgspec.json.encode(msg)
        decoded = msgspec.json.decode(encoded, type=Message)
        assert isinstance(decoded, KeyEventResponseMessage)
        assert decoded.handled is False

    def test_tag_field(self):
        msg = KeyEventResponseMessage(request_id="req-789", handled=True)
        encoded = msgspec.json.encode(msg)
        data = msgspec.json.decode(encoded)
        assert data["type"] == "key_event_response"


class TestKeyCallbackHandling:
    """Tests for the handler's key callback wrapping logic."""

    @pytest.fixture
    def handler_setup(self, app_wrapper, make_component):
        """Create a minimal MessageHandler for testing."""
        comp = make_component("TestRoot")
        handler = MessageHandler(comp, app_wrapper)
        handler.session = RenderSession(comp)
        render(handler.session)
        handler.send_message = AsyncMock()
        return handler

    @pytest.mark.anyio
    async def test_key_callback_returns_true(self, handler_setup):
        handler = handler_setup
        assert handler._is_key_event_callback("__key_filters__[0].handler")
        assert handler._is_key_event_callback("__global_key_filters__[0].handler")

    @pytest.mark.anyio
    async def test_not_key_callback(self, handler_setup):
        handler = handler_setup
        assert not handler._is_key_event_callback("on_click")
        assert not handler._is_key_event_callback("on_key_down")

    @pytest.mark.anyio
    async def test_key_callback_handled_true(self, handler_setup):
        handler = handler_setup

        def my_handler():
            return True

        await handler._invoke_key_callback(
            "test|__key_filters__[0].handler",
            "test",
            my_handler,
            ["req-1"],
        )

        handler.send_message.assert_called_once()
        msg = handler.send_message.call_args[0][0]
        assert isinstance(msg, KeyEventResponseMessage)
        assert msg.request_id == "req-1"
        assert msg.handled is True

    @pytest.mark.anyio
    async def test_key_callback_returns_none_is_handled(self, handler_setup):
        handler = handler_setup

        def my_handler():
            pass  # returns None

        await handler._invoke_key_callback(
            "test|__key_filters__[0].handler",
            "test",
            my_handler,
            ["req-2"],
        )

        msg = handler.send_message.call_args[0][0]
        assert msg.handled is True

    @pytest.mark.anyio
    async def test_key_callback_returns_false_is_pass(self, handler_setup):
        handler = handler_setup

        def my_handler():
            return False

        await handler._invoke_key_callback(
            "test|__key_filters__[0].handler",
            "test",
            my_handler,
            ["req-3"],
        )

        msg = handler.send_message.call_args[0][0]
        assert msg.handled is False

    @pytest.mark.anyio
    async def test_key_callback_exception_is_not_handled(self, handler_setup):
        handler = handler_setup

        def my_handler():
            raise ValueError("oops")

        await handler._invoke_key_callback(
            "test|__key_filters__[0].handler",
            "test",
            my_handler,
            ["req-4"],
        )

        msg = handler.send_message.call_args[0][0]
        assert msg.handled is False

    @pytest.mark.anyio
    async def test_async_key_callback(self, handler_setup):
        handler = handler_setup

        async def my_handler():
            return True

        await handler._invoke_key_callback(
            "test|__key_filters__[0].handler",
            "test",
            my_handler,
            ["req-5"],
        )

        msg = handler.send_message.call_args[0][0]
        assert msg.handled is True
