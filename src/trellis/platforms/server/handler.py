"""WebSocket message handler for server platform."""

from __future__ import annotations

import msgspec
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from trellis.core.components.base import Component
from trellis.core.protocol import decode_registered_message
from trellis.platforms.common.errors import SessionDisconnected
from trellis.platforms.common.handler import AppWrapper, MessageHandler
from trellis.platforms.common.handler_registry import get_global_registry
from trellis.platforms.common.messages import Message

router = APIRouter()


def _is_closed_websocket_error(exc: RuntimeError) -> bool:
    """Return whether a Starlette/Uvicorn runtime error means the socket is closed."""
    message = str(exc)
    return (
        "Unexpected ASGI message 'websocket.send'" in message
        and "after sending 'websocket.close'" in message
    )


class WebSocketMessageHandler(MessageHandler):
    """WebSocket transport with msgpack serialization.

    Uses the base MessageHandler's handle_hello() for session initialization.
    """

    websocket: WebSocket
    _encoder: msgspec.msgpack.Encoder
    _decoder: msgspec.msgpack.Decoder[object]

    def __init__(
        self,
        root_component: Component,
        app_wrapper: AppWrapper,
        websocket: WebSocket,
        batch_delay: float = 1.0 / 30,
    ) -> None:
        """Create a WebSocket message handler.

        Args:
            root_component: The root Trellis component to render
            app_wrapper: Callback to wrap component with TrellisApp
            websocket: The FastAPI WebSocket connection
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
        """
        super().__init__(root_component, app_wrapper, batch_delay=batch_delay)
        self.websocket = websocket
        self._encoder = msgspec.msgpack.Encoder()
        self._decoder = msgspec.msgpack.Decoder()

    async def send_message(self, msg: object) -> None:
        """Send message to client via WebSocket."""
        try:
            await self.websocket.send_bytes(self._encoder.encode(msg))
        except WebSocketDisconnect as exc:
            raise SessionDisconnected() from exc
        except RuntimeError as exc:
            if _is_closed_websocket_error(exc):
                raise SessionDisconnected() from exc
            raise

    async def receive_message(self) -> object:
        """Receive message from client via WebSocket."""
        try:
            data = await self.websocket.receive_bytes()
        except WebSocketDisconnect as exc:
            raise SessionDisconnected() from exc
        raw_message = self._decoder.decode(data)
        extension_message = decode_registered_message(raw_message)
        if extension_message is not None:
            return extension_message
        return msgspec.convert(raw_message, Message)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections.

    The handler.run() method performs:
    1. Hello handshake (session initialization)
    2. Initial render
    3. Event loop
    """
    await websocket.accept()

    # Get top component and wrapper from app state
    top_component = websocket.app.state.trellis_top_component
    app_wrapper = websocket.app.state.trellis_app_wrapper
    if top_component is None or app_wrapper is None:
        await websocket.close(code=4000, reason="No top component configured")
        return

    # Get batch_delay from app state (defaults to 30fps if not set)
    batch_delay = getattr(websocket.app.state, "trellis_batch_delay", 1.0 / 30)

    handler = WebSocketMessageHandler(
        top_component, app_wrapper, websocket, batch_delay=batch_delay
    )

    # Register handler for broadcast (e.g., reload messages)
    registry = get_global_registry()
    registry.register(handler)

    try:
        await handler.run()
    except WebSocketDisconnect:
        pass
    finally:
        registry.unregister(handler)
        handler.cleanup()
