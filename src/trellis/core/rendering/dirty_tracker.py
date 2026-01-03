"""Dirty element tracking for incremental rendering.

DirtyTracker manages the set of element IDs that need re-rendering.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator

__all__ = ["DirtyTracker"]


class DirtyTracker:
    """Tracks which element IDs are dirty and need re-rendering.

    Elements are marked dirty when their state changes. The render loop
    processes dirty elements and clears their dirty status.

    The mark() method acquires the session lock to ensure that state
    updates from other threads block while a render is in progress.
    """

    __slots__ = ("_dirty_ids", "_lock")

    def __init__(self, lock: threading.RLock | None = None) -> None:
        self._dirty_ids: set[str] = set()
        self._lock = lock

    def set_lock(self, lock: threading.RLock) -> None:
        """Set the lock to use for thread-safe mark() operations.

        Args:
            lock: The RLock to acquire when marking elements dirty
        """
        self._lock = lock

    def mark(self, element_id: str) -> None:
        """Mark an element ID as dirty.

        Acquires the session lock to block if a render is in progress.
        This ensures state updates from other threads wait for render
        to complete before marking elements dirty.

        Args:
            element_id: The ID of the element to mark dirty
        """
        if self._lock is not None:
            with self._lock:
                self._dirty_ids.add(element_id)
        else:
            self._dirty_ids.add(element_id)

    def clear(self, element_id: str) -> None:
        """Clear dirty status for an element ID.

        Args:
            element_id: The ID of the element to clear
        """
        self._dirty_ids.discard(element_id)

    def discard(self, element_id: str) -> None:
        """Remove an element ID from dirty set (alias for clear).

        Args:
            element_id: The ID of the element to remove
        """
        self._dirty_ids.discard(element_id)

    def has_dirty(self) -> bool:
        """Check if there are any dirty elements.

        Returns:
            True if there are dirty elements, False otherwise
        """
        return bool(self._dirty_ids)

    def pop_all(self) -> list[str]:
        """Pop and return all dirty element IDs, clearing the set.

        Returns:
            List of all dirty element IDs
        """
        ids = list(self._dirty_ids)
        self._dirty_ids.clear()
        return ids

    def pop(self) -> str | None:
        """Pop and return one dirty ID, or None if empty.

        Returns:
            A dirty element ID, or None if no dirty elements
        """
        if self._dirty_ids:
            return self._dirty_ids.pop()
        return None

    def __contains__(self, element_id: str) -> bool:
        """Check if an element ID is dirty."""
        return element_id in self._dirty_ids

    def __len__(self) -> int:
        """Return number of dirty elements."""
        return len(self._dirty_ids)

    def __iter__(self) -> Iterator[str]:
        """Iterate over dirty element IDs."""
        return iter(self._dirty_ids)
