"""Serialization of Element trees for WebSocket transmission.

This module converts the server-side Element tree to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are registered and replaced with IDs that the client can use
to invoke them via events.
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.rendering import Element

# Callback registry - maps callback IDs to callables
_callback_registry: dict[str, tp.Callable[..., tp.Any]] = {}
_callback_counter = 0


def _generate_callback_id() -> str:
    """Generate a unique callback ID."""
    global _callback_counter
    _callback_counter += 1
    return f"cb_{_callback_counter}"


def register_callback(callback: tp.Callable[..., tp.Any]) -> str:
    """Register a callback and return its ID.

    Args:
        callback: The callable to register

    Returns:
        A unique string ID for this callback
    """
    cb_id = _generate_callback_id()
    _callback_registry[cb_id] = callback
    return cb_id


def get_callback(cb_id: str) -> tp.Callable[..., tp.Any] | None:
    """Retrieve a callback by ID.

    Args:
        cb_id: The callback ID to look up

    Returns:
        The registered callback, or None if not found
    """
    return _callback_registry.get(cb_id)


def clear_callbacks() -> None:
    """Clear all registered callbacks. For testing only."""
    global _callback_counter
    _callback_registry.clear()
    _callback_counter = 0


def _serialize_value(value: tp.Any) -> tp.Any:
    """Serialize a single value, handling special cases.

    Args:
        value: The value to serialize

    Returns:
        A JSON-serializable version of the value
    """
    if callable(value):
        # Register callback and return reference
        return {"__callback__": register_callback(value)}
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    # For other types, convert to string
    return str(value)


def serialize_element(element: Element) -> dict[str, tp.Any]:
    """Convert an Element tree to a serializable dict.

    The resulting structure can be JSON-encoded and sent to the client.
    Callbacks are replaced with `{"__callback__": "cb_123"}` references.

    Args:
        element: The Element to serialize

    Returns:
        A dict with structure:
        {
            "type": "ReactComponentType",  # The React component to render
            "name": "PythonComponentName",  # For debugging
            "key": "optional-key" or null,
            "props": {...},
            "children": [...]
        }
    """
    # Serialize props, excluding children (handled separately)
    props: dict[str, tp.Any] = {}
    for key, value in element.properties.items():
        if key == "children":
            continue  # Children are serialized separately
        props[key] = _serialize_value(value)

    return {
        "type": element.component.react_type,  # React component to use
        "name": element.component.name,  # Python component name for debugging
        "key": element.key or None,
        "props": props,
        "children": [serialize_element(child) for child in element.children],
    }
