"""Serialization of ElementNode trees for WebSocket transmission.

This module converts the server-side ElementNode trees to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are replaced with IDs (node_id|prop_name) that the client can use
to invoke them via events. The callback is looked up from the node's props
at invocation time.

Two modes:
1. Full serialization via `serialize_node()` - for initial render
2. Incremental patches are generated inline during reconciliation (see rendering.py)
"""

from __future__ import annotations

import typing as tp

from trellis.core.components.composition import CompositionComponent
from trellis.core.state.mutable import Mutable

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import ElementNode
    from trellis.core.rendering.session import RenderSession


def _make_callback_id(node_id: str, prop_name: str) -> str:
    """Create a callback ID from node_id and prop_name.

    Args:
        node_id: The node's ID
        prop_name: The property name

    Returns:
        Callback ID in format "node_id|prop_name"
    """
    return f"{node_id}|{prop_name}"


def parse_callback_id(callback_id: str) -> tuple[str, str]:
    """Parse a callback ID into node_id and prop_name.

    Args:
        callback_id: The callback ID to parse

    Returns:
        Tuple of (node_id, prop_name)

    Raises:
        ValueError: If callback_id format is invalid
    """
    # Find the last | since node_id may contain special characters
    idx = callback_id.rfind("|")
    if idx == -1:
        raise ValueError(f"Invalid callback_id format: {callback_id}")
    return callback_id[:idx], callback_id[idx + 1 :]


def _serialize_value(
    value: tp.Any,
    session: RenderSession,
    node_id: str,
    prop_name: str,
) -> tp.Any:
    """Serialize a single value, handling special cases.

    Args:
        value: The value to serialize
        session: The render session (unused, kept for API compatibility)
        node_id: The node ID for callback IDs
        prop_name: The property name for callback IDs

    Returns:
        A JSON-serializable version of the value
    """
    # Handle Mutable wrappers for two-way binding
    # Mutable has __call__ so it's callable - we serialize the current value
    # and provide a callback ID for updates
    if isinstance(value, Mutable):
        cb_id = _make_callback_id(node_id, prop_name)
        return {
            "__mutable__": cb_id,
            "value": _serialize_value(value.value, session, node_id, f"{prop_name}.value"),
        }

    if callable(value):
        # Create callback ID from node and prop
        cb_id = _make_callback_id(node_id, prop_name)
        return {"__callback__": cb_id}
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [
            _serialize_value(v, session, node_id, f"{prop_name}[{i}]") for i, v in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            k: _serialize_value(v, session, node_id, f"{prop_name}.{k}") for k, v in value.items()
        }
    # For other types, convert to string
    return str(value)


def serialize_node(node: ElementNode, session: RenderSession) -> dict[str, tp.Any]:
    """Convert an ElementNode to a serializable dict.

    The resulting structure can be JSON-encoded and sent to the client.
    Callbacks are replaced with `{"__callback__": "cb_123"}` references.
    Children are looked up from the flat node storage via child_ids.

    Args:
        node: The ElementNode to serialize
        session: The RenderSession for callback registration and child lookup

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
    props = _serialize_node_props(node, session)

    # Get children from flat storage and serialize them
    children = []
    for child_id in node.child_ids:
        child_node = session.elements.get(child_id)
        if child_node:
            children.append(serialize_node(child_node, session))

    return {
        "kind": node.component.element_kind.value,  # Element kind for client handling
        "type": node.component.element_name,  # Component/element type to render
        "name": node.component.name,  # Python component name for debugging
        "key": node.id,  # Position-based ID (encodes position and user key)
        "props": props,
        "children": children,
    }


def _serialize_props(
    props: dict[str, tp.Any], session: RenderSession, node_id: str
) -> dict[str, tp.Any]:
    """Serialize a props dict for wire transmission.

    Args:
        props: Raw props dict to serialize
        session: The RenderSession (unused, kept for API compatibility)
        node_id: The node ID for callback IDs

    Returns:
        Serialized props dict
    """
    result = {}
    for key, value in props.items():
        if key == "child_ids":
            continue
        result[key] = _serialize_value(value, session, node_id, key)
    return result


def _serialize_node_props(node: ElementNode, session: RenderSession) -> dict[str, tp.Any]:
    """Serialize just the props of a node (excluding child_ids).

    Used by rendering.py for inline patch generation to compare props.

    Args:
        node: The ElementNode to serialize props from
        session: The RenderSession for callback registration

    Returns:
        Serialized props dict
    """
    if isinstance(node.component, CompositionComponent):
        return {}
    return _serialize_props(node.properties, session, node.id)
