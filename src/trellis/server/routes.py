"""FastAPI routes for Trellis server."""

from pathlib import Path
from uuid import uuid4

import msgspec
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from trellis.server.messages import HelloMessage, HelloResponseMessage, Message

router = APIRouter()

# Encoder/decoder for msgpack - reused for efficiency
_encoder = msgspec.msgpack.Encoder()
_decoder = msgspec.msgpack.Decoder(Message)


def get_index_html(static_path: str = "/static") -> str:
    """Generate the HTML page that loads the React app."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Trellis App</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="{static_path}/bundle.js"></script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Serve the main HTML page."""
    return get_index_html()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections."""
    await websocket.accept()

    try:
        # Wait for hello message
        data = await websocket.receive_bytes()
        msg = _decoder.decode(data)

        if not isinstance(msg, HelloMessage):
            await websocket.close(code=4000, reason="Expected hello message")
            return

        # Send hello response
        session_id = str(uuid4())
        response = HelloResponseMessage(
            session_id=session_id,
            server_version="0.1.0",
        )
        await websocket.send_bytes(_encoder.encode(response))

        # Keep connection open for future messages
        while True:
            data = await websocket.receive_bytes()
            # Future: handle other message types
            _ = _decoder.decode(data)

    except WebSocketDisconnect:
        pass


def create_static_dir() -> Path:
    """Get or create the static files directory."""
    static_dir = Path(__file__).parent.parent / "client" / "dist"
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
