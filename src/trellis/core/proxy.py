"""Typed Python proxies for calling bundled JavaScript objects."""

from __future__ import annotations

import inspect
import typing as tp

from trellis.core.callback_context import get_callback_node_id, get_callback_session
from trellis.core.rendering.session import get_active_session

__all__ = ["JsProxy", "ProxyTransport", "js_object"]

T = tp.TypeVar("T", bound="JsProxy")


class ProxyTransport(tp.Protocol):
    """Transport interface used by JS proxies."""

    async def call_proxy(
        self,
        proxy_id: str,
        method: str,
        args: list[tp.Any],
    ) -> tp.Any: ...


def _snake_to_camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(part.capitalize() for part in tail)


def _resolve_transport() -> ProxyTransport:
    session = get_active_session()
    if session is not None and session.is_executing():
        transport = session.proxy_transport
        if transport is not None:
            return tp.cast("ProxyTransport", transport)

    callback_node_id = get_callback_node_id()
    if callback_node_id is not None:
        callback_session = get_callback_session()
        transport = callback_session.proxy_transport
        if transport is not None:
            return tp.cast("ProxyTransport", transport)

    raise RuntimeError(
        "Cannot call JS proxy outside render or callback context without an explicit transport."
    )


def _make_proxy_method(py_name: str) -> tp.Callable[..., tp.Any]:
    js_name = _snake_to_camel(py_name)

    async def proxy_method(self: JsProxy, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        if kwargs:
            raise TypeError("JS proxy methods do not accept keyword arguments")

        transport = self._transport or _resolve_transport()
        return await transport.call_proxy(self._proxy_id, js_name, list(args))

    proxy_method.__name__ = py_name
    proxy_method.__qualname__ = py_name
    return proxy_method


class JsProxy:
    """Base class for typed JS proxy definitions."""

    _proxy_id: str
    _transport: ProxyTransport | None

    def __init__(self, proxy_id: str, transport: ProxyTransport | None = None) -> None:
        self._proxy_id = proxy_id
        self._transport = transport

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        for name, value in list(cls.__dict__.items()):
            if name.startswith("_") or name in {"__module__", "__doc__"}:
                continue

            if not inspect.isfunction(value):
                continue

            if not inspect.iscoroutinefunction(value):
                raise TypeError(f"JsProxy method '{cls.__name__}.{name}' must be async")

            setattr(cls, name, _make_proxy_method(name))


def js_object(
    proxy_type: type[T],
    proxy_id: str,
    *,
    transport: ProxyTransport | None = None,
) -> T:
    """Create a typed proxy for a bundled JS object."""
    if not issubclass(proxy_type, JsProxy):
        raise TypeError(f"Expected JsProxy subclass, got {proxy_type.__name__}")

    return proxy_type(proxy_id, transport)
