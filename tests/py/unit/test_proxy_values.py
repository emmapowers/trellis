"""Unit tests for proxy value serialization."""

from __future__ import annotations

import asyncio
import gc
import weakref

import pytest

import trellis.core.proxy as proxy_module
from trellis.core import proxy_values
from trellis.core.components.composition import CompositionComponent
from trellis.core.rendering.session import RenderSession


def _make_session(node_id: str = "node-1") -> RenderSession:
    session = RenderSession(CompositionComponent(name="Root", render_func=lambda: None))
    session.active = type("ActiveRender", (), {"current_element_id": node_id})()
    return session


def test_serialize_proxy_value_wraps_callbacks_recursively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Callbacks in nested structures serialize to proxy callback sentinels."""
    session = _make_session()
    monkeypatch.setattr(proxy_values, "get_active_session", lambda: session)
    monkeypatch.setattr(proxy_values, "get_callback_node_id", lambda: None)

    def callback(value: int) -> int:
        return value

    serialized = proxy_values.serialize_proxy_value({"items": [callback], "callback": callback})

    callback_id = serialized["callback"][proxy_values.PROXY_CALLBACK_SENTINEL]
    nested_id = serialized["items"][0][proxy_values.PROXY_CALLBACK_SENTINEL]
    assert callback_id != nested_id

    status, resolved = session.lookup_proxy_callback(callback_id)
    assert status == "ok"
    assert resolved is not None
    assert resolved.node_id == "node-1"


def test_lookup_proxy_callback_cleans_up_dead_weakrefs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dead callback weakrefs are removed when looked up."""
    session = _make_session()
    monkeypatch.setattr(proxy_values, "get_active_session", lambda: session)
    monkeypatch.setattr(proxy_values, "get_callback_node_id", lambda: None)

    class Handler:
        def callback(self) -> None:
            return None

    owner = Handler()
    callback = owner.callback
    callback_id = proxy_values.serialize_proxy_value(callback)[proxy_values.PROXY_CALLBACK_SENTINEL]

    del callback
    del owner
    gc.collect()

    status, resolved = session.lookup_proxy_callback(callback_id)
    assert status == "dead"
    assert resolved is None
    assert callback_id not in session._proxy_callbacks


def test_register_proxy_callback_rejects_non_weakrefable_callables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-weakrefable callables are rejected."""
    session = _make_session()
    monkeypatch.setattr(proxy_values, "get_active_session", lambda: session)
    monkeypatch.setattr(proxy_values, "get_callback_node_id", lambda: None)

    class NonWeakrefableCallable:
        __slots__ = ()

        def __call__(self, value: int) -> int:
            return value

    with pytest.raises(TypeError, match="weak references"):
        proxy_values.serialize_proxy_value(NonWeakrefableCallable())


def test_decode_proxy_result_reuses_cached_handle_instance() -> None:
    """Repeated handle ids resolve to stable Python identity within one session."""

    @proxy_module.js_proxy(dynamic=True)
    class CounterHandle:
        async def increment(self) -> int:
            raise NotImplementedError

    transport = type(
        "Transport",
        (),
        {
            "session": RenderSession(CompositionComponent(name="Root", render_func=lambda: None)),
            "request_proxy": lambda self, *args, **kwargs: None,
        },
    )()
    return_spec = proxy_module._ProxyReturnSpec(
        mode="proxy",
        allow_null=False,
        proxy_cls=CounterHandle,
    )
    value = {proxy_values.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"}

    first = proxy_module._decode_proxy_result(value, return_spec=return_spec, transport=transport)
    second = proxy_module._decode_proxy_result(value, return_spec=return_spec, transport=transport)

    assert first is second
    assert transport.session.get_proxy_handle("__handle__:counter-1") is first


def test_decode_proxy_result_rejects_malformed_handle_sentinels() -> None:
    """Malformed handle payloads fail cleanly."""

    @proxy_module.js_proxy(dynamic=True)
    class CounterHandle:
        async def increment(self) -> int:
            raise NotImplementedError

    transport = type(
        "Transport",
        (),
        {
            "session": RenderSession(CompositionComponent(name="Root", render_func=lambda: None)),
            "request_proxy": lambda self, *args, **kwargs: None,
        },
    )()
    return_spec = proxy_module._ProxyReturnSpec(
        mode="proxy",
        allow_null=False,
        proxy_cls=CounterHandle,
    )

    with pytest.raises(RuntimeError, match="Malformed proxy handle response"):
        proxy_module._decode_proxy_result(
            {"wrong": "__handle__:counter-1"},
            return_spec=return_spec,
            transport=transport,
        )


def test_session_handle_cache_drops_dead_proxy_handles() -> None:
    """The per-session handle cache uses weak values."""

    class Handle:
        pass

    session = RenderSession(CompositionComponent(name="Root", render_func=lambda: None))
    handle = Handle()
    handle_ref = weakref.ref(handle)
    session.store_proxy_handle("handle-1", handle)

    assert session.get_proxy_handle("handle-1") is handle

    del handle
    gc.collect()

    assert handle_ref() is None
    assert session.get_proxy_handle("handle-1") is None


def test_decode_proxy_result_finalizer_releases_handles_on_gc() -> None:
    """Dynamic handles schedule a best-effort release on the originating loop."""

    @proxy_module.js_proxy(dynamic=True)
    class CounterHandle:
        async def increment(self) -> int:
            raise NotImplementedError

    class Transport:
        def __init__(self) -> None:
            self.session = RenderSession(
                CompositionComponent(name="Root", render_func=lambda: None)
            )
            self.calls: list[tuple[str, str, str | None]] = []

        async def request_proxy(self, proxy_id: str, operation: str, member: str | None) -> None:
            self.calls.append((proxy_id, operation, member))

    async def test() -> None:
        transport = Transport()
        return_spec = proxy_module._ProxyReturnSpec(
            mode="proxy",
            allow_null=False,
            proxy_cls=CounterHandle,
        )

        handle = proxy_module._decode_proxy_result(
            {proxy_values.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"},
            return_spec=return_spec,
            transport=transport,
        )
        handle_ref = weakref.ref(handle)
        del handle
        gc.collect()
        await asyncio.sleep(0.05)

        assert handle_ref() is None
        assert ("__handle__:counter-1", "release", None) in transport.calls

    asyncio.run(test())
