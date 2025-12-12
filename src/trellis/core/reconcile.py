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

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode, IComponent, RenderTree

from trellis.core.state import clear_node_dependencies


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

    # Case 4: Props changed or dirty - re-execute
    state.dirty = False
    return execute_node(node_with_id, parent_id, ctx, old_children=list(old_node.children))


def mount_new_node(
    node: ElementNode,
    parent_id: str | None,
    ctx: RenderTree,
    *,
    call_hooks: bool = True,
) -> ElementNode:
    """Create and mount a new node (ElementNode architecture).

    Assigns a new ID, creates ElementState, executes the component.

    Args:
        node: The node to mount (will have empty id)
        parent_id: Parent node's ID
        ctx: The render tree
        call_hooks: Whether to call mount hooks immediately. Set False for
                   bulk mounting where hooks are called later via mount_node_tree.

    Returns:
        The mounted node with ID and children populated
    """
    from trellis.core.rendering import ElementState

    # Assign new ID
    new_id = ctx.next_element_id()
    node_with_id = dataclass_replace(node, id=new_id)

    # Create ElementState
    state = ElementState(parent_id=parent_id)
    ctx._element_state[new_id] = state

    # Execute component to get children (don't call hooks recursively)
    result = execute_node(node_with_id, parent_id, ctx, call_hooks=call_hooks)

    if call_hooks:
        # Call hooks for this node and all descendants in parent-first order
        mount_node_tree(result, ctx)
    # Note: if call_hooks=False, caller is responsible for calling mount_node_tree

    return result


def execute_node(
    node: ElementNode,
    parent_id: str | None,
    ctx: RenderTree,
    old_children: list[ElementNode] | None = None,
    *,
    call_hooks: bool = True,
) -> ElementNode:
    """Execute a component and collect its children (ElementNode architecture).

    Args:
        node: The node to execute (must have id assigned)
        parent_id: Parent node's ID
        ctx: The render tree
        old_children: Previous children to reconcile against (None for initial mount)
        call_hooks: Whether to call mount hooks for children. Set False when
                   parent will call mount_node_tree to handle all hooks.

    Returns:
        Node with children populated from execution
    """
    from trellis.core.rendering import unfreeze_props

    # Get state for this node
    state = ctx.get_element_state(node.id)
    state.parent_id = parent_id

    # Get props including children if component accepts them
    props = unfreeze_props(node.props)
    has_children_param = getattr(node.component, "_has_children_param", False)
    if has_children_param:
        props["children"] = list(node.children)

    # Set up execution context
    old_executing = ctx.executing
    old_node_id = ctx._current_node_id
    ctx.executing = True
    ctx._current_node_id = node.id

    # Reset state call count for consistent hook ordering
    state.state_call_count = 0

    # Clear existing dependency tracking before re-execution
    # Dependencies will be re-registered fresh during execution
    clear_node_dependencies(node.id, state.watched_deps)

    # Push a frame for child nodes created during execution
    ctx.push_descriptor_frame()
    frame_popped = False

    try:
        # Execute the component (creates child nodes via component calls)
        node.component.execute(**props)

        # Get child nodes created during execution
        child_nodes = ctx.pop_descriptor_frame()
        frame_popped = True

        # Reconcile or mount children
        if child_nodes:
            # Reconcile with old children if this is a re-execution
            if old_children:
                new_children = reconcile_node_children(old_children, child_nodes, node.id, ctx)
            else:
                # Initial mount - mount all new children
                # Don't call hooks here - parent will call mount_node_tree
                new_children = [
                    mount_new_node(child, node.id, ctx, call_hooks=False) for child in child_nodes
                ]

            # Call mount hooks for any newly created children during re-render
            # For initial mount (old_children is None), parent's mount_node_tree handles this
            # mount_node_tree checks state.mounted and skips already-mounted nodes
            if call_hooks and old_children is not None:
                for child in new_children:
                    mount_node_tree(child, ctx)

            return dataclass_replace(node, children=tuple(new_children))

        # No new children created
        if old_children:
            # Had children before but none now - unmount all
            for child in old_children:
                unmount_node_tree(child, ctx)
        return dataclass_replace(node, children=())

    except BaseException:
        if not frame_popped:
            ctx.pop_descriptor_frame()
        raise

    finally:
        ctx.executing = old_executing
        ctx._current_node_id = old_node_id


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

    Mounting is performed parent-first.

    Args:
        node: The node to mount
        ctx: The render tree
    """
    state = ctx._element_state.get(node.id)
    if state is None or state.mounted:
        return

    state.mounted = True
    call_mount_hooks(node.id, ctx)

    for child in node.children:
        mount_node_tree(child, ctx)


def unmount_node_tree(node: ElementNode, ctx: RenderTree) -> None:
    """Unmount a node and all its descendants (ElementNode architecture).

    Unmounting is performed children-first.

    Args:
        node: The node to unmount
        ctx: The render tree
    """
    state = ctx._element_state.get(node.id)
    if state is None or not state.mounted:
        return

    # Unmount children first
    for child in node.children:
        unmount_node_tree(child, ctx)

    # Call unmount hooks
    call_unmount_hooks(node.id, ctx)

    state.mounted = False

    # Clean up dependency tracking before removing state
    clear_node_dependencies(node.id, state.watched_deps)

    # Clean up state
    ctx._element_state.pop(node.id, None)
    ctx._dirty_ids.discard(node.id)


def call_mount_hooks(node_id: str, ctx: RenderTree) -> None:
    """Call on_mount() for all Stateful instances on a node.

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
            stateful.on_mount()


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
