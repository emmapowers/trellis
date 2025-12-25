"""Serialization of ElementNode trees for WebSocket transmission.

This module converts the server-side ElementNode trees to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are registered on the RenderTree and replaced with IDs that
the client can use to invoke them via events.

Two modes:
1. Full serialization via `serialize_node()` - for initial render
2. Incremental patches are generated inline during reconciliation (see rendering.py)
"""

from __future__ import annotations

import typing as tp

from trellis.core.composition_component import CompositionComponent
from trellis.core.mutable import Mutable

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
    # Handle Mutable wrappers for two-way binding
    if isinstance(value, Mutable):

        def setter(new_val: tp.Any) -> None:
            value.value = new_val  # Mutable.value setter handles on_change

        cb_id = ctx.register_callback(setter, node_id, f"{prop_name}:mutable")
        return {
            "__mutable__": cb_id,
            "value": _serialize_value(value.value, ctx, node_id, f"{prop_name}.value"),
        }

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
    """Convert an ElementNode to a serializable dict.

    The resulting structure can be JSON-encoded and sent to the client.
    Callbacks are replaced with `{"__callback__": "cb_123"}` references.
    Children are looked up from the flat node storage via child_ids.

    Args:
        node: The ElementNode to serialize
        ctx: The RenderTree for callback registration and child lookup

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
        # Serialize props, excluding child_ids (children are serialized separately)
        props = {}
        for key, value in node.properties.items():
            if key == "child_ids":
                continue  # Children are serialized separately
            props[key] = _serialize_value(value, ctx, node.id, key)

    # Get children from flat storage and serialize them
    children = []
    for child_id in node.child_ids:
        child_node = ctx.get_node(child_id)
        if child_node:
            children.append(serialize_node(child_node, ctx))

    return {
        "kind": node.component.element_kind.value,  # Element kind for client handling
        "type": node.component.element_name,  # Component/element type to render
        "name": node.component.name,  # Python component name for debugging
        "key": node.id,  # Position-based ID (encodes position and user key)
        "props": props,
        "children": children,
    }


def _serialize_node_props(node: ElementNode, ctx: RenderTree) -> dict[str, tp.Any]:
    """Serialize just the props of a node (excluding child_ids).

    Used by rendering.py for inline patch generation to compare props.

    Args:
        node: The ElementNode to serialize props from
        ctx: The RenderTree for callback registration

    Returns:
        Serialized props dict
    """
    if isinstance(node.component, CompositionComponent):
        return {}
    props = {}
    for key, value in node.properties.items():
        if key == "child_ids":
            continue
        props[key] = _serialize_value(value, ctx, node.id, key)
    return props
