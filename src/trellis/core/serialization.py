"""Serialization of ElementNode trees for WebSocket transmission.

This module converts the server-side ElementNode trees to a JSON-serializable
format that can be sent to the client for rendering.

Callbacks are registered on the RenderTree and replaced with IDs that
the client can use to invoke them via events.

Two modes:
1. Full serialization via `serialize_node()` - for initial render
2. Incremental patches via `compute_patches()` - for updates after state changes
"""

from __future__ import annotations

import typing as tp

from trellis.core.composition_component import CompositionComponent
from trellis.core.messages import AddPatch, Patch, RemovePatch, UpdatePatch
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


def compute_patches(
    root: ElementNode,
    ctx: RenderTree,
    previous_props: dict[str, dict[str, tp.Any]],
    previous_children: dict[str, list[str]],
    removed_ids: list[str],
) -> list[Patch]:
    """Compute incremental patches by comparing current tree to previous state.

    Walks the tree and generates patches for:
    - Props changes (update patches with only changed props)
    - Children order changes (update patches with new children list)
    - Removed nodes (remove patches)
    - Added nodes (add patches with full subtree)

    NOTE: This function MUTATES previous_props and previous_children to update
    them with current state for the next diff cycle. This is intentional for
    efficiency but callers should be aware of the side effect.

    Args:
        root: Current root node of the tree
        ctx: The RenderTree for callback registration
        previous_props: Dict of node_id -> previous serialized props (mutated)
        previous_children: Dict of node_id -> previous child IDs (mutated)
        removed_ids: List of node IDs that were removed

    Returns:
        List of Patch objects to send to client
    """
    patches: list[Patch] = []

    # First, add remove patches for unmounted nodes
    for node_id in removed_ids:
        patches.append(RemovePatch(id=node_id))
        # Clean up previous state
        previous_props.pop(node_id, None)
        previous_children.pop(node_id, None)

    # Then walk tree and compute patches
    _compute_node_patches(root, None, None, ctx, previous_props, previous_children, patches)

    return patches


def _get_stable_id(node: ElementNode) -> str:
    """Get the stable ID for a node.

    With position-based IDs, the node.id is always the stable identifier.
    This must match what serialize_node() sends as the 'key' field to the client.
    """
    return node.id


def _populate_subtree_state(
    node: ElementNode,
    ctx: RenderTree,
    previous_props: dict[str, dict[str, tp.Any]],
    previous_children: dict[str, list[str]],
) -> None:
    """Recursively populate previous state for a node and all its descendants.

    Called when a new node is added to ensure all descendants have their state
    tracked for subsequent diffs.

    Args:
        node: The node to populate state for
        ctx: The RenderTree for callback registration and child lookup
        previous_props: Dict of node_id -> serialized props (mutated)
        previous_children: Dict of node_id -> child IDs (mutated)
    """
    node_id = _get_stable_id(node)
    previous_props[node_id] = _serialize_node_props(node, ctx)
    previous_children[node_id] = list(node.child_ids)
    for child_id in node.child_ids:
        child = ctx.get_node(child_id)
        if child:
            _populate_subtree_state(child, ctx, previous_props, previous_children)


def _compute_node_patches(
    node: ElementNode,
    parent_id: str | None,
    parent_child_ids: list[str] | None,
    ctx: RenderTree,
    previous_props: dict[str, dict[str, tp.Any]],
    previous_children: dict[str, list[str]],
    patches: list[Patch],
) -> None:
    """Recursively compute patches for a node and its descendants.

    Args:
        node: Current node to process
        parent_id: ID of parent node (for add patches)
        parent_child_ids: Parent's current children IDs (for add patches)
        ctx: The RenderTree for callback registration and child lookup
        previous_props: Dict of node_id -> previous serialized props (mutated)
        previous_children: Dict of node_id -> previous child IDs (mutated)
        patches: List to append patches to
    """
    node_id = _get_stable_id(node)
    current_props = _serialize_node_props(node, ctx)
    current_child_ids = list(node.child_ids)

    # Check if this is a new node
    if node_id not in previous_props:
        # New node - emit add patch with full subtree
        patches.append(
            AddPatch(
                parent_id=parent_id,
                children=parent_child_ids or [],
                node=serialize_node(node, ctx),
            )
        )
        # Store current state for this node AND all descendants
        _populate_subtree_state(node, ctx, previous_props, previous_children)
        # Don't recurse in patch computation - full subtree is in the add patch
        return

    # Existing node - check for changes
    prev_props = previous_props[node_id]
    prev_child_ids = previous_children.get(node_id, [])

    # Compute prop diff (only changed props)
    props_diff: dict[str, tp.Any] = {
        key: value
        for key, value in current_props.items()
        if key not in prev_props or prev_props[key] != value
    }
    # Add removed props (signal removal with None)
    props_diff.update({key: None for key in prev_props if key not in current_props})

    # Check if children order changed
    children_changed = current_child_ids != prev_child_ids

    # Emit update patch if props or children changed
    if props_diff or children_changed:
        patches.append(
            UpdatePatch(
                id=node_id,
                props=props_diff if props_diff else None,
                children=current_child_ids if children_changed else None,
            )
        )

    # Update stored state
    previous_props[node_id] = current_props
    previous_children[node_id] = current_child_ids

    # Recurse into children (lookup from flat storage)
    for child_id in node.child_ids:
        child = ctx.get_node(child_id)
        if child:
            _compute_node_patches(
                child, node_id, current_child_ids, ctx, previous_props, previous_children, patches
            )
