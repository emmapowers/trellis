"""Core protocol registry and handler-scoped messaging helpers."""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import typing as tp
import weakref
from collections import defaultdict
from dataclasses import dataclass

import msgspec

F = tp.TypeVar("F", bound=tp.Callable[..., tp.Any])
Listener = tp.Callable[["MessageHandlerProtocol", object], tp.Awaitable[None]]

_LISTEN_ATTR = "__trellis_listen_types__"
_handler_ctx: contextvars.ContextVar[MessageHandlerProtocol | None] = contextvars.ContextVar(
    "message_handler", default=None
)
_MESSAGE_TYPES: dict[str, type[object]] = {}
_MESSAGE_TAGS: dict[type[object], str] = {}
_GLOBAL_LISTENERS: dict[type[object], list[_ListenerRef]] = defaultdict(list)
_HANDLER_LISTENERS: weakref.WeakKeyDictionary[object, dict[type[object], list[_ListenerRef]]] = (
    weakref.WeakKeyDictionary()
)


@dataclass(frozen=True)
class _ListenerRef:
    """Weakly-reference bound methods while leaving plain functions untouched."""

    function: Listener | None = None
    method: weakref.WeakMethod[tp.Any] | None = None

    @classmethod
    def from_listener(cls, listener: Listener) -> _ListenerRef:
        if inspect.ismethod(listener):
            return cls(method=weakref.WeakMethod(listener))
        return cls(function=listener)

    def resolve(self) -> Listener | None:
        if self.function is not None:
            return self.function
        if self.method is None:
            return None
        return tp.cast("Listener | None", self.method())


class Message(msgspec.Struct, tag_field="type"):
    """Base class for all top-level protocol messages."""


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
    """Register protocol message types by their msgspec tag."""
    for message_type in message_types:
        if not issubclass(message_type, Message):
            raise TypeError(f"{message_type.__name__} must inherit from Message to register.")

        config = message_type.__struct_config__
        if config.tag is None or not isinstance(config.tag, str):
            raise TypeError(
                f"{message_type.__name__} must define a string msgspec tag to register."
            )
        existing_type = _MESSAGE_TYPES.get(config.tag)
        if existing_type is not None and existing_type is not message_type:
            raise ValueError(
                f"Message tag {config.tag!r} is already registered to {existing_type.__name__}."
            )
        existing_tag = _MESSAGE_TAGS.get(message_type)
        if existing_tag is not None and existing_tag != config.tag:
            raise ValueError(
                f"{message_type.__name__} is already registered with tag {existing_tag!r}."
            )
        _MESSAGE_TYPES[config.tag] = message_type
        _MESSAGE_TAGS[message_type] = config.tag


def decode_message(payload: object) -> object:
    """Decode a registered message from a builtins payload."""
    if not isinstance(payload, dict):
        raise msgspec.ValidationError("Expected builtins dict for protocol message decode.")

    tag = payload.get("type")
    if not isinstance(tag, str):
        raise msgspec.ValidationError("Expected message payload to include string 'type'.")

    message_type = _MESSAGE_TYPES.get(tag)
    if message_type is None:
        raise msgspec.ValidationError(f"Unknown message type {tag!r}.")

    return msgspec.convert(payload, message_type)


def listen(*message_types: type[object]) -> tp.Callable[[F], F]:
    """Register a listener or mark an instance method for later registration."""

    def decorator(fn: F) -> F:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("@listen handlers must be async functions.")
        if _looks_like_method(fn):
            setattr(fn, _LISTEN_ATTR, message_types)
            return fn

        handler = get_message_handler()
        for message_type in message_types:
            _register_listener(message_type, tp.cast("Listener", fn), handler)
        return fn

    return decorator


class _MessageHandlerBase:
    """Shared listener registration bookkeeping for handler-aware objects."""

    _message_listener_registrations: list[tuple[MessageHandlerProtocol, type[object], Listener]]
    _message_listener_handler: MessageHandlerProtocol | None

    def _ensure_message_listener_state(self) -> None:
        if hasattr(self, "_message_listener_registrations"):
            return
        self._message_listener_registrations = []
        self._message_listener_handler = None

    def register_message_listeners(self, handler: MessageHandlerProtocol | None = None) -> None:
        """Attach bound listeners for this object to the target handler."""
        self._ensure_message_listener_state()
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
        self._ensure_message_listener_state()
        for handler, message_type, listener in self._message_listener_registrations:
            _unregister_listener(message_type, listener, handler)
        self._message_listener_registrations.clear()
        self._message_listener_handler = None


class MessageHandler(_MessageHandlerBase):
    """Base class for non-stateful objects with protocol listeners."""

    def __init__(self) -> None:
        self._ensure_message_listener_state()
        handler = get_message_handler()
        if handler is not None:
            self.register_message_listeners(handler)


class StatefulMessageHandlerMixin(_MessageHandlerBase):
    """Lifecycle-driven protocol listeners for Stateful classes."""

    def on_mount(self) -> None | tp.Coroutine[tp.Any, tp.Any, None]:
        mount = getattr(super(), "on_mount", None)
        result = mount() if callable(mount) else None
        if inspect.isawaitable(result):

            async def run_after_mount(async_result: tp.Awaitable[tp.Any]) -> None:
                await async_result
                self.register_message_listeners()

            return run_after_mount(result)

        self.register_message_listeners()
        return tp.cast("None | tp.Coroutine[tp.Any, tp.Any, None]", result)

    def on_unmount(self) -> None | tp.Coroutine[tp.Any, tp.Any, None]:
        self.unregister_message_listeners()
        unmount = getattr(super(), "on_unmount", None)
        if callable(unmount):
            return tp.cast("None | tp.Coroutine[tp.Any, tp.Any, None]", unmount())
        return None


async def send(message: object) -> None:
    """Enqueue a message for the current handler."""
    handler = get_message_handler()
    if handler is None:
        raise RuntimeError("No active message handler is available for send().")
    await handler.message_send_queue.put(message)


async def dispatch(message: object) -> None:
    """Dispatch a decoded message to global and handler-scoped listeners."""
    handler = get_message_handler()
    if handler is None:
        raise RuntimeError("No active message handler is available for dispatch().")

    await _dispatch_listener_refs(_GLOBAL_LISTENERS, type(message), handler, message)

    scoped = _HANDLER_LISTENERS.get(handler)
    if scoped is None:
        return
    await _dispatch_listener_refs(scoped, type(message), handler, message)


def _register_listener(
    message_type: type[object],
    listener: Listener,
    handler: MessageHandlerProtocol | None,
) -> None:
    listener_ref = _ListenerRef.from_listener(listener)
    listeners = (
        _GLOBAL_LISTENERS[message_type]
        if handler is None
        else _HANDLER_LISTENERS.setdefault(handler, {}).setdefault(message_type, [])
    )
    if listener_ref in listeners:
        return
    listeners.append(listener_ref)


def _unregister_listener(
    message_type: type[object],
    listener: Listener,
    handler: MessageHandlerProtocol | None,
) -> None:
    listener_ref = _ListenerRef.from_listener(listener)
    listeners = (
        _GLOBAL_LISTENERS.get(message_type)
        if handler is None
        else _HANDLER_LISTENERS.get(handler, {}).get(message_type)
    )
    if not listeners:
        return

    remaining = [existing for existing in listeners if existing != listener_ref]
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


async def _dispatch_listener_refs(
    registry: dict[type[object], list[_ListenerRef]],
    message_type: type[object],
    handler: MessageHandlerProtocol,
    message: object,
) -> None:
    listener_refs = registry.get(message_type)
    if not listener_refs:
        return

    alive_refs: list[_ListenerRef] = []
    for listener_ref in tuple(listener_refs):
        listener = listener_ref.resolve()
        if listener is None:
            continue
        alive_refs.append(listener_ref)
        await listener(handler, message)

    if alive_refs:
        registry[message_type] = alive_refs
    else:
        registry.pop(message_type, None)


def _looks_like_method(fn: tp.Callable[..., tp.Any]) -> bool:
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError):
        return False
    if not params:
        return False
    first = params[0]
    return (
        first.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        and first.name == "self"
    )
