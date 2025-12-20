"""Collection conversion utilities for reactive state tracking.

This module provides utilities to convert plain Python collections (list, dict, set)
to their tracked equivalents (TrackedList, TrackedDict, TrackedSet) for use with
Stateful objects.

The conversion is recursive - nested collections are also converted.
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.state import Stateful

from trellis.core.tracked import TrackedDict, TrackedList, TrackedSet

__all__ = ["convert_to_tracked"]


def convert_to_tracked(
    value: tp.Any,
    owner: Stateful | None = None,
    attr: str = "",
) -> tp.Any:
    """Recursively convert plain collections to tracked versions.

    Converts list -> TrackedList, dict -> TrackedDict, set -> TrackedSet.
    Nested collections are also converted recursively.

    Already-tracked collections are rebound to the new owner/attr.

    Args:
        value: The value to potentially convert
        owner: The Stateful instance that owns this collection
        attr: The attribute name on owner where this is stored

    Returns:
        The converted value (or original if not a collection)
    """
    val_type = type(value)

    # Fast path: exact type match for plain collections
    if val_type is list:
        converted_list = [
            convert_to_tracked(item, owner, f"{attr}[{i}]") for i, item in enumerate(value)
        ]
        return TrackedList(converted_list, owner=owner, attr=attr)

    if val_type is dict:
        converted_dict = {
            k: convert_to_tracked(v, owner, f"{attr}[{k!r}]") for k, v in value.items()
        }
        return TrackedDict(converted_dict, owner=owner, attr=attr)

    if val_type is set:
        # Sets contain hashable items, which typically aren't collections
        # So we don't recurse into set items
        return TrackedSet(value, owner=owner, attr=attr)

    # Already a tracked collection - rebind to new owner if provided
    if isinstance(value, (TrackedList, TrackedDict, TrackedSet)):
        if owner is not None:
            value._bind(owner, attr)
        return value

    # Not a collection - return as-is
    return value
