"""Typed Python proxies for calling bundled JavaScript and browser global targets."""

from __future__ import annotations

import functools
import inspect
import re
import typing as tp

from trellis.core.callback_context import get_callback_node_id, get_callback_session
from trellis.core.rendering.session import get_active_session

__all__ = ["js_global", "js_method", "js_proxy"]

_METHOD_NAME_ATTR = "__trellis_js_method_name__"
_CLASS_TARGET_ATTR = "__trellis_js_proxy_name__"
_CLASS_GLOBAL_PATH_ATTR = "__trellis_js_global_path__"
_CLASS_BINDING_KIND_ATTR = "__trellis_js_binding_kind__"
_CLASS_PROXY_ID_ATTR = "__trellis_js_proxy_id__"
_GLOBAL_PROXY_ID_PREFIX = "__global__:"
_MIN_METHOD_QUALNAME_PARTS = 2
_PUBLIC_MEMBER_ERROR = (
    "proxy classes may only declare async public methods; public members are not supported"
)
_GLOBAL_PATH_RE = re.compile(r"^(?:[A-Za-z_$][A-Za-z0-9_$]*)(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+$")

_BUNDLED_OBJECT_KIND = "bundled_object"
_GLOBAL_OBJECT_KIND = "global_object"
_GLOBAL_FUNCTION_KIND = "global_function"

T = tp.TypeVar("T")
BindingKind = tp.Literal["bundled_object", "global_object", "global_function"]


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


def _make_bound_method(method_name: str | None) -> tp.Callable[..., tp.Any]:
    async def proxy_method(self: tp.Any, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        proxy_id = tp.cast("str", getattr(type(self), _CLASS_PROXY_ID_ATTR))
        transport = tp.cast("_ProxyTransport | None", getattr(self, "_transport", None))
        return await _call_proxy(proxy_id, method_name, args, kwargs, transport)

    return proxy_method


def _validate_js_method_target(func: tp.Callable[..., tp.Any]) -> None:
    qualname_parts = func.__qualname__.split(".")
    if len(qualname_parts) < _MIN_METHOD_QUALNAME_PARTS or qualname_parts[-2] == "<locals>":
        raise TypeError("@js_method can only be used on methods inside proxy classes")


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


def _validate_proxy_class_header(cls: type[tp.Any], *, decorator_name: str) -> None:
    _validate_public_annotations(cls)
    if "__init__" in cls.__dict__ or "__new__" in cls.__dict__:
        raise TypeError(f"{decorator_name} classes may not define __init__ or __new__")


def _resolve_method_name(py_name: str, func: tp.Callable[..., tp.Any]) -> str:
    return tp.cast("str | None", getattr(func, _METHOD_NAME_ATTR, None)) or _snake_to_camel(py_name)


def _iter_public_members(cls: type[tp.Any]) -> tp.Iterator[tuple[str, tp.Any]]:
    for attr_name, value in cls.__dict__.items():
        if attr_name in {"__module__", "__doc__", "__qualname__", "__annotations__"}:
            continue
        if attr_name.startswith("_"):
            continue
        yield attr_name, value


def _collect_object_proxy_methods(
    cls: type[tp.Any], *, decorator_name: str
) -> dict[str, tp.Callable[..., tp.Any]]:
    seen_methods: dict[str, str] = {}
    proxy_methods: dict[str, tp.Callable[..., tp.Any]] = {}

    for attr_name, value in _iter_public_members(cls):
        if isinstance(value, (staticmethod, classmethod, property)):
            raise TypeError(_PUBLIC_MEMBER_ERROR)
        if not inspect.isfunction(value):
            raise TypeError(_PUBLIC_MEMBER_ERROR)
        if not inspect.iscoroutinefunction(value):
            raise TypeError(f"{decorator_name} method '{cls.__name__}.{attr_name}' must be async")

        js_name = _resolve_method_name(attr_name, value)
        if js_name in seen_methods:
            other_name = seen_methods[js_name]
            raise ValueError(
                f"Duplicate JS proxy method name '{js_name}' for methods "
                f"'{other_name}' and '{attr_name}'"
            )
        seen_methods[js_name] = attr_name

        proxy_method = _make_bound_method(js_name)
        functools.update_wrapper(proxy_method, value)
        proxy_methods[attr_name] = proxy_method

    return proxy_methods


def _collect_callable_global_method(cls: type[tp.Any]) -> tuple[str, tp.Callable[..., tp.Any]]:
    methods: list[tuple[str, tp.Callable[..., tp.Any]]] = []

    for attr_name, value in _iter_public_members(cls):
        if isinstance(value, (staticmethod, classmethod, property)):
            raise TypeError(_PUBLIC_MEMBER_ERROR)
        if not inspect.isfunction(value):
            raise TypeError(_PUBLIC_MEMBER_ERROR)
        if getattr(value, _METHOD_NAME_ATTR, None) is not None:
            raise TypeError("@js_method is not supported on callable @js_global classes")
        if not inspect.iscoroutinefunction(value):
            raise TypeError(f"@js_global method '{cls.__name__}.{attr_name}' must be async")
        methods.append((attr_name, value))

    if len(methods) != 1:
        raise TypeError("callable @js_global classes must declare exactly one public async method")

    return methods[0]


def _set_class_binding_metadata(
    cls: type[tp.Any],
    *,
    binding_kind: BindingKind,
    proxy_name: str | None = None,
    global_path: str | None = None,
) -> None:
    setattr(cls, _CLASS_BINDING_KIND_ATTR, binding_kind)

    if proxy_name is not None:
        setattr(cls, _CLASS_TARGET_ATTR, proxy_name)
        setattr(cls, _CLASS_PROXY_ID_ATTR, proxy_name)

    if global_path is not None:
        setattr(cls, _CLASS_GLOBAL_PATH_ATTR, global_path)
        setattr(cls, _CLASS_PROXY_ID_ATTR, f"{_GLOBAL_PROXY_ID_PREFIX}{global_path}")


def _apply_proxy_methods(
    cls: type[T],
    *,
    binding_kind: BindingKind,
    proxy_methods: dict[str, tp.Callable[..., tp.Any]],
    proxy_name: str | None = None,
    global_path: str | None = None,
) -> type[T]:
    def __init__(self: tp.Any) -> None:
        self._transport = None

    proxy_class = tp.cast("tp.Any", cls)
    proxy_class.__init__ = __init__

    _set_class_binding_metadata(
        cls,
        binding_kind=binding_kind,
        proxy_name=proxy_name,
        global_path=global_path,
    )

    for attr_name, proxy_method in proxy_methods.items():
        setattr(cls, attr_name, proxy_method)

    return cls


def _validate_global_path(path: str) -> str:
    if not _GLOBAL_PATH_RE.match(path):
        raise TypeError(
            "Invalid global path: expected a dotted identifier path such as "
            "'window.localStorage' or 'globalThis.encodeURIComponent'"
        )
    return path


def _decorate_proxy_class(cls: type[T], name: str | None) -> type[T]:
    _validate_proxy_class_header(cls, decorator_name="@js_proxy")
    proxy_methods = _collect_object_proxy_methods(cls, decorator_name="@js_proxy")
    return _apply_proxy_methods(
        cls,
        binding_kind=_BUNDLED_OBJECT_KIND,
        proxy_methods=proxy_methods,
        proxy_name=name or cls.__name__,
    )


def _decorate_global_class(
    cls: type[T], path: str, *, kind: tp.Literal["object", "function"]
) -> type[T]:
    _validate_proxy_class_header(cls, decorator_name="@js_global")
    global_path = _validate_global_path(path)

    if kind == "object":
        proxy_methods = _collect_object_proxy_methods(cls, decorator_name="@js_global")
        return _apply_proxy_methods(
            cls,
            binding_kind=_GLOBAL_OBJECT_KIND,
            proxy_methods=proxy_methods,
            global_path=global_path,
        )

    attr_name, original_method = _collect_callable_global_method(cls)
    proxy_method = _make_bound_method(None)
    functools.update_wrapper(proxy_method, original_method)
    return _apply_proxy_methods(
        cls,
        binding_kind=_GLOBAL_FUNCTION_KIND,
        proxy_methods={attr_name: proxy_method},
        global_path=global_path,
    )


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
    """Decorate a class or async function as a bundled JavaScript proxy."""

    def decorator(target: T) -> T:
        if inspect.isclass(target):
            return tp.cast("T", _decorate_proxy_class(tp.cast("type[tp.Any]", target), name))

        if inspect.isfunction(target):
            return tp.cast(
                "T", _decorate_function(tp.cast("tp.Callable[..., tp.Any]", target), name)
            )

        raise TypeError("@js_proxy can only decorate classes or async functions")

    if obj is None:
        return decorator

    return decorator(obj)


def js_global(
    path: str,
    *,
    kind: tp.Literal["object", "function"] = "object",
) -> tp.Callable[[type[T]], type[T]]:
    """Decorate a class as a browser global JavaScript proxy."""

    def decorator(cls: type[T]) -> type[T]:
        if not inspect.isclass(cls):
            raise TypeError("@js_global can only decorate classes")
        return _decorate_global_class(cls, path, kind=kind)

    return decorator
