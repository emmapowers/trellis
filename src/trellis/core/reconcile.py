"""
React-like reconciliation algorithm for element trees.

This module implements a reconciliation algorithm inspired by React's approach,
used to efficiently update the element tree when components re-render. The goal
is to minimize DOM-like mutations by reusing existing elements where possible.

## Two-Phase Architecture

The rendering system uses two phases:
1. **Descriptor Creation**: Components return ElementDescriptors (no execution)
2. **Reconciliation/Execution**: Compare descriptors with existing Elements,
   execute components only when needed

## Matching Strategy

Elements are matched using a multi-phase approach for optimal performance:

1. **Two-pointer scan (head)**: Match elements from the start of both lists
   while component types match. Catches appends efficiently.

2. **Two-pointer scan (tail)**: Match elements from the end of both lists
   while component types match. Catches prepends efficiently.

3. **Key-based matching**: For the remaining "middle" section, use explicit
   keys for O(1) lookup when both old and new elements have keys.

4. **Linear fallback**: For non-keyed elements in the middle section, fall
   back to linear scan matching by component type.

## Complexity

- Best case (append/prepend): O(n) where n = list length
- Average case (keyed lists): O(n)
- Worst case (shuffled non-keyed): O(k²) where k = middle section size
"""

from __future__ import annotations

import logging
import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.rendering import Element, ElementDescriptor, RenderContext
    from trellis.core.state import Stateful


def reconcile(
    old_node: Element | None,
    new_desc: ElementDescriptor,
    parent: Element | None,
    ctx: RenderContext,
) -> Element:
    """
    Reconcile an old element (or None) with a new descriptor.

    This is the main entry point for reconciliation. It decides whether to:
    - Create a new element (if old_node is None or component changed)
    - Reuse the old element (if props unchanged and not dirty)
    - Update the old element (if props changed or dirty)

    Args:
        old_node: Existing element to reconcile against, or None for new mount
        new_desc: The new descriptor describing what to render
        parent: Parent element for the new/updated element
        ctx: The render context

    Returns:
        The reconciled element (may be old_node or a new element)
    """

    # Case 1: No old element - mount new
    if old_node is None:
        return mount_new(new_desc, parent, ctx)

    # Case 2: Component changed - unmount old, mount new
    if old_node.descriptor.component != new_desc.component:
        unmount_tree(old_node, ctx)
        return mount_new(new_desc, parent, ctx)

    # Case 3: Same component - check if we can skip execution
    if old_node.descriptor.props == new_desc.props and not old_node.dirty:
        # Props unchanged and not dirty - skip execution entirely!
        # But still need to reconcile children if they're descriptors
        if new_desc.children:
            old_node.children = reconcile_children(old_node.children, list(new_desc.children), ctx)
            fixup_children(old_node, old_node.children)
        return old_node

    # Case 4: Props changed or dirty - re-execute
    old_node.descriptor = new_desc
    old_node.dirty = False
    execute_and_reconcile(old_node, ctx)
    return old_node


def mount_new(
    desc: ElementDescriptor,
    parent: Element | None,
    ctx: RenderContext,
    *,
    defer_mount: bool = False,
) -> Element:
    """
    Create and mount a new element from a descriptor.

    Args:
        desc: The descriptor to mount
        parent: Parent element (None for root)
        ctx: The render context
        defer_mount: If True, don't mount the tree (caller will do it)

    Returns:
        The newly created and mounted element
    """
    from trellis.core.rendering import Element

    # Create the element
    element = Element(
        descriptor=desc,
        parent=parent,
        depth=parent.depth + 1 if parent else 0,
        render_context=ctx,
    )

    # Execute the component to get child descriptors (children created with defer_mount=True)
    execute_and_reconcile(element, ctx, defer_mount=True)

    # Mount the tree (parent first, then children)
    if not defer_mount:
        mount_tree(element, ctx)

    # Add to parent's children if parent exists
    if parent is not None:
        parent.children.append(element)

    return element


def execute_and_reconcile(
    element: Element, ctx: RenderContext, *, defer_mount: bool = False
) -> None:
    """
    Execute a component and reconcile its children.

    This sets up the execution context, calls component.execute(),
    then reconciles the resulting children.

    Args:
        element: The element to execute
        ctx: The render context
        defer_mount: If True, don't mount new children (caller will do it)
    """
    from trellis.core.rendering import _descriptor_stack, unfreeze_props

    # Get props including children if component has children param
    props = unfreeze_props(element.descriptor.props)
    has_children_param = getattr(element.component, "_has_children_param", False)
    if has_children_param:
        # Always pass children (may be empty list)
        props["children"] = list(element.descriptor.children)

    # Set up execution context
    old_executing = ctx.executing
    old_node = ctx._current_node
    ctx.executing = True
    ctx._current_node = element

    # Reset state call count for consistent hook ordering
    element._state_call_count = 0

    # Push a descriptor stack for any child descriptors created during execution
    _descriptor_stack.append([])

    try:
        # Execute the component
        element.component.execute(element, **props)

        # Get child descriptors created during execution
        child_descs = _descriptor_stack.pop()

        # Reconcile children
        if child_descs:
            element.children = reconcile_children(
                element.children, child_descs, ctx, defer_mount=defer_mount
            )
            fixup_children(element, element.children)
        elif not element.children:
            # No children created and no existing children - nothing to do
            pass
        else:
            # Had children before but none now - unmount all
            for child in element.children:
                unmount_tree(child, ctx)
            element.children = []

    finally:
        ctx.executing = old_executing
        ctx._current_node = old_node


def reconcile_children(
    old_children: list[Element],
    new_descs: list[ElementDescriptor],
    ctx: RenderContext,
    *,
    defer_mount: bool = False,
) -> list[Element]:
    """
    Reconcile old child elements with new child descriptors.

    Uses a multi-phase algorithm for efficient matching:
    1. Handle empty edge cases
    2. Two-pointer scan from head
    3. Two-pointer scan from tail
    4. Key-based matching for middle section
    5. Linear fallback for non-keyed elements
    6. Unmount unmatched old elements

    Args:
        old_children: Current child elements
        new_descs: New child descriptors
        ctx: The render context
        defer_mount: If True, don't mount new elements (caller will do it)

    Returns:
        List of reconciled elements
    """
    # Phase 1: Handle empty edge cases
    if not old_children:
        # All new - mount everything
        result = []
        for desc in new_descs:
            # Get parent from context
            parent = ctx._current_node
            elem = mount_new(desc, parent, ctx, defer_mount=defer_mount)
            # Remove from parent.children since mount_new adds it
            if parent and elem in parent.children:
                parent.children.remove(elem)
            result.append(elem)
        return result

    if not new_descs:
        # All removed - unmount everything
        for child in old_children:
            unmount_tree(child, ctx)
        return []

    old_len = len(old_children)
    new_len = len(new_descs)
    result: list[Element] = []
    matched_old_ids: set[int] = set()

    # Phase 2: Two-pointer scan from head
    head = 0
    while head < old_len and head < new_len:
        old_child = old_children[head]
        new_desc = new_descs[head]

        # Keys must match
        if old_child.key != new_desc.key:
            break

        # Component types must match
        if old_child.component != new_desc.component:
            break

        # Match found - reconcile
        matched_old_ids.add(id(old_child))
        reconcile(old_child, new_desc, old_child.parent, ctx)
        result.append(old_child)
        head += 1

    # If we matched everything, we're done
    if head == old_len and head == new_len:
        return result

    # Phase 3: Two-pointer scan from tail
    tail_matches: list[Element] = []
    old_tail = old_len - 1
    new_tail = new_len - 1

    while old_tail >= head and new_tail >= head:
        old_child = old_children[old_tail]
        new_desc = new_descs[new_tail]

        if old_child.key != new_desc.key:
            break

        if old_child.component != new_desc.component:
            break

        matched_old_ids.add(id(old_child))
        reconcile(old_child, new_desc, old_child.parent, ctx)
        tail_matches.append(old_child)
        old_tail -= 1
        new_tail -= 1

    tail_matches.reverse()

    # Phase 4: Process middle section
    middle_old_start = head
    middle_old_end = old_tail + 1
    middle_new_start = head
    middle_new_end = new_tail + 1

    # Build keyed lookup for unmatched old elements
    keyed_old: dict[str, Element] = {}
    for i in range(middle_old_start, middle_old_end):
        old_child = old_children[i]
        if old_child.key and id(old_child) not in matched_old_ids:
            keyed_old[old_child.key] = old_child

    # Process middle section
    for i in range(middle_new_start, middle_new_end):
        new_desc = new_descs[i]
        matched: Element | None = None

        if new_desc.key:
            # Key-based match
            old = keyed_old.get(new_desc.key)
            if old and old.component == new_desc.component:
                if id(old) not in matched_old_ids:
                    matched = old
        else:
            # Linear fallback for non-keyed
            for j in range(middle_old_start, middle_old_end):
                old = old_children[j]
                if id(old) not in matched_old_ids and old.component == new_desc.component:
                    if not old.key:
                        matched = old
                        break

        if matched:
            matched_old_ids.add(id(matched))
            reconcile(matched, new_desc, matched.parent, ctx)
            result.append(matched)
        else:
            # No match - mount new
            parent = ctx._current_node
            elem = mount_new(new_desc, parent, ctx, defer_mount=defer_mount)
            if parent and elem in parent.children:
                parent.children.remove(elem)
            result.append(elem)

    result.extend(tail_matches)

    # Phase 5: Unmount unmatched old elements
    for old in old_children:
        if id(old) not in matched_old_ids:
            unmount_tree(old, ctx)

    return result


def mount_tree(element: Element, ctx: RenderContext) -> None:
    """
    Mount an element and all its descendants.

    Mounting is performed parent-first (pre-order traversal).
    This ensures parents are initialized before children.

    Args:
        element: The element to mount
        ctx: The render context
    """
    if element._mounted:
        return

    element._mounted = True
    element.on_mount()

    # Mount states in creation order
    for state in get_states_for_element(ctx, element):
        state.on_mount()

    # Then mount children
    for child in element.children:
        mount_tree(child, ctx)


def unmount_tree(element: Element, ctx: RenderContext) -> None:
    """
    Unmount an element and all its descendants.

    Unmounting is performed children-first (post-order traversal).
    This ensures children can access parents during cleanup.

    Args:
        element: The element to unmount
        ctx: The render context
    """
    if not element._mounted:
        return

    # Unmount children first
    for child in element.children:
        unmount_tree(child, ctx)

    # Unmount states in reverse creation order
    for state in reversed(get_states_for_element(ctx, element)):
        try:
            state.on_unmount()
        except Exception as e:
            logging.exception(f"Error in Stateful.on_unmount: {e}")

    try:
        element.on_unmount()
    except Exception as e:
        logging.exception(f"Error in Element.on_unmount: {e}")

    element._mounted = False
    cleanup_element_state(ctx, element)


def fixup_children(parent: Element, children: list[Element]) -> None:
    """Update parent references and depths for a list of child elements.

    Called after reconciling children to ensure the tree structure is
    consistent. Each child gets its parent set and depth calculated.

    Args:
        parent: The parent element
        children: List of child elements to update
    """
    for child in children:
        child.parent = parent
        child.depth = parent.depth + 1


def get_states_for_element(ctx: RenderContext, element: Element) -> list[Stateful]:
    """Get all Stateful instances cached on an element, in creation order.

    State instances are keyed by (class, call_index) to ensure consistent
    ordering across re-renders (like React hooks).

    Args:
        ctx: The render context (unused but kept for API consistency)
        element: The element to get states from

    Returns:
        List of Stateful instances sorted by creation order (call index)
    """
    items = list(element._local_state.items())
    items.sort(key=lambda x: x[0][1])  # Sort by call index
    return [state for _, state in items]


def cleanup_element_state(ctx: RenderContext, element: Element) -> None:
    """Clean up an element's state when it's unmounted.

    This clears the local state cache, resets the state call counter,
    and removes the element from the dirty set.

    Args:
        ctx: The render context (to remove from dirty_elements)
        element: The element being cleaned up
    """
    element._local_state.clear()
    element._state_call_count = 0
    ctx.dirty_elements.discard(element)
