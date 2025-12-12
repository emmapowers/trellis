"""FastAPI routes for Trellis server."""

from __future__ import annotations

import asyncio
import dataclasses
import inspect
import logging
import typing as tp
from pathlib import Path
from uuid import uuid4

import msgspec
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from trellis.core.rendering import RenderTree
from trellis.html.events import (
    BaseEvent,
    ChangeEvent,
    FocusEvent,
    FormEvent,
    InputEvent,
    KeyboardEvent,
    MouseEvent,
)
from trellis.server.messages import (
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    RenderMessage,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Event type mapping
# =============================================================================

# Map event type strings to their corresponding dataclasses
EVENT_TYPE_MAP: dict[str, type[BaseEvent]] = {
    # Mouse events
    "click": MouseEvent,
    "dblclick": MouseEvent,
    "mousedown": MouseEvent,
    "mouseup": MouseEvent,
    "mousemove": MouseEvent,
    "mouseenter": MouseEvent,
    "mouseleave": MouseEvent,
    "mouseover": MouseEvent,
    "mouseout": MouseEvent,
    "contextmenu": MouseEvent,
    # Keyboard events
    "keydown": KeyboardEvent,
    "keyup": KeyboardEvent,
    "keypress": KeyboardEvent,
    # Form events
    "change": ChangeEvent,
    "input": InputEvent,
    "focus": FocusEvent,
    "blur": FocusEvent,
    "submit": FormEvent,
}


# =============================================================================
# Callback argument processing
# =============================================================================


def _extract_args_kwargs(args: list[tp.Any]) -> tuple[list[tp.Any], dict[str, tp.Any]]:
    """Extract positional args and kwargs from callback args.

    Convention: last arg can be {'__kwargs__': True, key: value, ...}
    to pass keyword arguments to the callback.

    Args:
        args: List of arguments from the client

    Returns:
        Tuple of (positional_args, keyword_args)
    """
    if not args:
        return [], {}

    last = args[-1]
    if isinstance(last, dict) and last.get("__kwargs__") is True:
        kwargs = {k: v for k, v in last.items() if k != "__kwargs__"}
        return list(args[:-1]), kwargs

    return list(args), {}


def _convert_event_arg(arg: tp.Any) -> tp.Any:
    """Convert serialized event dict to appropriate dataclass.

    If the arg looks like an event (has a 'type' field), convert it to
    the corresponding event dataclass. Otherwise return as-is.

    Args:
        arg: An argument that may be a serialized event

    Returns:
        Event dataclass if arg is an event, otherwise the original arg
    """
    if not isinstance(arg, dict) or "type" not in arg:
        return arg

    event_type = arg.get("type", "")
    event_class = EVENT_TYPE_MAP.get(event_type, BaseEvent)

    # Filter to only fields the dataclass accepts
    valid_fields = {f.name for f in dataclasses.fields(event_class)}
    filtered = {k: v for k, v in arg.items() if k in valid_fields}

    return event_class(**filtered)


def _process_callback_args(
    args: list[tp.Any],
) -> tuple[list[tp.Any], dict[str, tp.Any]]:
    """Process callback arguments: convert events and extract kwargs.

    Args:
        args: Raw arguments from the client

    Returns:
        Tuple of (processed_positional_args, keyword_args)
    """
    # First extract kwargs
    positional, kwargs = _extract_args_kwargs(args)

    # Then convert any event args
    converted = [_convert_event_arg(arg) for arg in positional]

    return converted, kwargs


router = APIRouter()

# Encoder/decoder for msgpack - reused for efficiency
_encoder = msgspec.msgpack.Encoder()
_decoder = msgspec.msgpack.Decoder(Message)

# Set to hold background tasks and prevent garbage collection
_background_tasks: set[asyncio.Task[tp.Any]] = set()


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
    ctx: RenderTree | None = None

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
            ctx = RenderTree(top_component)
            try:
                tree_data = ctx.render()
            except Exception as e:
                logger.exception(f"Error during initial render: {e}")
                await websocket.close(code=4001, reason="Render error")
                return

            render_msg = RenderMessage(tree=tree_data)
            await websocket.send_bytes(_encoder.encode(render_msg))

        # Handle messages (events, etc.)
        while True:
            data = await websocket.receive_bytes()
            msg = _decoder.decode(data)

            if isinstance(msg, EventMessage) and ctx is not None:
                # Look up and invoke the callback (callbacks stored on ctx)
                callback = ctx.get_callback(msg.callback_id)
                if callback is not None:
                    # Process args: convert events and extract kwargs
                    args, kwargs = _process_callback_args(msg.args)

                    # Invoke callback with error handling to prevent connection crash
                    try:
                        if inspect.iscoroutinefunction(callback):
                            # Async callback - schedule with create_task
                            task = asyncio.create_task(callback(*args, **kwargs))
                            # Store reference to prevent garbage collection
                            _background_tasks.add(task)
                            task.add_done_callback(_background_tasks.discard)
                        else:
                            # Sync callback - call directly
                            callback(*args, **kwargs)
                    except Exception as e:
                        logger.exception(f"Error in callback {msg.callback_id}: {e}")
                        # Continue processing - don't crash the connection
                        continue

                    # Re-render dirty elements and send updated tree
                    try:
                        tree_data = ctx.render()
                        render_msg = RenderMessage(tree=tree_data)
                        await websocket.send_bytes(_encoder.encode(render_msg))
                    except Exception as e:
                        logger.exception(f"Error during render after callback: {e}")
                        # Continue processing - connection may recover

    except WebSocketDisconnect:
        pass
    finally:
        # Clean up callbacks associated with this session
        if ctx is not None:
            ctx.clear_callbacks()


def create_static_dir() -> Path:
    """Get or create the static files directory."""
    static_dir = Path(__file__).parent.parent / "client" / "dist"
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
