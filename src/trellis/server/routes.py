"""FastAPI routes for Trellis server."""

from pathlib import Path
from uuid import uuid4

import msgspec
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from trellis.core.rendering import RenderContext
from trellis.core.serialization import (
    clear_callbacks,
    get_callback,
    serialize_element,
)
from trellis.server.messages import (
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    RenderMessage,
)

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
    <style>
        *, *::before, *::after {{ box-sizing: border-box; }}
        html, body, #root {{ margin: 0; padding: 0; height: 100%; }}
    </style>
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
    ctx: RenderContext | None = None

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

        # Render and send the component tree if a top component is configured
        top_component = getattr(websocket.app.state, "top_component", None)
        if top_component is not None:
            # Clear stale callbacks from previous renders
            clear_callbacks()

            # Perform initial render
            ctx = RenderContext(top_component)
            ctx.render(from_element=None)

            # Serialize the tree and send to client
            assert ctx.root_element is not None
            tree_data = serialize_element(ctx.root_element)
            render_msg = RenderMessage(tree=tree_data)
            await websocket.send_bytes(_encoder.encode(render_msg))

        # Handle messages (events, etc.)
        while True:
            data = await websocket.receive_bytes()
            msg = _decoder.decode(data)

            if isinstance(msg, EventMessage) and ctx is not None:
                # Look up and invoke the callback
                callback = get_callback(msg.callback_id)
                if callback is not None:
                    callback(*msg.args)

                    # Re-render dirty elements and send updated tree
                    clear_callbacks()
                    ctx.render_dirty()
                    assert ctx.root_element is not None
                    tree_data = serialize_element(ctx.root_element)
                    render_msg = RenderMessage(tree=tree_data)
                    await websocket.send_bytes(_encoder.encode(render_msg))

    except WebSocketDisconnect:
        pass


def create_static_dir() -> Path:
    """Get or create the static files directory."""
    static_dir = Path(__file__).parent.parent / "client" / "dist"
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
