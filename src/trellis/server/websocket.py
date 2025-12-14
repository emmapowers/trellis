"""WebSocket message handler for Trellis server."""

from __future__ import annotations

from uuid import uuid4

import msgspec
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from trellis.core.message_handler import MessageHandler
from trellis.core.messages import Message as CoreMessage
from trellis.core.rendering import IComponent
from trellis.server.messages import (
    HelloMessage,
    HelloResponseMessage,
    Message,
)

router = APIRouter()


class WebSocketMessageHandler(MessageHandler):
    """WebSocket transport with msgpack serialization."""

    websocket: WebSocket
    _encoder: msgspec.msgpack.Encoder
    _hello_decoder: msgspec.msgpack.Decoder[Message]
    _message_decoder: msgspec.msgpack.Decoder[CoreMessage]

    def __init__(self, root_component: IComponent, websocket: WebSocket) -> None:
        """Create a WebSocket message handler.

        Args:
            root_component: The root Trellis component to render
            websocket: The FastAPI WebSocket connection
        """
        super().__init__(root_component)
        self.websocket = websocket
        self._encoder = msgspec.msgpack.Encoder()
        # Separate decoders: one for hello handshake, one for message loop
        self._hello_decoder = msgspec.msgpack.Decoder(Message)
        self._message_decoder = msgspec.msgpack.Decoder(CoreMessage)

    async def send_message(self, msg: CoreMessage) -> None:
        """Send message to client via WebSocket."""
        await self.websocket.send_bytes(self._encoder.encode(msg))

    async def receive_message(self) -> CoreMessage:
        """Receive message from client via WebSocket."""
        data = await self.websocket.receive_bytes()
        return self._message_decoder.decode(data)

    async def handle_hello(self) -> str:
        """WebSocket-specific hello handshake.

        Returns:
            The session ID assigned to this connection
        """
        data = await self.websocket.receive_bytes()
        msg = self._hello_decoder.decode(data)

        if not isinstance(msg, HelloMessage):
            raise ValueError("Expected hello message")

        session_id = str(uuid4())
        response = HelloResponseMessage(
            session_id=session_id,
            server_version="0.1.0",
        )
        await self.websocket.send_bytes(self._encoder.encode(response))
        return session_id


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections."""
    await websocket.accept()

    # Get top component from app state
    top_component = websocket.app.state.trellis.top_component
    if top_component is None:
        await websocket.close(code=4000, reason="No top component configured")
        return

    handler = WebSocketMessageHandler(top_component, websocket)

    try:
        await handler.handle_hello()
        await handler.run()
    except WebSocketDisconnect:
        pass
    finally:
        handler.cleanup()
