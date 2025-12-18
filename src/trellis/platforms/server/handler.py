"""WebSocket message handler for server platform."""

from __future__ import annotations

import msgspec
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from trellis.core.message_handler import MessageHandler
from trellis.core.messages import Message
from trellis.core.rendering import IComponent

router = APIRouter()


class WebSocketMessageHandler(MessageHandler):
    """WebSocket transport with msgpack serialization.

    Uses the base MessageHandler's handle_hello() for session initialization.
    """

    websocket: WebSocket
    _encoder: msgspec.msgpack.Encoder
    _decoder: msgspec.msgpack.Decoder[Message]

    def __init__(self, root_component: IComponent, websocket: WebSocket) -> None:
        """Create a WebSocket message handler.

        Args:
            root_component: The root Trellis component to render
            websocket: The FastAPI WebSocket connection
        """
        super().__init__(root_component)
        self.websocket = websocket
        self._encoder = msgspec.msgpack.Encoder()
        # Single decoder for all message types (including HelloMessage)
        self._decoder = msgspec.msgpack.Decoder(Message)

    async def send_message(self, msg: Message) -> None:
        """Send message to client via WebSocket."""
        await self.websocket.send_bytes(self._encoder.encode(msg))

    async def receive_message(self) -> Message:
        """Receive message from client via WebSocket."""
        data = await self.websocket.receive_bytes()
        return self._decoder.decode(data)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections.

    The handler.run() method performs:
    1. Hello handshake (session initialization)
    2. Initial render
    3. Event loop
    """
    await websocket.accept()

    # Get top component from app state
    top_component = websocket.app.state.trellis_top_component
    if top_component is None:
        await websocket.close(code=4000, reason="No top component configured")
        return

    handler = WebSocketMessageHandler(top_component, websocket)

    try:
        await handler.run()
    except WebSocketDisconnect:
        pass
    finally:
        handler.cleanup()
