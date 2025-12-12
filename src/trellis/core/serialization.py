"""Serialization of ElementNode trees for WebSocket transmission.

This module converts the server-side ElementNode trees to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are registered on the RenderTree and replaced with IDs that
the client can use to invoke them via events.
"""

from __future__ import annotations

import typing as tp

from trellis.core.functional_component import FunctionalComponent

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode, RenderTree


def _serialize_value(value: tp.Any, ctx: RenderTree) -> tp.Any:
    """Serialize a single value, handling special cases.

    Args:
        value: The value to serialize
        ctx: The render tree for callback registration

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


def serialize_node(node: ElementNode, ctx: RenderTree) -> dict[str, tp.Any]:
    """Convert an ElementNode tree to a serializable dict.

    The resulting structure can be JSON-encoded and sent to the client.
    Callbacks are replaced with `{"__callback__": "cb_123"}` references.

    Args:
        node: The ElementNode to serialize
        ctx: The RenderTree for callback registration

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
    # Skip props for FunctionalComponents - they're layout-only and not used by React
    if isinstance(node.component, FunctionalComponent):
        props: dict[str, tp.Any] = {}
    else:
        # Serialize props, excluding children (handled separately)
        props = {}
        for key, value in node.properties.items():
            if key == "children":
                continue  # Children are serialized separately
            props[key] = _serialize_value(value, ctx)

    return {
        "type": node.component.react_type,  # React component to use
        "name": node.component.name,  # Python component name for debugging
        "key": node.key or node.id,  # User key or server-assigned ID
        "props": props,
        "children": [serialize_node(child, ctx) for child in node.children],
    }
