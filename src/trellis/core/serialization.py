"""Serialization of ElementNode trees for WebSocket transmission.

This module converts the server-side ElementNode trees to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are registered on the RenderTree and replaced with IDs that
the client can use to invoke them via events.
"""

from __future__ import annotations

import typing as tp

from trellis.core.composition_component import CompositionComponent

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode, RenderTree


def _serialize_value(
    value: tp.Any,
    ctx: RenderTree,
    node_id: str,
    prop_name: str,
) -> tp.Any:
    """Serialize a single value, handling special cases.

    Args:
        value: The value to serialize
        ctx: The render tree for callback registration
        node_id: The node ID for deterministic callback IDs
        prop_name: The property name for deterministic callback IDs

    Returns:
        A JSON-serializable version of the value
    """
    if callable(value):
        # Register callback with deterministic ID based on node and prop
        cb_id = ctx.register_callback(value, node_id, prop_name)
        return {"__callback__": cb_id}
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v, ctx, node_id, f"{prop_name}[{i}]") for i, v in enumerate(value)]
    if isinstance(value, dict):
        return {k: _serialize_value(v, ctx, node_id, f"{prop_name}.{k}") for k, v in value.items()}
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
            "kind": "react_component" | "jsx_element" | "text",
            "type": "ComponentOrTagName",  # The component/element to render
            "name": "PythonComponentName",  # For debugging
            "key": "optional-key" or null,
            "props": {...},
            "children": [...]
        }
    """
    # Skip props for CompositionComponents - they're layout-only and not used by React
    if isinstance(node.component, CompositionComponent):
        props: dict[str, tp.Any] = {}
    else:
        # Serialize props, excluding children (handled separately)
        props = {}
        for key, value in node.properties.items():
            if key == "children":
                continue  # Children are serialized separately
            props[key] = _serialize_value(value, ctx, node.id, key)

    return {
        "kind": node.component.element_kind.value,  # Element kind for client handling
        "type": node.component.element_name,  # Component/element type to render
        "name": node.component.name,  # Python component name for debugging
        "key": node.key or node.id,  # User key or server-assigned ID
        "props": props,
        "children": [serialize_node(child, ctx) for child in node.children],
    }
