"""
React-like reconciliation algorithm for Element trees.

This module implements a reconciliation algorithm inspired by React's approach,
used to efficiently update the node tree when components re-render. The goal
is to minimize mutations by reusing existing nodes where possible.

## Architecture

The rendering system uses:
- **Element**: Immutable tree nodes with child_ids (references, not nested)
- **ElementState**: Mutable runtime state keyed by node ID (local_state, dirty flag, etc.)
- **RenderSession._nodes**: Flat storage of all nodes by ID

During reconciliation:
1. **Node Creation**: Components produce Element descriptors with IDs
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
from dataclasses import dataclass, field

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
