"""Unit tests for server WebSocket transport behavior."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import WebSocketDisconnect

from trellis.core.rendering.session import SessionDisconnected
from trellis.platforms.common.messages import PatchMessage
from trellis.platforms.server.handler import WebSocketMessageHandler


class _FakeWebSocket:
    """Minimal websocket stub for transport tests."""

    def __init__(self) -> None:
        self.send_error: BaseException | None = None
        self.receive_error: BaseException | None = None

    async def send_bytes(self, data: bytes) -> None:
        if self.send_error is not None:
            raise self.send_error

    async def receive_bytes(self) -> bytes:
        if self.receive_error is not None:
            raise self.receive_error
        return b""


class TestWebSocketMessageHandler:
    """Tests for WebSocket-specific disconnect normalization."""

    def test_send_message_raises_session_disconnected_for_closed_websocket(
        self,
        noop_component,
        app_wrapper,
    ) -> None:
        websocket = _FakeWebSocket()
        websocket.send_error = RuntimeError(
            "Unexpected ASGI message 'websocket.send', after sending 'websocket.close' or response already completed."
        )
        handler = WebSocketMessageHandler(noop_component, app_wrapper, websocket)  # type: ignore[arg-type]

        with pytest.raises(SessionDisconnected):
            asyncio.run(handler.send_message(PatchMessage(patches=[])))

    def test_receive_message_raises_session_disconnected_for_websocket_disconnect(
        self,
        noop_component,
        app_wrapper,
    ) -> None:
        websocket = _FakeWebSocket()
        websocket.receive_error = WebSocketDisconnect(code=1000)
        handler = WebSocketMessageHandler(noop_component, app_wrapper, websocket)  # type: ignore[arg-type]

        with pytest.raises(SessionDisconnected):
            asyncio.run(handler.receive_message())
