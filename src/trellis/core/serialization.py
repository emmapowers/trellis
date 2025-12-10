"""Serialization of Element trees for WebSocket transmission.

This module converts the server-side Element tree to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are registered on the RenderContext and replaced with IDs that
the client can use to invoke them via events.
"""

from __future__ import annotations

import typing as tp

from trellis.core.functional_component import FunctionalComponent

if tp.TYPE_CHECKING:
    from trellis.core.rendering import Element, RenderContext


def _serialize_value(value: tp.Any, ctx: RenderContext) -> tp.Any:
    """Serialize a single value, handling special cases.

    Args:
        value: The value to serialize
        ctx: The render context for callback registration

    Returns:
        A JSON-serializable version of the value
    """
    if callable(value):
        # Register callback on the context and return reference
        cb_id = ctx.register_callback(value)
        return {"__callback__": cb_id}
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v, ctx) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v, ctx) for k, v in value.items()}
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

    Raises:
        RuntimeError: If element has no render_context
    """
    ctx = element.render_context
    if ctx is None:
        raise RuntimeError("Cannot serialize element without render_context")

    # Skip props for FunctionalComponents - they're layout-only and not used by React
    if isinstance(element.component, FunctionalComponent):
        props: dict[str, tp.Any] = {}
    else:
        # Serialize props, excluding children (handled separately)
        props = {}
        for key, value in element.properties.items():
            if key == "children":
                continue  # Children are serialized separately
            props[key] = _serialize_value(value, ctx)

    return {
        "type": element.component.react_type,  # React component to use
        "name": element.component.name,  # Python component name for debugging
        "key": element.key or element.stable_id,  # User key or server-assigned ID
        "props": props,
        "children": [serialize_element(child) for child in element.children],
    }
