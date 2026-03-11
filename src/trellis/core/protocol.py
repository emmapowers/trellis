"""Core protocol registry and handler-scoped messaging helpers."""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import typing as tp
import weakref
from collections import defaultdict

import msgspec

F = tp.TypeVar("F", bound=tp.Callable[..., tp.Any])
Listener = tp.Callable[["MessageHandlerProtocol", object], tp.Awaitable[None]]

_LISTEN_ATTR = "__trellis_listen_types__"
_handler_ctx: contextvars.ContextVar[MessageHandlerProtocol | None] = contextvars.ContextVar(
    "message_handler", default=None
)
_MESSAGE_TYPES: dict[str, type[object]] = {}
_MESSAGE_TAGS: dict[type[object], str] = {}
_GLOBAL_LISTENERS: dict[type[object], list[Listener]] = defaultdict(list)
_HANDLER_LISTENERS: weakref.WeakKeyDictionary[
    object, dict[type[object], list[Listener]]
] = weakref.WeakKeyDictionary()


@tp.runtime_checkable
class MessageHandlerProtocol(tp.Protocol):
    """Core interface exposed to protocol listeners and senders."""

    message_send_queue: asyncio.Queue[object]


def get_message_handler() -> MessageHandlerProtocol | None:
    """Return the message handler bound to the current async context."""
    return _handler_ctx.get()


def set_message_handler(handler: MessageHandlerProtocol | None) -> None:
    """Bind a message handler to the current async context."""
    _handler_ctx.set(handler)


def register_message_types(*message_types: type[msgspec.Struct]) -> None:
    """Register extension message types by their msgspec tag."""
    for message_type in message_types:
        config = message_type.__struct_config__
        if config.tag is None or not isinstance(config.tag, str):
            raise TypeError(
                f"{message_type.__name__} must define a string msgspec tag to register."
            )
        _MESSAGE_TYPES[config.tag] = message_type
        _MESSAGE_TAGS[message_type] = config.tag


def decode_registered_message(payload: object) -> object | None:
    """Decode an extension message from a builtins payload if it is registered."""
    if not isinstance(payload, dict):
        return None

    tag = payload.get("type")
    if not isinstance(tag, str):
        return None

    message_type = _MESSAGE_TYPES.get(tag)
    if message_type is None:
        return None

    return msgspec.convert(payload, message_type)


def listen(*message_types: type[object]) -> tp.Callable[[F], F]:
    """Register a listener or mark an instance method for later registration."""

    def decorator(fn: F) -> F:
        if _looks_like_method(fn):
            setattr(fn, _LISTEN_ATTR, message_types)
            return fn

        handler = get_message_handler()
        for message_type in message_types:
            _register_listener(message_type, tp.cast("Listener", fn), handler)
        return fn

    return decorator


class MessageListener:
    """Base class for objects with handler-scoped protocol listeners."""

    _message_listener_registrations: list[tuple[MessageHandlerProtocol, type[object], Listener]]
    _message_listener_handler: MessageHandlerProtocol | None

    def __init__(self) -> None:
        self._message_listener_registrations = []
        self._message_listener_handler = None
        handler = get_message_handler()
        if handler is not None:
            self.register_message_listeners(handler)

    def register_message_listeners(
        self, handler: MessageHandlerProtocol | None = None
    ) -> None:
        """Attach bound listeners for this object to the target handler."""
        if handler is None:
            handler = get_message_handler()
        if handler is None:
            return
        if self._message_listener_handler is handler and self._message_listener_registrations:
            return
        if self._message_listener_registrations:
            self.unregister_message_listeners()

        for name in dir(type(self)):
            descriptor = getattr(type(self), name, None)
            message_types = getattr(descriptor, _LISTEN_ATTR, None)
            if not message_types:
                continue

            listener = tp.cast("Listener", getattr(self, name))
            for message_type in message_types:
                _register_listener(message_type, listener, handler)
                self._message_listener_registrations.append((handler, message_type, listener))
        self._message_listener_handler = handler

    def unregister_message_listeners(self) -> None:
        """Detach any handler-scoped listeners previously registered by this object."""
        for handler, message_type, listener in self._message_listener_registrations:
            _unregister_listener(message_type, listener, handler)
        self._message_listener_registrations.clear()
        self._message_listener_handler = None


async def send(message: object) -> None:
    """Enqueue a message for the current handler."""
    handler = get_message_handler()
    if handler is None:
        raise RuntimeError("No active message handler is available for send().")
    await handler.message_send_queue.put(message)


async def dispatch(handler: MessageHandlerProtocol, message: object) -> None:
    """Dispatch a decoded message to global and handler-scoped listeners."""
    previous = get_message_handler()
    set_message_handler(handler)
    try:
        for listener in _GLOBAL_LISTENERS.get(type(message), ()):
            await listener(handler, message)

        scoped = _HANDLER_LISTENERS.get(handler)
        if scoped is None:
            return
        for listener in scoped.get(type(message), ()):
            await listener(handler, message)
    finally:
        set_message_handler(previous)


def _register_listener(
    message_type: type[object],
    listener: Listener,
    handler: MessageHandlerProtocol | None,
) -> None:
    listeners = (
        _GLOBAL_LISTENERS[message_type]
        if handler is None
        else _HANDLER_LISTENERS.setdefault(handler, {}).setdefault(message_type, [])
    )
    if any(existing == listener for existing in listeners):
        return
    listeners.append(listener)


def _unregister_listener(
    message_type: type[object],
    listener: Listener,
    handler: MessageHandlerProtocol | None,
) -> None:
    listeners = (
        _GLOBAL_LISTENERS.get(message_type)
        if handler is None
        else _HANDLER_LISTENERS.get(handler, {}).get(message_type)
    )
    if not listeners:
        return

    remaining = [existing for existing in listeners if existing != listener]
    if handler is None:
        if remaining:
            _GLOBAL_LISTENERS[message_type] = remaining
        else:
            _GLOBAL_LISTENERS.pop(message_type, None)
        return

    scoped = _HANDLER_LISTENERS.get(handler)
    if scoped is None:
        return
    if remaining:
        scoped[message_type] = remaining
    else:
        scoped.pop(message_type, None)
    if not scoped:
        _HANDLER_LISTENERS.pop(handler, None)


def _looks_like_method(fn: tp.Callable[..., tp.Any]) -> bool:
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError):
        return False
    if not params:
        return False
    first = params[0]
    return first.kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ) and first.name == "self"


def _reset_for_tests() -> None:
    """Reset protocol registries and context for isolated tests."""
    _GLOBAL_LISTENERS.clear()
    _HANDLER_LISTENERS.clear()
    _handler_ctx.set(None)
