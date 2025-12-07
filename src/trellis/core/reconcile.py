"""
React-like reconciliation algorithm for element trees.

This module implements a reconciliation algorithm inspired by React's approach,
used to efficiently update the element tree when components re-render. The goal
is to minimize DOM-like mutations by reusing existing elements where possible.

## Algorithm Overview

The reconciliation process compares old and new child lists to determine:
1. Which elements can be reused (matched by key or position+type)
2. Which elements need to be mounted (new additions)
3. Which elements need to be unmounted (removed)

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

## Usage Notes

- Always use keys for dynamic lists to ensure O(n) reconciliation
- Keys must be unique among siblings and stable across renders
- Component identity (same component function/class) is required for matching
"""

from __future__ import annotations

import logging
import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.rendering import Element, RenderContext
    from trellis.core.state import Stateful


def reconcile_children(
    old_children: list[Element],
    new_children: list[Element],
    context: RenderContext,
) -> list[Element]:
    """
    Reconcile old and new children using a React-like algorithm.

    This function compares two lists of child elements and produces a reconciled
    list that reuses old element instances where possible. This preserves element
    identity and any associated state.

    The algorithm uses a multi-phase approach:

    1. Handle empty edge cases (all new or all removed)
    2. Two-pointer scan from head - match consecutive elements from start
    3. Two-pointer scan from tail - match consecutive elements from end
    4. Key-based matching for middle section
    5. Linear fallback for non-keyed middle elements
    6. Unmount any unmatched old elements

    Args:
        old_children: Current child elements in the tree
        new_children: Newly rendered child elements
        context: The render context for mount/unmount operations

    Returns:
        List of reconciled elements, preserving old element identity where matched.
        New elements are mounted, unmatched old elements are unmounted.

    Complexity:
        - O(n) for appends, prepends, or keyed lists
        - O(k²) worst case where k = size of non-keyed middle section
    """
    # -------------------------------------------------------------------------
    # Phase 1: Handle empty edge cases
    # -------------------------------------------------------------------------
    if not old_children:
        # All new - mount everything
        for child in new_children:
            mount_tree(child, context)
        return list(new_children)

    if not new_children:
        # All removed - unmount everything
        for child in old_children:
            unmount_tree(child, context)
        return []

    old_len = len(old_children)
    new_len = len(new_children)
    result: list[Element] = []
    matched_old_ids: set[int] = set()

    # -------------------------------------------------------------------------
    # Phase 2: Two-pointer scan from head
    # Match consecutive elements from the start while component types match.
    # This efficiently handles the common case of appending to a list.
    # -------------------------------------------------------------------------
    head = 0
    while head < old_len and head < new_len:
        old_child = old_children[head]
        new_child = new_children[head]

        # Keys must match if present (None == None is fine for non-keyed)
        if old_child.key != new_child.key:
            break

        # Component types must match for reuse
        if old_child.component != new_child.component:
            break

        # Match found - update old element with new properties and reconcile
        matched_old_ids.add(id(old_child))
        update_element(old_child, new_child, context)
        result.append(old_child)
        head += 1

    # If we matched everything, we're done
    if head == old_len and head == new_len:
        return result

    # -------------------------------------------------------------------------
    # Phase 3: Two-pointer scan from tail
    # Match consecutive elements from the end while component types match.
    # This efficiently handles the common case of prepending to a list.
    # We build a separate list for tail matches and prepend later.
    # -------------------------------------------------------------------------
    tail_matches: list[Element] = []
    old_tail = old_len - 1
    new_tail = new_len - 1

    while old_tail >= head and new_tail >= head:
        old_child = old_children[old_tail]
        new_child = new_children[new_tail]

        # Keys must match if present
        if old_child.key != new_child.key:
            break

        # Component types must match
        if old_child.component != new_child.component:
            break

        # Match found - update and save for later (we're going backwards)
        matched_old_ids.add(id(old_child))
        update_element(old_child, new_child, context)
        tail_matches.append(old_child)
        old_tail -= 1
        new_tail -= 1

    # Reverse tail matches since we collected them backwards
    tail_matches.reverse()

    # -------------------------------------------------------------------------
    # Phase 4: Process middle section (between head and tail pointers)
    # For elements not matched by the two-pointer scans, use key-based
    # lookup first, then fall back to linear scan for non-keyed elements.
    # -------------------------------------------------------------------------

    # Build keyed lookup only for unmatched old elements in the middle
    middle_old_start = head
    middle_old_end = old_tail + 1  # exclusive
    middle_new_start = head
    middle_new_end = new_tail + 1  # exclusive

    keyed_old: dict[str, Element] = {}
    for i in range(middle_old_start, middle_old_end):
        old_child = old_children[i]
        if old_child.key and id(old_child) not in matched_old_ids:
            keyed_old[old_child.key] = old_child

    # Process middle section of new children
    for i in range(middle_new_start, middle_new_end):
        new_child = new_children[i]
        matched: Element | None = None

        if new_child.key:
            # Key-based match - O(1) lookup
            old = keyed_old.get(new_child.key)
            if old and old.component == new_child.component:
                if id(old) not in matched_old_ids:
                    matched = old
        else:
            # Linear fallback for non-keyed elements - O(k) per element
            # Only scan the middle section, not the entire old list
            for j in range(middle_old_start, middle_old_end):
                old = old_children[j]
                if id(old) not in matched_old_ids and old.component == new_child.component:
                    # Non-keyed old element can match non-keyed new element
                    if not old.key:
                        matched = old
                        break

        if matched:
            matched_old_ids.add(id(matched))
            update_element(matched, new_child, context)
            result.append(matched)
        else:
            # No match found - mount new element
            mount_tree(new_child, context)
            result.append(new_child)

    # Append tail matches
    result.extend(tail_matches)

    # -------------------------------------------------------------------------
    # Phase 5: Unmount unmatched old elements
    # Any old element not matched during reconciliation must be unmounted.
    # -------------------------------------------------------------------------
    for old in old_children:
        if id(old) not in matched_old_ids:
            unmount_tree(old, context)

    return result


def reconcile_element(
    old_element: Element,
    new_element: Element,
    context: RenderContext,
) -> None:
    """
    Reconcile an old element with a newly rendered element.

    Updates the old element's properties to match the new element and
    recursively reconciles their children. The old element's identity
    is preserved, maintaining any associated state.

    Args:
        old_element: The existing element in the tree to update
        new_element: The newly rendered element with updated properties
        context: The render context for child reconciliation

    Note:
        This function modifies old_element in place. After reconciliation,
        old_element will have new_element's properties and reconciled children.
    """
    old_element.properties = new_element.properties
    old_element.children = reconcile_children(
        old_element.children, new_element.children, context
    )

    # Update parent references and depths for reconciled children
    for child in old_element.children:
        child.parent = old_element
        child.depth = old_element.depth + 1


def mount_tree(element: Element, context: RenderContext) -> None:
    """
    Mount an element and all its descendants.

    Mounting is performed parent-first, then children (pre-order traversal).
    This ensures parents are fully initialized before their children attempt
    to access them.

    The mount process:
    1. Mark element as mounted
    2. Call element's on_mount() lifecycle hook
    3. Call on_mount() for each Stateful instance associated with the element
    4. Recursively mount all children

    Args:
        element: The element to mount
        context: The render context (used for state lookup)

    Note:
        This function is idempotent - already-mounted elements are skipped.
    """
    if element._mounted:
        return

    element._mounted = True
    element.on_mount()

    # Mount states for this element (in creation order)
    for state in get_states_for_element(context, element):
        state.on_mount()

    # Then mount children (depth-first)
    for child in element.children:
        mount_tree(child, context)


def unmount_tree(element: Element, context: RenderContext) -> None:
    """
    Unmount an element and all its descendants.

    Unmounting is performed children-first, then parent (post-order traversal).
    This ensures children can still access their parent during cleanup.

    The unmount process:
    1. Recursively unmount all children
    2. Call on_unmount() for each Stateful instance (reverse creation order)
    3. Call element's on_unmount() lifecycle hook
    4. Mark element as unmounted
    5. Clean up element's state cache

    Args:
        element: The element to unmount
        context: The render context (used for state cleanup)

    Note:
        This function is idempotent - already-unmounted elements are skipped.
        Exceptions in lifecycle hooks are logged but don't prevent cleanup.
    """
    if not element._mounted:
        return

    # Unmount children first (depth-first, post-order)
    for child in element.children:
        unmount_tree(child, context)

    # Unmount states in reverse creation order
    for state in reversed(get_states_for_element(context, element)):
        try:
            state.on_unmount()
        except Exception as e:
            logging.exception(f"Error in Stateful.on_unmount: {e}")

    # Then unmount self
    try:
        element.on_unmount()
    except Exception as e:
        logging.exception(f"Error in Element.on_unmount: {e}")

    element._mounted = False

    # Clean up state cache to prevent memory leaks
    cleanup_element_state(context, element)


def update_element(old: Element, new: Element, context: RenderContext) -> None:
    """
    Update an existing element with new properties and reconcile children.

    This is the core update operation during reconciliation. The old element's
    identity is preserved while its properties are replaced with new values.
    Children are recursively reconciled.

    Args:
        old: The existing element to update
        new: The new element with updated properties
        context: The render context for child reconciliation

    Note:
        After this call, old.properties == new.properties and old.children
        contains the reconciled child list.
    """
    old.properties = new.properties
    old.children = reconcile_children(old.children, new.children, context)

    # Update parent references and depths for reconciled children
    for child in old.children:
        child.parent = old
        child.depth = old.depth + 1


def get_states_for_element(ctx: RenderContext, element: Element) -> list[Stateful]:
    """
    Get all Stateful instances associated with an element.

    Returns Stateful instances in creation order, which is important for
    consistent lifecycle hook ordering (mount in creation order, unmount
    in reverse).

    Args:
        ctx: The render context (currently unused but kept for API consistency)
        element: The element to get states for

    Returns:
        List of Stateful instances, sorted by creation order (call index).
    """
    items = list(element._local_state.items())
    # Sort by call index (second element of the (type, index) key tuple)
    items.sort(key=lambda x: x[0][1])
    return [state for _, state in items]


def cleanup_element_state(ctx: RenderContext, element: Element) -> None:
    """
    Clean up an element's state cache and remove from dirty tracking.

    Called during unmount to prevent memory leaks. Clears the element's
    local state cache and removes it from the context's dirty set.

    Args:
        ctx: The render context containing the dirty elements set
        element: The element to clean up
    """
    element._local_state.clear()
    element._state_call_count = 0
    ctx.dirty_elements.discard(element)
