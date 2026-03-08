"""Serialization helpers for values crossing the JS proxy boundary."""

from __future__ import annotations

import typing as tp

from trellis.core.callback_context import get_callback_node_id, get_callback_session
from trellis.core.rendering.session import get_active_session

PROXY_CALLBACK_SENTINEL = "__proxy_callback__"
PROXY_CALLBACK_ID_PREFIX = "__callback__:"


def _resolve_proxy_callback_context() -> tuple[tp.Any, str]:
    session = get_active_session()
    if session is not None and session.is_executing():
        node_id = session.current_element_id
        if node_id is not None:
            return session, node_id

    callback_node_id = get_callback_node_id()
    if callback_node_id is not None:
        return get_callback_session(), callback_node_id

    raise RuntimeError("Cannot serialize JS proxy callbacks outside render or callback context.")


def serialize_proxy_value(value: tp.Any) -> tp.Any:
    """Serialize values for proxy transport, converting callables to callback sentinels."""
    if callable(value):
        session, node_id = _resolve_proxy_callback_context()
        callback_id = session.register_proxy_callback(value, node_id)
        return {PROXY_CALLBACK_SENTINEL: callback_id}

    if isinstance(value, list):
        return [serialize_proxy_value(item) for item in value]

    if isinstance(value, tuple):
        return [serialize_proxy_value(item) for item in value]

    if isinstance(value, dict):
        return {key: serialize_proxy_value(item) for key, item in value.items()}

    return value
