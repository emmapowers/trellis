"""
React-like reconciliation algorithm for ElementNode trees.

This module implements a reconciliation algorithm inspired by React's approach,
used to efficiently update the node tree when components re-render. The goal
is to minimize mutations by reusing existing nodes where possible.

## Architecture

The rendering system uses:
- **ElementNode**: Immutable tree nodes describing the component structure
- **ElementState**: Mutable runtime state keyed by node ID (local_state, dirty flag, etc.)

During reconciliation:
1. **Node Creation**: Components produce ElementNode descriptors
2. **Reconciliation/Execution**: Compare new nodes with existing ones,
   execute components only when needed

## Matching Strategy

Nodes are matched using a multi-phase approach for optimal performance:

1. **Two-pointer scan (head)**: Match nodes from the start of both lists
   while component types match. Catches appends efficiently.

2. **Two-pointer scan (tail)**: Match nodes from the end of both lists
   while component types match. Catches prepends efficiently.

3. **Key-based matching**: For the remaining "middle" section, use explicit
   keys for O(1) lookup when both old and new nodes have keys.

4. **Type-based matching**: For non-keyed nodes in the middle section,
   use O(1) lookup by component type.

## Complexity

- Best case (append/prepend): O(n) where n = list length
- Average/worst case: O(n) with hash lookups for keyed and type-based matching
"""

from __future__ import annotations

import logging
import typing as tp
from dataclasses import replace as dataclass_replace

# Import shared types from base (no circular dependency)
from trellis.core.base import IComponent

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
    """Reconcile an old node with a new node (ElementNode architecture).

    This is the main entry point for the new reconciliation. It decides whether to:
    - Create a new node (if old_node is None or component changed)
    - Skip execution (if props unchanged and not dirty)
    - Re-execute (if props changed or dirty)

    Args:
        old_node: Existing node to reconcile against, or None for new mount
        new_node: The new node describing what to render
        parent_id: Parent node's ID (for ElementState.parent_id)
        ctx: The render tree
        call_hooks: Whether to call mount hooks. Set False for recursive calls.

    Returns:
        The reconciled node with final ID and children
    """

    # Case 1: No old node - mount new
    if old_node is None:
        return mount_new_node(new_node, parent_id, ctx, call_hooks=call_hooks)

    # Case 2: Component changed - unmount old, mount new
    if old_node.component != new_node.component:
        unmount_node_tree(old_node, ctx)
        return mount_new_node(new_node, parent_id, ctx, call_hooks=call_hooks)

    # Transfer ID from old to new
    node_with_id = dataclass_replace(new_node, id=old_node.id)

    # Get state for this node
    state = ctx.get_element_state(node_with_id.id)

    # Case 3: Same component - check if we can skip execution
    if old_node.props == new_node.props and not state.dirty:
        # Props unchanged and not dirty - skip execution entirely!
        # But still need to reconcile children if they exist
        if new_node.children:
            new_children = reconcile_node_children(
                list(old_node.children), list(new_node.children), node_with_id.id, ctx
            )
            node_with_id = dataclass_replace(node_with_id, children=tuple(new_children))
        elif old_node.children:
            # new_node has no children (it's a descriptor, not executed)
            # but old_node has children from previous execution - preserve them
            node_with_id = dataclass_replace(node_with_id, children=old_node.children)
        return node_with_id

    # Case 4: Props changed or dirty - mark dirty for later rendering
    # Keep old children - they'll be reconciled when this node is rendered
    ctx.mark_dirty_id(node_with_id.id)
    return dataclass_replace(node_with_id, children=old_node.children)


def mount_new_node(
    node: ElementNode,
    parent_id: str | None,
    ctx: RenderTree,
    *,
    call_hooks: bool = True,
) -> ElementNode:
    """Create and mount a new node (ElementNode architecture).

    Assigns a new ID, creates ElementState, marks dirty for later rendering.
    The actual component execution happens in _render_dirty_nodes.

    Args:
        node: The node to mount (will have empty id)
        parent_id: Parent node's ID
        ctx: The render tree
        call_hooks: Whether to track mount hooks. Set False for internal
                   reconciliation where parent handles hook tracking.

    Returns:
        The mounted node with ID assigned (children empty until rendered)
    """
    from trellis.core.rendering import ElementState

    # Assign new ID (keep original children - they're descriptors from with block
    # that will be passed to render(), then replaced with mounted children)
    new_id = ctx.next_element_id()
    node_with_id = dataclass_replace(node, id=new_id)

    # Create ElementState and mark as mounted
    # (hooks are deferred but node is conceptually mounted now)
    state = ElementState(parent_id=parent_id, mounted=True)
    ctx._element_state[new_id] = state

    # Mark dirty so _render_dirty_nodes will render this node
    ctx.mark_dirty_id(new_id)

    # Track for mount hooks (called after render completes)
    ctx.track_mount(new_id)

    # Return node - children are descriptors from with block, will be replaced when rendered
    return node_with_id


def reconcile_node_children(
    old_children: list[ElementNode],
    new_children: list[ElementNode],
    parent_id: str,
    ctx: RenderTree,
) -> list[ElementNode]:
    """Reconcile old child nodes with new child nodes.

    Uses same multi-phase algorithm as reconcile_children but for ElementNode.

    Args:
        old_children: Current child nodes
        new_children: New child nodes
        parent_id: Parent node's ID
        ctx: The render tree

    Returns:
        List of reconciled child nodes
    """
    # Phase 1: Handle empty edge cases
    if not old_children:
        return [mount_new_node(child, parent_id, ctx, call_hooks=False) for child in new_children]

    if not new_children:
        for child in old_children:
            unmount_node_tree(child, ctx)
        return []

    old_len = len(old_children)
    new_len = len(new_children)
    result: list[ElementNode] = []
    matched_old_ids: set[str] = set()

    # Phase 2: Two-pointer scan from head
    head = 0
    while head < old_len and head < new_len:
        old_child = old_children[head]
        new_child = new_children[head]

        if old_child.key != new_child.key:
            break
        if old_child.component != new_child.component:
            break

        matched_old_ids.add(old_child.id)
        reconciled = reconcile_node(old_child, new_child, parent_id, ctx, call_hooks=False)
        result.append(reconciled)
        head += 1

    if head == old_len and head == new_len:
        return result

    # Phase 3: Two-pointer scan from tail
    tail_matches: list[ElementNode] = []
    old_tail = old_len - 1
    new_tail = new_len - 1

    while old_tail >= head and new_tail >= head:
        old_child = old_children[old_tail]
        new_child = new_children[new_tail]

        if old_child.key != new_child.key:
            break
        if old_child.component != new_child.component:
            break

        matched_old_ids.add(old_child.id)
        reconciled = reconcile_node(old_child, new_child, parent_id, ctx, call_hooks=False)
        tail_matches.append(reconciled)
        old_tail -= 1
        new_tail -= 1

    tail_matches.reverse()

    # Phase 4: Process middle section with key-based matching
    middle_old_start = head
    middle_old_end = old_tail + 1
    middle_new_start = head
    middle_new_end = new_tail + 1

    # Build lookup structures for O(1) matching
    keyed_old: dict[str, ElementNode] = {}
    unkeyed_old_by_type: dict[IComponent, list[ElementNode]] = {}
    for i in range(middle_old_start, middle_old_end):
        old_child = old_children[i]
        if old_child.id not in matched_old_ids:
            if old_child.key:
                keyed_old[old_child.key] = old_child
            else:
                unkeyed_old_by_type.setdefault(old_child.component, []).append(old_child)

    for i in range(middle_new_start, middle_new_end):
        new_child = new_children[i]
        matched: ElementNode | None = None

        if new_child.key:
            old = keyed_old.get(new_child.key)
            if old and old.component == new_child.component:
                if old.id not in matched_old_ids:
                    matched = old
        else:
            # O(1) lookup by component type instead of O(k) linear scan
            candidates = unkeyed_old_by_type.get(new_child.component, [])
            for old in candidates:
                if old.id not in matched_old_ids:
                    matched = old
                    break

        if matched:
            matched_old_ids.add(matched.id)
            reconciled = reconcile_node(matched, new_child, parent_id, ctx, call_hooks=False)
            result.append(reconciled)
        else:
            mounted = mount_new_node(new_child, parent_id, ctx, call_hooks=False)
            result.append(mounted)

    result.extend(tail_matches)

    # Phase 5: Unmount unmatched old nodes
    for old in old_children:
        if old.id not in matched_old_ids:
            unmount_node_tree(old, ctx)

    return result


def mount_node_tree(node: ElementNode, ctx: RenderTree) -> None:
    """Mount a node and all its descendants (ElementNode architecture).

    Mounting is performed parent-first. Hooks are tracked for deferred
    execution after the render phase completes.

    Args:
        node: The node to mount
        ctx: The render tree
    """
    state = ctx._element_state.get(node.id)
    if state is None or state.mounted:
        return

    state.mounted = True
    # Track mount hook (called after render completes)
    ctx.track_mount(node.id)

    for child in node.children:
        mount_node_tree(child, ctx)


def unmount_node_tree(node: ElementNode, ctx: RenderTree) -> None:
    """Unmount a node and all its descendants (ElementNode architecture).

    Unmounting is performed children-first. Hooks are tracked for deferred
    execution after the render phase completes. State cleanup is also deferred
    so hooks can access local_state.

    Args:
        node: The node to unmount
        ctx: The render tree
    """
    state = ctx._element_state.get(node.id)
    if state is None or not state.mounted:
        return

    # Unmount children first (depth-first)
    for child in node.children:
        unmount_node_tree(child, ctx)

    # Track unmount hook (called after render completes)
    # State cleanup is deferred to _process_pending_hooks so hooks can access local_state
    ctx.track_unmount(node.id)

    state.mounted = False
    ctx._dirty_ids.discard(node.id)


def call_mount_hooks(node_id: str, ctx: RenderTree) -> None:
    """Call on_mount() for all Stateful instances on a node.

    Exceptions are logged but not propagated, to ensure all mount hooks run.

    Args:
        node_id: The node's ID
        ctx: The render tree
    """
    state = ctx._element_state.get(node_id)
    if state is None:
        return

    # Get states sorted by call index
    items = list(state.local_state.items())
    items.sort(key=lambda x: x[0][1])
    for _, stateful in items:
        if hasattr(stateful, "on_mount"):
            try:
                stateful.on_mount()
            except Exception as e:
                logging.exception(f"Error in Stateful.on_mount: {e}")


def call_unmount_hooks(node_id: str, ctx: RenderTree) -> None:
    """Call on_unmount() for all Stateful instances on a node (reverse order).

    Args:
        node_id: The node's ID
        ctx: The render tree
    """
    state = ctx._element_state.get(node_id)
    if state is None:
        return

    # Get states sorted by call index, reversed
    items = list(state.local_state.items())
    items.sort(key=lambda x: x[0][1], reverse=True)
    for _, stateful in items:
        if hasattr(stateful, "on_unmount"):
            try:
                stateful.on_unmount()
            except Exception as e:
                logging.exception(f"Error in Stateful.on_unmount: {e}")
