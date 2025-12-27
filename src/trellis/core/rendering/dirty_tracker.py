"""Dirty node tracking for incremental rendering.

DirtyTracker manages the set of node IDs that need re-rendering.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator

__all__ = ["DirtyTracker"]


class DirtyTracker:
    """Tracks which node IDs are dirty and need re-rendering.

    Nodes are marked dirty when their state changes. The render loop
    processes dirty nodes and clears their dirty status.

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
            lock: The RLock to acquire when marking nodes dirty
        """
        self._lock = lock

    def mark(self, node_id: str) -> None:
        """Mark a node ID as dirty.

        Acquires the session lock to block if a render is in progress.
        This ensures state updates from other threads wait for render
        to complete before marking nodes dirty.

        Args:
            node_id: The ID of the node to mark dirty
        """
        if self._lock is not None:
            with self._lock:
                self._dirty_ids.add(node_id)
        else:
            self._dirty_ids.add(node_id)

    def clear(self, node_id: str) -> None:
        """Clear dirty status for a node ID.

        Args:
            node_id: The ID of the node to clear
        """
        self._dirty_ids.discard(node_id)

    def discard(self, node_id: str) -> None:
        """Remove a node ID from dirty set (alias for clear).

        Args:
            node_id: The ID of the node to remove
        """
        self._dirty_ids.discard(node_id)

    def has_dirty(self) -> bool:
        """Check if there are any dirty nodes.

        Returns:
            True if there are dirty nodes, False otherwise
        """
        return bool(self._dirty_ids)

    def pop_all(self) -> list[str]:
        """Pop and return all dirty IDs, clearing the set.

        Returns:
            List of all dirty node IDs
        """
        ids = list(self._dirty_ids)
        self._dirty_ids.clear()
        return ids

    def __contains__(self, node_id: str) -> bool:
        """Check if a node ID is dirty."""
        return node_id in self._dirty_ids

    def __len__(self) -> int:
        """Return number of dirty nodes."""
        return len(self._dirty_ids)

    def __iter__(self) -> Iterator[str]:
        """Iterate over dirty node IDs."""
        return iter(self._dirty_ids)
