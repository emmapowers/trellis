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

## Pure Reconciliation

The `reconcile_children` function is a pure function that compares old and new
child ID lists and returns a `ReconcileResult` categorizing each node:
- **added**: New nodes not in old list
- **removed**: Old nodes not in new list
- **matched**: Nodes present in both (may need props comparison to determine if changed)
- **child_order**: Final order of child IDs

The renderer interprets this result and performs the actual side effects
(mount/unmount, mark dirty, generate patches).
"""

from __future__ import annotations

import logging
import typing as tp
from dataclasses import dataclass, field
from dataclasses import replace as dataclass_replace

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode, RenderTree

logger = logging.getLogger(__name__)


@dataclass
class ReconcileResult:
    """Result of reconciling old and new child ID lists.

    This is a pure data structure containing categorized changes.
    No side effects are performed during reconciliation - the renderer
    interprets this result and applies mutations.

    Attributes:
        added: Node IDs that are new (not in old list)
        removed: Node IDs that were removed (in old, not in new)
        matched: Node IDs that exist in both old and new lists
        child_order: Final order of child IDs after reconciliation
    """

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)
    child_order: list[str] = field(default_factory=list)


def reconcile_children(
    old_child_ids: list[str],
    new_child_ids: list[str],
) -> ReconcileResult:
    """Pure reconciliation of old and new child ID lists.

    This function is PURE - it performs no side effects and doesn't access
    any mutable state. It only compares the two lists and categorizes each ID.

    Uses a multi-phase algorithm for optimal performance:
    1. Head scan: Match IDs from start while they match
    2. Tail scan: Match IDs from end while they match
    3. Middle: Use set-based lookup for remaining nodes

    Args:
        old_child_ids: Previous child IDs
        new_child_ids: New child IDs

    Returns:
        ReconcileResult with categorized IDs and final order
    """
    logger.debug("Reconcile: old=%d → new=%d", len(old_child_ids), len(new_child_ids))

    result = ReconcileResult(child_order=list(new_child_ids))

    # Handle empty edge cases
    if not old_child_ids:
        result.added = list(new_child_ids)
        logger.debug("Result: %d added, 0 removed, 0 matched", len(result.added))
        return result

    if not new_child_ids:
        result.removed = list(old_child_ids)
        logger.debug("Result: 0 added, %d removed, 0 matched", len(result.removed))
        return result

    old_len = len(old_child_ids)
    new_len = len(new_child_ids)
    matched_old_ids: set[str] = set()

    # Build lookup set for old children
    old_id_set: set[str] = set(old_child_ids)

    # Phase 1: Two-pointer scan from head (IDs match)
    head = 0
    while head < old_len and head < new_len:
        old_child_id = old_child_ids[head]
        new_child_id = new_child_ids[head]

        if old_child_id != new_child_id:
            break

        matched_old_ids.add(old_child_id)
        result.matched.append(old_child_id)
        head += 1

    if head == old_len and head == new_len:
        logger.debug("Result: 0 added, 0 removed, %d matched", len(result.matched))
        return result

    if head > 0:
        logger.debug("Head scan matched %d nodes", head)

    # Phase 2: Two-pointer scan from tail (IDs match)
    tail_matches: list[str] = []
    old_tail = old_len - 1
    new_tail = new_len - 1

    while old_tail >= head and new_tail >= head:
        old_child_id = old_child_ids[old_tail]
        new_child_id = new_child_ids[new_tail]

        if old_child_id != new_child_id:
            break

        matched_old_ids.add(old_child_id)
        tail_matches.append(old_child_id)
        old_tail -= 1
        new_tail -= 1

    tail_matches.reverse()

    if tail_matches:
        logger.debug("Tail scan matched %d nodes", len(tail_matches))

    # Phase 3: Process middle section with set-based matching
    middle_new_start = head
    middle_new_end = new_tail + 1

    for i in range(middle_new_start, middle_new_end):
        new_child_id = new_child_ids[i]

        if new_child_id in old_id_set and new_child_id not in matched_old_ids:
            # Found matching old node by ID
            matched_old_ids.add(new_child_id)
            result.matched.append(new_child_id)
        elif new_child_id not in old_id_set:
            # No matching old node - it's new
            result.added.append(new_child_id)

    # Add tail matches to matched list
    result.matched.extend(tail_matches)

    # Phase 4: Find removed nodes (old nodes not matched)
    for old_id in old_child_ids:
        if old_id not in matched_old_ids:
            result.removed.append(old_id)

    logger.debug(
        "Result: %d added, %d removed, %d matched",
        len(result.added),
        len(result.removed),
        len(result.matched),
    )

    return result


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
        logger.debug(
            "reconcile_node %s: component changed %s → %s, remounting",
            node_id,
            old_node.component.name,
            new_node.component.name,
        )
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
        logger.debug("reconcile_node %s: skipping (props unchanged, not dirty)", node_id)
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
    logger.debug(
        "reconcile_node %s: marking dirty (props changed or dirty flag)",
        node_id,
    )
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

    This function uses the pure `reconcile_children` function to compare
    old and new child lists, then delegates to `ctx.process_reconcile_result`
    to apply side effects (mount, unmount, reconcile matched nodes).

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
    # Use provided old_nodes, or build from ctx if not provided (for callers
    # like reconcile_node that call us before render() has a chance to overwrite)
    if old_nodes is None:
        old_nodes = {}
        for old_id in old_child_ids:
            node = ctx.get_node(old_id)
            if node:
                old_nodes[old_id] = node

    # Use pure reconciliation to compare lists
    result = reconcile_children(old_child_ids, new_child_ids)

    # Apply side effects and return final child order
    return ctx.process_reconcile_result(result, parent_id, old_nodes)
