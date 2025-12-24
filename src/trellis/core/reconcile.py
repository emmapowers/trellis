"""
React-like reconciliation algorithm for ElementNode trees.

This module implements a reconciliation algorithm inspired by React's approach,
used to efficiently update the node tree when components re-render. The goal
is to minimize mutations by reusing existing nodes where possible.

## Architecture

The rendering system uses:
- **ElementNode**: Immutable tree nodes with child_ids (references, not nested)
- **ElementState**: Mutable runtime state keyed by node ID (local_state, dirty flag, etc.)
- **RenderTree._nodes**: Flat storage of all nodes by ID

During reconciliation:
1. **Node Creation**: Components produce ElementNode descriptors with IDs
2. **Reconciliation/Execution**: Compare old/new child IDs, reconcile as needed

## Matching Strategy

With position-based IDs (which encode position AND component identity), matching
is now by ID:
- Same ID = same position and component type
- Different ID = different position or component type

The multi-phase optimization is still used for efficient child list reconciliation:
1. **Head scan**: Match IDs from the start while they match
2. **Tail scan**: Match IDs from the end while they match
3. **Middle**: Use ID-based lookup for remaining nodes

## Complexity

- Best case (append/prepend): O(n) where n = list length
- Average/worst case: O(n) with hash lookups
"""

from __future__ import annotations

import typing as tp
from dataclasses import replace as dataclass_replace

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode, RenderTree


def reconcile_node(
    old_node: ElementNode | None,
    new_node: ElementNode,
    parent_id: str | None,
    ctx: RenderTree,
    *,
    call_hooks: bool = True,
) -> ElementNode:
    """Reconcile an old node with a new node.

    With position-based IDs, the new node already has its ID assigned based on
    tree position. Matching is now by ID, not by component + key.

    This function decides whether to:
    - Create a new node (if old_node is None or component changed at same position)
    - Skip execution (if props unchanged and not dirty)
    - Re-execute (if props changed or dirty)

    Args:
        old_node: Existing node to reconcile against, or None for new mount
        new_node: The new node describing what to render (already has position-based ID)
        parent_id: Parent node's ID (for ElementState.parent_id)
        ctx: The render tree
        call_hooks: Whether to call mount hooks. Set False for recursive calls.

    Returns:
        The reconciled node (also stored in ctx._nodes)
    """
    node_id = new_node.id

    # Case 1: No old node - mount new
    if old_node is None:
        mounted = ctx.mount_new_node(new_node, parent_id, call_hooks=call_hooks)
        ctx.store_node(mounted)
        return mounted

    # With position-based IDs, old and new nodes at same position have same ID
    # If IDs don't match, that's a bug in caller - they should use ID for lookup
    assert (
        old_node.id == new_node.id
    ), f"reconcile_node called with mismatched IDs: old={old_node.id}, new={new_node.id}"

    # Case 2: Component changed at same position - unmount old, mount new
    if old_node.component != new_node.component:
        ctx.unmount_node_tree(old_node.id)
        mounted = ctx.mount_new_node(new_node, parent_id, call_hooks=call_hooks)
        ctx.store_node(mounted)
        return mounted

    # Check if this node has been mounted before (has ElementState)
    # With position-based IDs, nodes created in `with` blocks have IDs but
    # haven't been mounted yet - they need to go through mount_new_node
    existing_state = ctx._element_state.get(node_id)
    if existing_state is None:
        # First time seeing this node - mount it
        mounted = ctx.mount_new_node(new_node, parent_id, call_hooks=call_hooks)
        ctx.store_node(mounted)
        return mounted

    # Case 3: Same component - check if we can skip execution
    if old_node.props == new_node.props and not existing_state.dirty:
        # Props unchanged and not dirty - skip execution entirely!
        # However, we must reconcile with-block child_ids from the parent's execution.
        # These appear on new_node.child_ids when a parent re-renders and produces
        # nested with-block descriptors (e.g., `with Outer(): with Inner(): Leaf()`).
        # Even though this node's props are unchanged, grandchildren may have new props.
        if new_node.child_ids:
            new_child_ids = reconcile_node_children(
                list(old_node.child_ids), list(new_node.child_ids), node_id, ctx
            )
            result = dataclass_replace(new_node, child_ids=tuple(new_child_ids))
            ctx.store_node(result)
            return result
        # Preserve old child_ids if new_node has none (it's a descriptor, not executed)
        result = (
            dataclass_replace(new_node, child_ids=old_node.child_ids)
            if old_node.child_ids
            else new_node
        )
        ctx.store_node(result)
        return result

    # Case 4: Props changed or dirty - mark dirty for later rendering
    # Keep old child_ids - they'll be reconciled when this node is rendered
    ctx.mark_dirty_id(node_id)
    result = dataclass_replace(new_node, child_ids=old_node.child_ids)
    ctx.store_node(result)
    return result


def reconcile_node_children(
    old_child_ids: list[str],
    new_child_ids: list[str],
    parent_id: str,
    ctx: RenderTree,
    old_nodes: dict[str, ElementNode] | None = None,
) -> list[str]:
    """Reconcile old child IDs with new child IDs.

    With position-based IDs and flat storage, this function:
    1. Matches old and new children by ID
    2. Calls reconcile_node for matches
    3. Mounts new nodes, unmounts removed nodes
    4. Returns the final list of child IDs

    Uses a multi-phase algorithm for optimal performance:
    1. Head scan: Match IDs from start while they match
    2. Tail scan: Match IDs from end while they match
    3. Middle: Use ID-based lookup for remaining nodes

    IMPORTANT: Old nodes must be saved BEFORE render() is called, since new node
    descriptors may overwrite them in ctx._nodes (same position-based ID). The
    old_nodes dict is passed in by the caller (execute_node) who saved them.

    Args:
        old_child_ids: Current child IDs
        new_child_ids: New child IDs
        parent_id: Parent node's ID
        ctx: The render tree
        old_nodes: Pre-saved old nodes dict (from before render() overwrote them)

    Returns:
        List of reconciled child IDs
    """
    result_ids: list[str] = []

    # Use provided old_nodes, or build from ctx if not provided (for callers
    # like reconcile_node that call us before render() has a chance to overwrite)
    if old_nodes is None:
        old_nodes = {}
        for old_id in old_child_ids:
            node = ctx.get_node(old_id)
            if node:
                old_nodes[old_id] = node

    # Phase 1: Handle empty edge cases
    if not old_child_ids:
        for child_id in new_child_ids:
            child_node = ctx.get_node(child_id)
            if child_node:
                ctx.mount_new_node(child_node, parent_id, call_hooks=False)
                result_ids.append(child_id)
        return result_ids

    if not new_child_ids:
        for child_id in old_child_ids:
            ctx.unmount_node_tree(child_id)
        return []

    old_len = len(old_child_ids)
    new_len = len(new_child_ids)
    matched_old_ids: set[str] = set()

    # Build lookup set for old children
    old_id_set: set[str] = set(old_child_ids)

    # Phase 2: Two-pointer scan from head (IDs match)
    head = 0
    while head < old_len and head < new_len:
        old_child_id = old_child_ids[head]
        new_child_id = new_child_ids[head]

        # With position-based IDs, same position = same ID
        if old_child_id != new_child_id:
            break

        matched_old_ids.add(old_child_id)
        old_node = old_nodes.get(old_child_id)  # Use saved old node
        new_node = ctx.get_node(new_child_id)
        if old_node and new_node:
            reconcile_node(old_node, new_node, parent_id, ctx, call_hooks=False)
        result_ids.append(new_child_id)
        head += 1

    if head == old_len and head == new_len:
        return result_ids

    # Phase 3: Two-pointer scan from tail (IDs match)
    tail_match_ids: list[str] = []
    old_tail = old_len - 1
    new_tail = new_len - 1

    while old_tail >= head and new_tail >= head:
        old_child_id = old_child_ids[old_tail]
        new_child_id = new_child_ids[new_tail]

        if old_child_id != new_child_id:
            break

        matched_old_ids.add(old_child_id)
        old_node = old_nodes.get(old_child_id)  # Use saved old node
        new_node = ctx.get_node(new_child_id)
        if old_node and new_node:
            reconcile_node(old_node, new_node, parent_id, ctx, call_hooks=False)
        tail_match_ids.append(new_child_id)
        old_tail -= 1
        new_tail -= 1

    tail_match_ids.reverse()

    # Phase 4: Process middle section with ID-based matching
    middle_new_start = head
    middle_new_end = new_tail + 1

    for i in range(middle_new_start, middle_new_end):
        new_child_id = new_child_ids[i]

        if new_child_id in old_id_set and new_child_id not in matched_old_ids:
            # Found matching old node by ID - reconcile
            matched_old_ids.add(new_child_id)
            old_node = old_nodes.get(new_child_id)  # Use saved old node
            new_node = ctx.get_node(new_child_id)
            if old_node and new_node:
                reconcile_node(old_node, new_node, parent_id, ctx, call_hooks=False)
            result_ids.append(new_child_id)
        else:
            # No matching old node - mount new
            new_node = ctx.get_node(new_child_id)
            if new_node:
                ctx.mount_new_node(new_node, parent_id, call_hooks=False)
            result_ids.append(new_child_id)

    result_ids.extend(tail_match_ids)

    # Phase 5: Unmount unmatched old nodes
    for old_id in old_child_ids:
        if old_id not in matched_old_ids:
            ctx.unmount_node_tree(old_id)

    return result_ids
