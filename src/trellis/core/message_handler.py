"""Base message handler for Trellis communication.

Provides the core render/event/re-render loop shared by all backends.
Transport-specific subclasses implement send_message/receive_message.
"""

from __future__ import annotations

import asyncio
import dataclasses
import inspect
import logging
import traceback
import typing as tp
from uuid import uuid4

from trellis.core.components.base import Component
from trellis.core.messages import (
    AddPatch,
    DebugConfig,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    Patch,
    PatchMessage,
    RemovePatch,
    UpdatePatch,
)
from trellis.core.rendering.patches import (
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderUpdatePatch,
)
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.serialization import _serialize_node_props, serialize_node
from trellis.html.events import get_event_class
from trellis.utils.debug import get_enabled_categories

logger = logging.getLogger(__name__)


def _get_version() -> str:
    """Get package version from metadata."""
    from importlib.metadata import version

    try:
        return version("trellis")
    except Exception:
        return "0.0.0"


__all__ = [
    "MessageHandler",
]


# =============================================================================
# Exception formatting
# =============================================================================


def _format_exception(e: BaseException) -> str:
    """Format an exception as a string with traceback."""
    return "".join(traceback.format_exception(type(e), e, e.__traceback__))


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
    event_class = get_event_class(event_type)

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


# =============================================================================
# Patch serialization
# =============================================================================


def _serialize_patches(patches: list[RenderPatch], session: RenderSession) -> list[Patch]:
    """Convert render patches to wire-format patches.

    This is where serialization happens - at the protocol boundary,
    not during rendering.

    Args:
        patches: List of RenderPatch objects from render()
        session: The RenderSession for callback registration and node lookup

    Returns:
        List of wire-format Patch objects ready for transmission
    """
    result: list[Patch] = []
    for patch in patches:
        if isinstance(patch, RenderAddPatch):
            result.append(
                AddPatch(
                    parent_id=patch.parent_id,
                    children=list(patch.children),
                    node=serialize_node(patch.node, session),
                )
            )
        elif isinstance(patch, RenderUpdatePatch):
            # Only serialize props if they changed
            props = None
            if patch.props_changed:
                node = session.nodes.get(patch.node_id)
                if node:
                    props = _serialize_node_props(node, session)
            result.append(
                UpdatePatch(
                    id=patch.node_id,
                    props=props,
                    children=list(patch.children) if patch.children else None,
                )
            )
        elif isinstance(patch, RenderRemovePatch):
            result.append(RemovePatch(id=patch.node_id))
    return result


# =============================================================================
# MessageHandler base class
# =============================================================================


class MessageHandler:
    """Base message handler - core loop shared by all backends.

    Subclasses implement transport-specific send_message/receive_message.

    Example:
        class WebSocketMessageHandler(MessageHandler):
            async def send_message(self, msg: Message) -> None:
                await self.websocket.send_bytes(encode(msg))

            async def receive_message(self) -> Message:
                return decode(await self.websocket.receive_bytes())

        handler = WebSocketMessageHandler(root_component, websocket)
        await handler.run()
    """

    session: RenderSession
    session_id: str | None
    batch_delay: float
    _background_tasks: set[asyncio.Task[tp.Any]]
    _render_task: asyncio.Task[None] | None

    def __init__(
        self,
        root_component: Component,
        batch_delay: float = 1.0 / 30,
    ) -> None:
        """Create a new message handler.

        Args:
            root_component: The root Trellis component to render
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
        """
        self.session = RenderSession(root_component)
        self.session_id = None
        self.batch_delay = batch_delay
        self._background_tasks = set()
        self._render_task = None

    async def handle_hello(self) -> str:
        """Handle hello handshake with client.

        Receives HelloMessage from client, generates session ID,
        and sends HelloResponseMessage. All platforms use this
        handshake for session initialization.

        Returns:
            The generated session ID

        Raises:
            ValueError: If received message is not HelloMessage
        """
        msg = await self.receive_message()
        if not isinstance(msg, HelloMessage):
            raise ValueError(f"Expected HelloMessage, got {type(msg).__name__}")

        logger.debug("Hello from client_id=%s", msg.client_id)

        self.session_id = str(uuid4())

        # Include debug config if debug logging is enabled
        debug_categories = get_enabled_categories()
        debug_config = DebugConfig(categories=debug_categories) if debug_categories else None

        response = HelloResponseMessage(
            session_id=self.session_id,
            server_version=_get_version(),
            debug=debug_config,
        )
        await self.send_message(response)
        logger.debug("Session initialized: session_id=%s", self.session_id)
        return self.session_id

    def initial_render(self) -> Message:
        """Generate initial render message.

        Returns:
            PatchMessage on success, ErrorMessage on exception
        """
        try:
            render_patches = render(self.session)
            wire_patches = _serialize_patches(render_patches, self.session)
            node_count = len(self.session.nodes)
            logger.debug("Initial render complete, sending PatchMessage (%d nodes)", node_count)
            return PatchMessage(patches=wire_patches)
        except Exception as e:
            logger.exception(f"Error during initial render: {e}")
            return ErrorMessage(error=_format_exception(e), context="render")

    async def handle_message(self, msg: Message) -> Message | None:
        """Process incoming message, return response message.

        Args:
            msg: The incoming message to process

        Returns:
            ErrorMessage on callback error, or None. Re-rendering is handled
            by the background render loop, not per-message.
        """
        if isinstance(msg, EventMessage):
            logger.debug("Received EventMessage: callback_id=%s", msg.callback_id)
            try:
                await self._invoke_callback(msg.callback_id, msg.args)
            except KeyError as e:
                logger.exception(f"Unknown callback: {msg.callback_id}")
                return ErrorMessage(error=_format_exception(e), context="callback")
            except Exception as e:
                logger.exception(f"Error in callback {msg.callback_id}: {e}")
                return ErrorMessage(error=_format_exception(e), context="callback")

            # Callback executed successfully. State changes mark nodes dirty.
            # The render loop will pick them up on the next frame.
            return None

        return None

    async def _invoke_callback(self, callback_id: str, args: list[tp.Any]) -> None:
        """Invoke callback with event conversion.

        Args:
            callback_id: The callback ID to invoke (format: node_id|prop_name)
            args: Raw arguments from the client

        Raises:
            KeyError: If callback not found
        """
        from trellis.core.serialization import parse_callback_id

        node_id, prop_name = parse_callback_id(callback_id)
        callback = self.session.get_callback(node_id, prop_name)
        if callback is None:
            raise KeyError(f"Callback not found: {callback_id}")

        processed_args, kwargs = _process_callback_args(args)
        logger.debug("Invoking callback %s with %d args", callback_id, len(processed_args))

        if inspect.iscoroutinefunction(callback):
            # Async: fire-and-forget
            logger.debug("Callback %s is async, scheduled as task", callback_id)
            task = asyncio.create_task(callback(*processed_args, **kwargs))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        else:
            # Sync: call directly
            callback(*processed_args, **kwargs)

    # -------------------------------------------------------------------------
    # Render loop - batches updates at 30fps
    # -------------------------------------------------------------------------

    async def _render_loop(self) -> None:
        """Background loop that renders when dirty nodes exist.

        This loop runs continuously, sleeping for the configured batch_delay,
        then checking if any nodes need re-rendering. If so, it renders
        and sends patches to the client.
        """
        while True:
            # Wait for frame period (configured via batch_delay)
            await asyncio.sleep(self.batch_delay)

            # Check if there are dirty nodes to render
            if not self.session.dirty.has_dirty():
                continue

            dirty_count = len(self.session.dirty)
            logger.debug("Render loop: %d dirty nodes", dirty_count)

            try:
                render_patches = render(self.session)
                if render_patches:
                    wire_patches = _serialize_patches(render_patches, self.session)
                    logger.debug("Sending PatchMessage with %d patches", len(wire_patches))
                    await self.send_message(PatchMessage(patches=wire_patches))
            except Exception as e:
                logger.exception(f"Error in render loop: {e}")
                await self.send_message(ErrorMessage(error=_format_exception(e), context="render"))

    # -------------------------------------------------------------------------
    # Transport methods - subclasses must override
    # -------------------------------------------------------------------------

    async def send_message(self, msg: Message) -> None:
        """Send message to client. Override in subclass."""
        raise NotImplementedError

    async def receive_message(self) -> Message:
        """Receive message from client. Override in subclass."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    async def run(self) -> None:
        """Main message loop - hello, initial render, then event loop.

        1. Performs hello handshake with client
        2. Sends initial render (full tree)
        3. Starts background render loop (30fps batched updates)
        4. Loops receiving messages and sending responses
        """
        await self.handle_hello()
        await self.send_message(self.initial_render())

        # Start background render loop for batched updates
        self._render_task = asyncio.create_task(self._render_loop())

        try:
            while True:
                msg = await self.receive_message()
                response = await self.handle_message(msg)
                if response:
                    await self.send_message(response)
        finally:
            # Cancel render loop on disconnect
            if self._render_task:
                self._render_task.cancel()
                try:
                    await self._render_task
                except asyncio.CancelledError:
                    pass

    def cleanup(self) -> None:
        """Clean up resources. Call when session ends."""
        # No explicit cleanup needed - callbacks are stored in node props
        # and cleaned up when nodes are unmounted
        pass
