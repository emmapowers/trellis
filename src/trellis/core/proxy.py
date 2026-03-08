"""Typed Python proxies for calling bundled JavaScript and browser global targets."""

from __future__ import annotations

import asyncio
import functools
import inspect
import re
import types
import typing as tp
import weakref
from dataclasses import dataclass

from trellis.core.callback_context import get_callback_node_id, get_callback_session
from trellis.core.proxy_values import (
    PROXY_HANDLE_ID_PREFIX,
    PROXY_HANDLE_SENTINEL,
    serialize_proxy_value,
)
from trellis.core.rendering.session import get_active_session

__all__ = ["js_global", "js_method", "js_property", "js_proxy", "js_release"]

_METHOD_NAME_ATTR = "__trellis_js_method_name__"
_CLASS_TARGET_ATTR = "__trellis_js_proxy_name__"
_CLASS_GLOBAL_PATH_ATTR = "__trellis_js_global_path__"
_CLASS_BINDING_KIND_ATTR = "__trellis_js_binding_kind__"
_CLASS_PROXY_ID_ATTR = "__trellis_js_proxy_id__"
_CLASS_DYNAMIC_ONLY_ATTR = "__trellis_js_dynamic_only__"
_PROPERTY_NAME_ATTR = "__trellis_js_property_name__"
_GLOBAL_PROXY_ID_PREFIX = "__global__:"
_MIN_METHOD_QUALNAME_PARTS = 2
_PUBLIC_MEMBER_ERROR = (
    "proxy classes may only declare async public methods and js_property descriptors; "
    "other public members are not supported"
)
_GLOBAL_PATH_RE = re.compile(r"^(?:[A-Za-z_$][A-Za-z0-9_$]*)(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*$")

T = tp.TypeVar("T")
BindingKind = tp.Literal["bundled_object", "global_object", "global_function", "dynamic_handle"]
_BUNDLED_OBJECT_KIND: BindingKind = "bundled_object"
_GLOBAL_OBJECT_KIND: BindingKind = "global_object"
_GLOBAL_FUNCTION_KIND: BindingKind = "global_function"
_DYNAMIC_HANDLE_KIND: BindingKind = "dynamic_handle"


@dataclass(frozen=True)
class _ProxyReturnSpec:
    mode: tp.Literal["value", "proxy"] = "value"
    allow_null: bool = True
    proxy_cls: type[tp.Any] | None = None


class _ProxyTransport(tp.Protocol):
    """Transport interface used by JS proxies."""

    async def request_proxy(
        self,
        proxy_id: str,
        operation: tp.Literal["call", "get", "set", "delete", "release"],
        member: str | None,
        args: list[tp.Any] | None = None,
        value: tp.Any = None,
        *,
        return_mode: tp.Literal["value", "proxy"] = "value",
        allow_null: bool = True,
    ) -> tp.Any: ...


class _BoundJsProperty(tp.Generic[T]):
    """Bound async accessors for a JS property."""

    def __init__(self, instance: tp.Any, descriptor: js_property[T]) -> None:
        self._instance = instance
        self._descriptor = descriptor

    async def get(self) -> T:
        proxy_id = _get_instance_proxy_id(self._instance)
        transport = tp.cast("_ProxyTransport | None", getattr(self._instance, "_transport", None))
        result = await _request_proxy(
            proxy_id,
            "get",
            self._descriptor._resolved_name,
            (),
            {},
            transport,
            return_spec=self._descriptor._return_spec,
        )
        return tp.cast("T", result)

    async def set(self, value: T) -> bool:
        if not self._descriptor.writable:
            raise TypeError(f"JS proxy property '{self._descriptor._public_name}' is not writable")

        proxy_id = _get_instance_proxy_id(self._instance)
        transport = tp.cast("_ProxyTransport | None", getattr(self._instance, "_transport", None))
        result = await _request_proxy(
            proxy_id,
            "set",
            self._descriptor._resolved_name,
            (),
            {},
            transport,
            value=value,
        )
        return tp.cast("bool", result)

    async def delete(self) -> bool:
        if not self._descriptor.deletable:
            raise TypeError(f"JS proxy property '{self._descriptor._public_name}' is not deletable")

        proxy_id = _get_instance_proxy_id(self._instance)
        transport = tp.cast("_ProxyTransport | None", getattr(self._instance, "_transport", None))
        result = await _request_proxy(
            proxy_id,
            "delete",
            self._descriptor._resolved_name,
            (),
            {},
            transport,
        )
        return tp.cast("bool", result)


class js_property(tp.Generic[T]):
    """Descriptor declaring a remotely accessible JS property."""

    writable: bool
    deletable: bool
    _declared_name: str | None
    _resolved_name: str
    _public_name: str
    _return_spec: _ProxyReturnSpec

    def __init__(
        self,
        *,
        name: str | None = None,
        writable: bool = False,
        deletable: bool = False,
    ) -> None:
        self._declared_name = name
        self.writable = writable
        self.deletable = deletable
        self._resolved_name = ""
        self._public_name = ""
        self._return_spec = _ProxyReturnSpec()

    def __set_name__(self, owner: type[tp.Any], name: str) -> None:
        self._public_name = name
        self._resolved_name = self._declared_name or _snake_to_camel(name)
        setattr(self, _PROPERTY_NAME_ATTR, self._resolved_name)

    def __get__(self, instance: tp.Any, owner: type[tp.Any] | None = None) -> tp.Any:
        if instance is None:
            return self
        return _BoundJsProperty(instance, self)


def _snake_to_camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(part.capitalize() for part in tail)


def _is_proxy_class(annotation: tp.Any) -> type[tp.Any] | None:
    if inspect.isclass(annotation) and hasattr(annotation, _CLASS_BINDING_KIND_ATTR):
        return tp.cast("type[tp.Any]", annotation)
    return None


def _parse_proxy_return_annotation(annotation: tp.Any) -> _ProxyReturnSpec:
    proxy_cls = _is_proxy_class(annotation)
    if proxy_cls is not None:
        return _ProxyReturnSpec(mode="proxy", allow_null=False, proxy_cls=proxy_cls)

    origin = tp.get_origin(annotation)
    if origin not in (tp.Union, types.UnionType):
        return _ProxyReturnSpec()

    args = tp.get_args(annotation)
    if len(args) != 2 or type(None) not in args:
        return _ProxyReturnSpec()

    other = args[0] if args[1] is type(None) else args[1]
    proxy_cls = _is_proxy_class(other)
    if proxy_cls is None:
        return _ProxyReturnSpec()
    return _ProxyReturnSpec(mode="proxy", allow_null=True, proxy_cls=proxy_cls)


def _resolve_return_spec(
    callable_obj: tp.Callable[..., tp.Any],
    *,
    localns: dict[str, tp.Any] | None = None,
) -> _ProxyReturnSpec:
    try:
        hints = tp.get_type_hints(callable_obj, globalns=callable_obj.__globals__, localns=localns)
    except Exception:
        return _ProxyReturnSpec()
    return _parse_proxy_return_annotation(hints.get("return", tp.Any))


def _get_property_return_spec(descriptor: js_property[tp.Any]) -> _ProxyReturnSpec:
    orig_class = getattr(descriptor, "__orig_class__", None)
    if orig_class is None:
        return _ProxyReturnSpec()

    args = tp.get_args(orig_class)
    if len(args) != 1:
        return _ProxyReturnSpec()
    return _parse_proxy_return_annotation(args[0])


def _get_instance_proxy_id(instance: tp.Any) -> str:
    if getattr(instance, "_released", False):
        raise RuntimeError("JS proxy handle has been released")

    instance_proxy_id = getattr(instance, "_proxy_id", None)
    if isinstance(instance_proxy_id, str):
        return instance_proxy_id

    return tp.cast("str", getattr(type(instance), _CLASS_PROXY_ID_ATTR))


def _get_transport_session(transport: _ProxyTransport) -> tp.Any | None:
    return getattr(transport, "session", None)


def _decode_proxy_result(
    value: tp.Any,
    *,
    return_spec: _ProxyReturnSpec,
    transport: _ProxyTransport,
) -> tp.Any:
    if return_spec.mode == "value":
        return value

    if value is None:
        if return_spec.allow_null:
            return None
        raise RuntimeError("Proxy response was null for a non-optional proxy return")

    if not (
        isinstance(value, dict)
        and set(value) == {PROXY_HANDLE_SENTINEL}
        and isinstance(value[PROXY_HANDLE_SENTINEL], str)
        and value[PROXY_HANDLE_SENTINEL].startswith(PROXY_HANDLE_ID_PREFIX)
    ):
        raise RuntimeError("Malformed proxy handle response")

    handle_id = value[PROXY_HANDLE_SENTINEL]
    proxy_cls = return_spec.proxy_cls
    if proxy_cls is None:
        raise RuntimeError("Missing proxy class for proxy handle response")

    session = _get_transport_session(transport)
    if session is not None:
        cached = session.get_proxy_handle(handle_id)
        if cached is not None:
            return cached

    proxy = object.__new__(proxy_cls)
    proxy._transport = transport
    proxy._proxy_id = handle_id
    proxy._released = False
    proxy._dynamic_handle = True
    proxy._finalizer = None

    if session is not None:
        session.store_proxy_handle(handle_id, proxy)
    proxy._finalizer = weakref.finalize(proxy, _finalize_proxy_handle, handle_id, transport)
    return proxy


def _finalize_proxy_handle(handle_id: str, transport: _ProxyTransport) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    if loop.is_closed():
        return

    async def release_handle() -> None:
        try:
            await transport.request_proxy(handle_id, "release", None)
        except Exception:
            return

    loop.create_task(release_handle())


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


async def _request_proxy(
    proxy_id: str,
    operation: tp.Literal["call", "get", "set", "delete", "release"],
    member: str | None,
    args: tuple[tp.Any, ...],
    kwargs: dict[str, tp.Any],
    transport: _ProxyTransport | None,
    *,
    value: tp.Any = None,
    return_spec: _ProxyReturnSpec = _ProxyReturnSpec(),
) -> tp.Any:
    if kwargs:
        raise TypeError("JS proxy methods do not accept keyword arguments")

    active_transport = transport or _resolve_transport()
    serialized_args = [serialize_proxy_value(arg) for arg in args]
    serialized_value = serialize_proxy_value(value)
    result = await active_transport.request_proxy(
        proxy_id,
        operation,
        member,
        serialized_args,
        serialized_value,
        return_mode=return_spec.mode,
        allow_null=return_spec.allow_null,
    )
    return _decode_proxy_result(result, return_spec=return_spec, transport=active_transport)


def _make_bound_method(
    method_name: str | None,
    return_spec: _ProxyReturnSpec,
) -> tp.Callable[..., tp.Any]:
    async def proxy_method(self: tp.Any, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        proxy_id = _get_instance_proxy_id(self)
        transport = tp.cast("_ProxyTransport | None", getattr(self, "_transport", None))
        return await _request_proxy(
            proxy_id,
            "call",
            method_name,
            args,
            kwargs,
            transport,
            return_spec=return_spec,
        )

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


def _collect_object_proxy_members(
    cls: type[tp.Any], *, decorator_name: str, localns: dict[str, tp.Any] | None = None
) -> tuple[dict[str, tp.Callable[..., tp.Any]], set[str]]:
    seen_members: dict[str, str] = {}
    proxy_methods: dict[str, tp.Callable[..., tp.Any]] = {}
    property_names: set[str] = set()

    for attr_name, value in _iter_public_members(cls):
        if isinstance(value, (staticmethod, classmethod, property)):
            raise TypeError(_PUBLIC_MEMBER_ERROR)
        if isinstance(value, js_property):
            js_name = value._resolved_name
            value._return_spec = _get_property_return_spec(value)
            if js_name in seen_members:
                other_name = seen_members[js_name]
                raise ValueError(
                    f"Duplicate JS proxy member name '{js_name}' for members "
                    f"'{other_name}' and '{attr_name}'"
                )
            seen_members[js_name] = attr_name
            property_names.add(attr_name)
            continue
        if not inspect.isfunction(value):
            raise TypeError(_PUBLIC_MEMBER_ERROR)
        if not inspect.iscoroutinefunction(value):
            raise TypeError(f"{decorator_name} method '{cls.__name__}.{attr_name}' must be async")

        js_name = _resolve_method_name(attr_name, value)
        return_spec = _resolve_return_spec(value, localns=localns)
        if js_name in seen_members:
            other_name = seen_members[js_name]
            raise ValueError(
                f"Duplicate JS proxy member name '{js_name}' for members "
                f"'{other_name}' and '{attr_name}'"
            )
        seen_members[js_name] = attr_name

        proxy_method = _make_bound_method(js_name, return_spec)
        functools.update_wrapper(proxy_method, value)
        proxy_methods[attr_name] = proxy_method

    return proxy_methods, property_names


def _collect_callable_global_method(cls: type[tp.Any]) -> tuple[str, tp.Callable[..., tp.Any]]:
    methods: list[tuple[str, tp.Callable[..., tp.Any]]] = []

    for attr_name, value in _iter_public_members(cls):
        if isinstance(value, js_property):
            raise TypeError("js_property is not supported on callable @js_global classes")
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
    dynamic_only: bool = False,
) -> None:
    setattr(cls, _CLASS_BINDING_KIND_ATTR, binding_kind)
    setattr(cls, _CLASS_DYNAMIC_ONLY_ATTR, dynamic_only)

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
    dynamic_only: bool = False,
) -> type[T]:
    def __init__(self: tp.Any) -> None:
        if dynamic_only:
            raise TypeError("dynamic @js_proxy classes cannot be instantiated directly")
        self._transport = None
        self._proxy_id = None
        self._released = False
        self._dynamic_handle = False
        self._finalizer = None

    proxy_class = tp.cast("tp.Any", cls)
    proxy_class.__init__ = __init__

    _set_class_binding_metadata(
        cls,
        binding_kind=binding_kind,
        proxy_name=proxy_name,
        global_path=global_path,
        dynamic_only=dynamic_only,
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


def _decorate_proxy_class(
    cls: type[T],
    name: str | None,
    *,
    dynamic: bool = False,
    localns: dict[str, tp.Any] | None = None,
) -> type[T]:
    _validate_proxy_class_header(cls, decorator_name="@js_proxy")
    if dynamic and name is not None:
        raise TypeError("@js_proxy name=... is not supported with dynamic=True")

    proxy_methods, _ = _collect_object_proxy_members(
        cls,
        decorator_name="@js_proxy",
        localns=localns,
    )
    return _apply_proxy_methods(
        cls,
        binding_kind=_DYNAMIC_HANDLE_KIND if dynamic else _BUNDLED_OBJECT_KIND,
        proxy_methods=proxy_methods,
        proxy_name=None if dynamic else name or cls.__name__,
        dynamic_only=dynamic,
    )


def _decorate_global_class(
    cls: type[T],
    path: str,
    *,
    kind: tp.Literal["object", "function"],
    localns: dict[str, tp.Any] | None = None,
) -> type[T]:
    _validate_proxy_class_header(cls, decorator_name="@js_global")
    global_path = _validate_global_path(path)

    if kind == "object":
        proxy_methods, _ = _collect_object_proxy_members(
            cls,
            decorator_name="@js_global",
            localns=localns,
        )
        return _apply_proxy_methods(
            cls,
            binding_kind=_GLOBAL_OBJECT_KIND,
            proxy_methods=proxy_methods,
            global_path=global_path,
        )

    attr_name, original_method = _collect_callable_global_method(cls)
    proxy_method = _make_bound_method(None, _resolve_return_spec(original_method, localns=localns))
    functools.update_wrapper(proxy_method, original_method)
    return _apply_proxy_methods(
        cls,
        binding_kind=_GLOBAL_FUNCTION_KIND,
        proxy_methods={attr_name: proxy_method},
        global_path=global_path,
    )


def _decorate_function(
    func: tp.Callable[..., tp.Any],
    name: str | None,
    *,
    localns: dict[str, tp.Any] | None = None,
) -> tp.Callable[..., tp.Any]:
    if not inspect.iscoroutinefunction(func):
        raise TypeError("@js_proxy can only decorate async functions")

    proxy_id = name or _snake_to_camel(func.__name__)
    return_spec = _resolve_return_spec(func, localns=localns)

    @functools.wraps(func)
    async def wrapper(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        return await _request_proxy(
            proxy_id,
            "call",
            None,
            args,
            kwargs,
            None,
            return_spec=return_spec,
        )

    return wrapper


@tp.overload
def js_proxy(obj: type[T]) -> type[T]: ...


@tp.overload
def js_proxy(obj: tp.Callable[..., tp.Any]) -> tp.Callable[..., tp.Any]: ...


@tp.overload
def js_proxy(*, name: str | None = None, dynamic: bool = False) -> tp.Callable[[T], T]: ...


def js_proxy(
    obj: T | None = None,
    *,
    name: str | None = None,
    dynamic: bool = False,
) -> T | tp.Callable[[T], T]:
    """Decorate a class or async function as a bundled JavaScript proxy."""
    frame = inspect.currentframe()
    assert frame is not None
    caller_frame = frame.f_back
    localns = dict(caller_frame.f_locals) if caller_frame is not None else None

    def decorator(target: T) -> T:
        if inspect.isclass(target):
            return tp.cast(
                "T",
                _decorate_proxy_class(
                    tp.cast("type[tp.Any]", target),
                    name,
                    dynamic=dynamic,
                    localns=localns,
                ),
            )

        if inspect.isfunction(target):
            if dynamic:
                raise TypeError("@js_proxy(dynamic=True) is only supported on classes")
            return tp.cast(
                "T",
                _decorate_function(
                    tp.cast("tp.Callable[..., tp.Any]", target),
                    name,
                    localns=localns,
                ),
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
    frame = inspect.currentframe()
    assert frame is not None
    caller_frame = frame.f_back
    localns = dict(caller_frame.f_locals) if caller_frame is not None else None

    def decorator(cls: type[T]) -> type[T]:
        if not inspect.isclass(cls):
            raise TypeError("@js_global can only decorate classes")
        return _decorate_global_class(cls, path, kind=kind, localns=localns)

    return decorator


async def js_release(proxy: tp.Any) -> None:
    """Release a returned dynamic proxy handle."""
    if not getattr(proxy, "_dynamic_handle", False):
        raise TypeError("js_release() only supports returned proxy handles")

    if getattr(proxy, "_released", False):
        return

    proxy._released = True
    finalizer = getattr(proxy, "_finalizer", None)
    if finalizer is not None:
        finalizer.detach()

    transport = tp.cast("_ProxyTransport | None", getattr(proxy, "_transport", None))
    if transport is None:
        return

    await transport.request_proxy(proxy._proxy_id, "release", None)
