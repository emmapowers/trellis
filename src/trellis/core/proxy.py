"""Typed Python proxies for calling bundled JavaScript targets."""

from __future__ import annotations

import functools
import inspect
import typing as tp

from trellis.core.callback_context import get_callback_node_id, get_callback_session
from trellis.core.rendering.session import get_active_session

__all__ = ["js_method", "js_proxy"]

_METHOD_NAME_ATTR = "__trellis_js_method_name__"
_CLASS_TARGET_ATTR = "__trellis_js_proxy_name__"
_MIN_METHOD_QUALNAME_PARTS = 2
_PUBLIC_MEMBER_ERROR = (
    "@js_proxy classes may only declare async public methods; public members are not supported"
)

T = tp.TypeVar("T")


class _ProxyTransport(tp.Protocol):
    """Transport interface used by JS proxies."""

    async def call_proxy(
        self,
        proxy_id: str,
        method: str | None,
        args: list[tp.Any],
    ) -> tp.Any: ...


def _snake_to_camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(part.capitalize() for part in tail)


def _resolve_transport() -> _ProxyTransport:
    session = get_active_session()
    if session is not None and session.is_executing():
        transport = session.proxy_transport
        if transport is not None:
            return tp.cast("_ProxyTransport", transport)

    callback_node_id = get_callback_node_id()
    if callback_node_id is not None:
        callback_session = get_callback_session()
        transport = callback_session.proxy_transport
        if transport is not None:
            return tp.cast("_ProxyTransport", transport)

    raise RuntimeError("Cannot call JS proxy outside render or callback context.")


async def _call_proxy(
    proxy_id: str,
    method: str | None,
    args: tuple[tp.Any, ...],
    kwargs: dict[str, tp.Any],
    transport: _ProxyTransport | None,
) -> tp.Any:
    if kwargs:
        raise TypeError("JS proxy methods do not accept keyword arguments")

    active_transport = transport or _resolve_transport()
    return await active_transport.call_proxy(proxy_id, method, list(args))


def _make_object_method(method_name: str) -> tp.Callable[..., tp.Any]:
    async def proxy_method(self: tp.Any, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        proxy_id = tp.cast("str", getattr(type(self), _CLASS_TARGET_ATTR))
        transport = tp.cast("_ProxyTransport | None", getattr(self, "_transport", None))
        return await _call_proxy(proxy_id, method_name, args, kwargs, transport)

    return proxy_method


def _validate_js_method_target(func: tp.Callable[..., tp.Any]) -> None:
    qualname_parts = func.__qualname__.split(".")
    if len(qualname_parts) < _MIN_METHOD_QUALNAME_PARTS or qualname_parts[-2] == "<locals>":
        raise TypeError("@js_method can only be used on methods inside @js_proxy classes")


def js_method(*, name: str) -> tp.Callable[[T], T]:
    """Override the JavaScript method name for a proxy method."""

    def decorator(func: T) -> T:
        if not inspect.isfunction(func):
            raise TypeError("@js_method can only decorate methods")

        _validate_js_method_target(func)
        setattr(func, _METHOD_NAME_ATTR, name)
        return func

    return decorator


def _validate_public_annotations(cls: type[tp.Any]) -> None:
    annotations = getattr(cls, "__annotations__", {})
    for name in annotations:
        if name.startswith("_"):
            continue
        if name not in cls.__dict__:
            raise TypeError(_PUBLIC_MEMBER_ERROR)


def _resolve_method_name(py_name: str, func: tp.Callable[..., tp.Any]) -> str:
    return tp.cast("str | None", getattr(func, _METHOD_NAME_ATTR, None)) or _snake_to_camel(py_name)


def _decorate_class(cls: type[T], name: str | None) -> type[T]:
    _validate_public_annotations(cls)

    if "__init__" in cls.__dict__ or "__new__" in cls.__dict__:
        raise TypeError("@js_proxy classes may not define __init__ or __new__")

    seen_methods: dict[str, str] = {}
    proxy_methods: dict[str, tp.Callable[..., tp.Any]] = {}

    for attr_name, value in list(cls.__dict__.items()):
        if attr_name in {"__module__", "__doc__", "__qualname__", "__annotations__"}:
            continue
        if attr_name.startswith("_"):
            continue

        if isinstance(value, (staticmethod, classmethod, property)):
            raise TypeError(_PUBLIC_MEMBER_ERROR)

        if not inspect.isfunction(value):
            raise TypeError(_PUBLIC_MEMBER_ERROR)

        if not inspect.iscoroutinefunction(value):
            raise TypeError(f"js_proxy method '{cls.__name__}.{attr_name}' must be async")

        js_name = _resolve_method_name(attr_name, value)
        if js_name in seen_methods:
            other_name = seen_methods[js_name]
            raise ValueError(
                f"Duplicate JS proxy method name '{js_name}' for methods "
                f"'{other_name}' and '{attr_name}'"
            )
        seen_methods[js_name] = attr_name

        proxy_method = _make_object_method(js_name)
        functools.update_wrapper(proxy_method, value)
        proxy_methods[attr_name] = proxy_method

    def __init__(self: tp.Any) -> None:
        self._transport = None

    setattr(cls, _CLASS_TARGET_ATTR, name or cls.__name__)
    cls.__init__ = __init__

    for attr_name, proxy_method in proxy_methods.items():
        setattr(cls, attr_name, proxy_method)

    return cls


def _decorate_function(
    func: tp.Callable[..., tp.Any], name: str | None
) -> tp.Callable[..., tp.Any]:
    if not inspect.iscoroutinefunction(func):
        raise TypeError("@js_proxy can only decorate async functions")

    proxy_id = name or _snake_to_camel(func.__name__)

    @functools.wraps(func)
    async def wrapper(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        return await _call_proxy(proxy_id, None, args, kwargs, None)

    return wrapper


@tp.overload
def js_proxy(obj: type[T]) -> type[T]: ...


@tp.overload
def js_proxy(obj: tp.Callable[..., tp.Any]) -> tp.Callable[..., tp.Any]: ...


@tp.overload
def js_proxy(*, name: str) -> tp.Callable[[T], T]: ...


def js_proxy(
    obj: T | None = None,
    *,
    name: str | None = None,
) -> T | tp.Callable[[T], T]:
    """Decorate a class or async function as a JavaScript proxy."""

    def decorator(target: T) -> T:
        if inspect.isclass(target):
            return tp.cast("T", _decorate_class(tp.cast("type[tp.Any]", target), name))

        if inspect.isfunction(target):
            return tp.cast(
                "T", _decorate_function(tp.cast("tp.Callable[..., tp.Any]", target), name)
            )

        raise TypeError("@js_proxy can only decorate classes or async functions")

    if obj is None:
        return decorator

    return decorator(obj)
