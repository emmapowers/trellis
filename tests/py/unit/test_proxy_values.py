"""Unit tests for proxy value serialization."""

from __future__ import annotations

import gc

import pytest

import trellis.core.proxy_values as proxy_values
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

    callback = lambda value: value
    serialized = proxy_values.serialize_proxy_value(
        {"items": [callback], "callback": callback}
    )

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
