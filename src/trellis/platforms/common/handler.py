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
import types
import typing as tp
from collections.abc import Callable
from importlib.metadata import version as get_package_version
from uuid import uuid4

from trellis.core.callback_context import callback_context
from trellis.core.components.base import Component
from trellis.core.protocol import dispatch, set_message_handler
from trellis.core.rendering.patches import (
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderUpdatePatch,
)
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession, get_session_registry, set_render_session
from trellis.core.rendering.ssr import execute_deferred_hooks
from trellis.html._generated_events import get_event_class
from trellis.platforms.common.errors import SessionDisconnected
from trellis.platforms.common.messages import (
    AddPatch,
    DebugConfig,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    KeyEventResponseMessage,
    Message,
    Patch,
    PatchMessage,
    RemovePatch,
    UpdatePatch,
)
from trellis.platforms.common.serialization import (
    _serialize_props,
    parse_callback_id,
    serialize_element,
)
from trellis.routing import RouterState
from trellis.routing.messages import HistoryBack, HistoryForward, HistoryPush
from trellis.utils.debug import get_enabled_categories

if tp.TYPE_CHECKING:
    from trellis.platforms.server.session_store import SessionStore

logger = logging.getLogger(__name__)
_DICT_ARG_COUNT = 2


def _get_version() -> str:
    """Get package version from metadata."""
    try:
        return get_package_version("trellis")
    except Exception:
        return "0.0.0"


__all__ = [
    "AppWrapper",
    "MessageHandler",
]


# Type alias for the app wrapper callback
# Takes (component, system_theme, theme_mode) and returns a wrapped component
AppWrapper = Callable[[Component, str, str | None], Component]


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

    return _coerce_dataclass_instance(arg, event_class)


def _resolve_nested_dataclass(annotation: tp.Any) -> type[tp.Any] | None:
    """Return nested dataclass type from an annotation if present."""
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        return annotation

    origin = tp.get_origin(annotation)
    if origin in (tp.Union, types.UnionType):
        for nested in tp.get_args(annotation):
            nested_dataclass = _resolve_nested_dataclass(nested)
            if nested_dataclass is not None:
                return nested_dataclass

    return None


def _coerce_typed_value(value: tp.Any, annotation: tp.Any) -> tp.Any:
    """Coerce nested event payload values based on dataclass field annotations."""
    nested_dataclass = _resolve_nested_dataclass(annotation)
    if nested_dataclass is not None and isinstance(value, dict):
        return _coerce_dataclass_instance(value, nested_dataclass)

    origin = tp.get_origin(annotation)
    if origin is list and isinstance(value, list):
        item_type = tp.get_args(annotation)[0] if tp.get_args(annotation) else tp.Any
        return [_coerce_typed_value(item, item_type) for item in value]

    if origin is dict and isinstance(value, dict):
        args = tp.get_args(annotation)
        value_type = args[1] if len(args) == _DICT_ARG_COUNT else tp.Any
        return {k: _coerce_typed_value(v, value_type) for k, v in value.items()}

    return value


def _coerce_dataclass_instance(data: dict[str, tp.Any], cls: type[tp.Any]) -> tp.Any:
    """Create a dataclass instance, recursively coercing nested dataclasses."""
    type_hints = tp.get_type_hints(cls)
    values: dict[str, tp.Any] = {}

    for field in dataclasses.fields(cls):
        if field.name not in data:
            continue
        annotation = type_hints.get(field.name, field.type)
        values[field.name] = _coerce_typed_value(data[field.name], annotation)

    return cls(**values)


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
        session: The RenderSession for callback registration and element lookup

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
                    element=serialize_element(patch.element, session),
                )
            )
        elif isinstance(patch, RenderUpdatePatch):
            # Serialize props if present
            props = None
            if patch.props is not None:
                props = _serialize_props(patch.props, session, patch.element_id)
            result.append(
                UpdatePatch(
                    id=patch.element_id,
                    props=props,
                    children=list(patch.children) if patch.children else None,
                )
            )
        elif isinstance(patch, RenderRemovePatch):
            result.append(RemovePatch(id=patch.element_id))
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

        handler = WebSocketMessageHandler(root_component, app_wrapper, websocket)
        await handler.run()
    """

    session: RenderSession | None
    session_id: str | None
    batch_delay: float
    message_send_queue: asyncio.Queue[Message]
    _root_component: Component
    _app_wrapper: AppWrapper
    _session_store: SessionStore | None
    _background_tasks: set[asyncio.Task[tp.Any]]
    _render_task: asyncio.Task[None] | None

    def __init__(
        self,
        root_component: Component,
        app_wrapper: AppWrapper,
        batch_delay: float = 1.0 / 30,
        session_store: SessionStore | None = None,
    ) -> None:
        """Create a new message handler.

        Args:
            root_component: The root Trellis component to render
            app_wrapper: Callback to wrap the component (e.g., with TrellisApp)
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
            session_store: Optional session store for SSR session resumption
        """
        self._root_component = root_component
        self._app_wrapper = app_wrapper
        self.session = None  # Created in handle_hello after receiving theme info
        self.session_id = None
        self.batch_delay = batch_delay
        self.message_send_queue = asyncio.Queue()
        self._session_store = session_store
        self._background_tasks = set()
        self._render_task = None

    async def handle_hello(self) -> str:
        """Handle hello handshake with client.

        Receives HelloMessage from client. If the message includes a session_id
        from SSR and it's found in the session store, the existing session is
        resumed and deferred hooks are executed. Otherwise, a new session is
        created.

        Returns:
            The generated or resumed session ID

        Raises:
            ValueError: If received message is not HelloMessage
        """
        msg = await self.receive_message()
        if not isinstance(msg, HelloMessage):
            raise ValueError(f"Expected HelloMessage, got {type(msg).__name__}")

        logger.debug("Hello from client_id=%s path=%s", msg.client_id, msg.path)

        # Try to resume an SSR session
        resumed = False
        if msg.session_id and self._session_store:
            entry = self._session_store.pop(msg.session_id)
            if entry is not None:
                self.session = entry.session
                self.session_id = msg.session_id
                get_session_registry().register(self.session)
                set_render_session(self.session)
                execute_deferred_hooks(self.session, entry.deferred_mounts, entry.deferred_unmounts)
                resumed = True
                logger.debug("Resumed SSR session: session_id=%s", self.session_id)

        if not resumed:
            # Create a new session
            wrapped = self._app_wrapper(
                self._root_component,
                msg.system_theme,  # "light" or "dark"
                msg.theme_mode,  # "system", "light", "dark", or None
            )
            self.session = RenderSession(wrapped)
            get_session_registry().register(self.session)
            set_render_session(self.session)
            self.session_id = str(uuid4())
            self.session.initial_path = msg.path

        # Include debug config if debug logging is enabled
        debug_categories = get_enabled_categories()
        debug_config = DebugConfig(categories=debug_categories) if debug_categories else None

        assert self.session_id is not None
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

        If the session was already rendered by SSR (root_element_id is set),
        skips rendering and returns empty patches. Otherwise performs a full
        initial render. Sets up router callbacks in both cases.


        Returns:
            PatchMessage on success, ErrorMessage on exception
        """
        assert self.session is not None, "handle_hello must be called before initial_render"
        try:
            if self.session.root_element_id is not None:
                # Already rendered by SSR — skip render, just set up router
                logger.debug("Skipping initial render (SSR session)")
                self._setup_router_callbacks()
                return PatchMessage(patches=[])

            render_patches = render(self.session)
            wire_patches = _serialize_patches(render_patches, self.session)
            element_count = len(self.session.elements)
            logger.debug(
                "Initial render complete, sending PatchMessage (%d elements)", element_count
            )

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

            # Callback executed successfully. State changes mark elements dirty.
            # The render loop will pick them up on the next frame.
            return None

        await dispatch(msg)
        return None

    def _handle_url_changed(self, path: str) -> None:
        """Handle browser URL change (popstate event).

        Finds RouterState in the session and updates its path.
        """
        router_state = self._find_router_state()
        if router_state is not None:
            router_state._update_path_from_url(path)

    def _find_router_state(self) -> tp.Any:
        """Find RouterState instance in session's element states.

        Note: While this search is technically O(N) in the number of elements,
        RouterState is typically placed on the root TrellisApp element, so in
        practice it completes in O(1) as it's found immediately.

        Returns:
            RouterState instance or None if not found
        """
        if self.session is None:
            return None

        # Search through element states for RouterState in context
        for element_id in self.session.states._state:
            state = self.session.states.get(element_id)
            if state is not None and RouterState in state.context:
                return state.context[RouterState]
        return None

    def _setup_router_callbacks(self) -> None:
        """Set up async callbacks on RouterState to send history messages."""
        router_state = self._find_router_state()
        if router_state is None:
            return

        async def on_navigate(path: str) -> None:
            await self.send_message(HistoryPush(path=path))

        async def on_go_back() -> None:
            await self.send_message(HistoryBack())

        async def on_go_forward() -> None:
            await self.send_message(HistoryForward())

        router_state._on_navigate = on_navigate
        router_state._on_go_back = on_go_back
        router_state._on_go_forward = on_go_forward

    def _is_key_event_callback(self, prop_name: str) -> bool:
        """Check if a callback prop path is a key event handler."""
        return prop_name.startswith("__key_filters__") or prop_name.startswith(
            "__global_key_filters__"
        )

    async def _invoke_callback(self, callback_id: str, args: list[tp.Any]) -> None:
        """Invoke callback with event conversion.

        Args:
            callback_id: The callback ID to invoke (format: element_id|prop_name)
            args: Raw arguments from the client

        Raises:
            KeyError: If callback not found
        """
        assert self.session is not None
        session = self.session  # Local var for closure capture
        element_id, prop_name = parse_callback_id(callback_id)
        callback = session.get_callback(element_id, prop_name)
        if callback is None:
            raise KeyError(f"Callback not found: {callback_id}")

        # Key event callbacks use a request-response protocol:
        # first arg is request_id, handler return value determines handled status.
        if self._is_key_event_callback(prop_name):
            await self._invoke_key_callback(callback_id, element_id, callback, args)
            return

        processed_args, kwargs = _process_callback_args(args)
        logger.debug("Invoking callback %s with %d args", callback_id, len(processed_args))

        if inspect.iscoroutinefunction(callback):
            # Async: wrap to provide callback context
            async def run_async_with_context() -> None:
                with callback_context(session, element_id):
                    await callback(*processed_args, **kwargs)

            logger.debug("Callback %s is async, scheduled as task", callback_id)
            session.spawn(
                run_async_with_context(),
                label=f"callback {callback_id}",
            )
        else:
            # Sync: call with callback context
            with callback_context(session, element_id):
                callback(*processed_args, **kwargs)

    async def _invoke_key_callback(
        self,
        callback_id: str,
        element_id: str,
        callback: tp.Callable[..., tp.Any],
        args: list[tp.Any],
    ) -> None:
        """Invoke a key event callback and send handled/pass response.

        Key event args: [request_id, ...event_data]
        Handler return: True/None = handled, False = pass
        """
        assert self.session is not None
        session = self.session

        if not args:
            logger.warning("Key event callback %s received no args", callback_id)
            return

        request_id = args[0]
        handler_args = args[1:]
        processed_args, kwargs = _process_callback_args(handler_args)

        # Only pass event args if the handler accepts them — most key handlers
        # take zero args and would TypeError if given the keyboard event.
        try:
            sig = inspect.signature(callback)
            accepts_args = any(
                p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)
                for p in sig.parameters.values()
            )
        except (ValueError, TypeError):
            accepts_args = True

        call_args = processed_args if accepts_args else []
        call_kwargs = kwargs if accepts_args else {}

        handled = True
        try:
            with callback_context(session, element_id):
                if inspect.iscoroutinefunction(callback):
                    result = await callback(*call_args, **call_kwargs)
                else:
                    result = callback(*call_args, **call_kwargs)
            # None or True = handled, False = pass
            if result is False:
                handled = False
        except Exception:
            logger.exception("Error in key callback %s", callback_id)
            handled = False

        await self.send_message(KeyEventResponseMessage(request_id=request_id, handled=handled))

    # -------------------------------------------------------------------------
    # Render loop - batches updates at 30fps
    # -------------------------------------------------------------------------

    async def _render_loop(self) -> None:
        """Background loop that renders when dirty elements exist.

        This loop runs continuously, sleeping for the configured batch_delay,
        then checking if any elements need re-rendering. If so, it renders
        and sends patches to the client.
        """
        assert self.session is not None
        while True:
            # Wait for frame period (configured via batch_delay)
            await asyncio.sleep(self.batch_delay)

            # Check if there are dirty elements to render
            if not self.session.dirty.has_dirty():
                continue

            dirty_count = len(self.session.dirty)
            logger.debug("Render loop: %d dirty elements", dirty_count)

            try:
                render_patches = render(self.session)
            except Exception as e:
                try:
                    await self.send_message(
                        ErrorMessage(error=_format_exception(e), context="render")
                    )
                except Exception:
                    logger.exception("Error sending render failure message")
                raise

            if not render_patches:
                continue

            wire_patches = _serialize_patches(render_patches, self.session)
            logger.debug("Sending PatchMessage with %d patches", len(wire_patches))
            await self.send_message(PatchMessage(patches=wire_patches))

    async def _drain_message_send_queue(self) -> None:
        """Send queued protocol messages over the transport."""
        while True:
            message = await self.message_send_queue.get()
            await self.send_message(message)

    # -------------------------------------------------------------------------
    # Transport methods - subclasses must override
    # -------------------------------------------------------------------------

    async def send_message(self, msg: Message) -> None:
        """Send message to client. Override in subclass."""
        raise NotImplementedError

    async def receive_message(self) -> Message:
        """Receive message from client. Override in subclass."""
        raise NotImplementedError

    async def _receive_message_or_critical(
        self, critical_tasks: set[asyncio.Task[tp.Any]]
    ) -> Message | None:
        """Wait for the next client message or a critical task completion."""
        receive_task = asyncio.create_task(self.receive_message())
        tasks = set(critical_tasks)
        tasks.add(receive_task)

        try:
            done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except BaseException:
            receive_task.cancel()
            await asyncio.gather(receive_task, return_exceptions=True)
            raise

        if any(task in done for task in critical_tasks):
            receive_task.cancel()
            await asyncio.gather(receive_task, return_exceptions=True)
            for task in critical_tasks:
                if task not in done:
                    continue
                try:
                    task.result()
                except SessionDisconnected:
                    return None
                except Exception:
                    logger.exception("Critical handler task failed")
                    return None
                logger.error("Critical handler task exited unexpectedly")
                return None

        return receive_task.result()

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
        try:
            set_message_handler(self)
            await self.handle_hello()
            await self.send_message(self.initial_render())
            assert self.session is not None

            critical_tasks = {
                asyncio.create_task(self._render_loop()),
                asyncio.create_task(self._drain_message_send_queue()),
            }

            while True:
                msg = await self._receive_message_or_critical(critical_tasks)
                if msg is None:
                    break

                response = await self.handle_message(msg)
                if response:
                    await self.send_message(response)
        except SessionDisconnected:
            return
        finally:
            critical_tasks = locals().get("critical_tasks", set())
            for task in critical_tasks:
                task.cancel()
            if critical_tasks:
                await asyncio.gather(*critical_tasks, return_exceptions=True)
            if self.session is not None:
                await self.session.shutdown()

    def cleanup(self) -> None:
        """Clean up resources. Call when session ends."""
        # No explicit cleanup needed - callbacks are stored in element props
        # and cleaned up when elements are unmounted
        pass
