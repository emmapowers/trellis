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

from trellis.core.messages import ErrorMessage, EventMessage, Message, RenderMessage
from trellis.core.rendering import IComponent, RenderTree
from trellis.html.events import get_event_class

logger = logging.getLogger(__name__)

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

    tree: RenderTree
    _background_tasks: set[asyncio.Task[tp.Any]]

    def __init__(self, root_component: IComponent) -> None:
        """Create a new message handler.

        Args:
            root_component: The root Trellis component to render
        """
        self.tree = RenderTree(root_component)
        self._background_tasks = set()

    def initial_render(self) -> Message:
        """Generate initial render message.

        Returns:
            RenderMessage on success, ErrorMessage on exception
        """
        try:
            return RenderMessage(tree=self.tree.render())
        except Exception as e:
            logger.exception(f"Error during initial render: {e}")
            return ErrorMessage(error=_format_exception(e), context="render")

    async def handle_message(self, msg: Message) -> Message | None:
        """Process incoming message, return response message.

        Args:
            msg: The incoming message to process

        Returns:
            Response message (RenderMessage or ErrorMessage), or None if no response
        """
        if isinstance(msg, EventMessage):
            try:
                await self._invoke_callback(msg.callback_id, msg.args)
            except KeyError as e:
                logger.exception(f"Unknown callback: {msg.callback_id}")
                return ErrorMessage(error=_format_exception(e), context="callback")
            except Exception as e:
                logger.exception(f"Error in callback {msg.callback_id}: {e}")
                return ErrorMessage(error=_format_exception(e), context="callback")

            # Re-render and return updated tree
            try:
                return RenderMessage(tree=self.tree.render())
            except Exception as e:
                logger.exception(f"Error during render after callback: {e}")
                return ErrorMessage(error=_format_exception(e), context="render")

        return None

    async def _invoke_callback(self, callback_id: str, args: list[tp.Any]) -> None:
        """Invoke callback with event conversion.

        Args:
            callback_id: The callback ID to invoke
            args: Raw arguments from the client

        Raises:
            KeyError: If callback not found
        """
        callback = self.tree.get_callback(callback_id)
        if callback is None:
            raise KeyError(f"Callback not found: {callback_id}")

        processed_args, kwargs = _process_callback_args(args)

        if inspect.iscoroutinefunction(callback):
            # Async: fire-and-forget
            task = asyncio.create_task(callback(*processed_args, **kwargs))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        else:
            # Sync: call directly
            callback(*processed_args, **kwargs)

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
        """Main message loop - receive, handle, send.

        Sends initial render, then loops receiving messages and
        sending responses.
        """
        await self.send_message(self.initial_render())

        while True:
            msg = await self.receive_message()
            response = await self.handle_message(msg)
            if response:
                await self.send_message(response)

    def cleanup(self) -> None:
        """Clean up callbacks. Call when session ends."""
        self.tree.clear_callbacks()
