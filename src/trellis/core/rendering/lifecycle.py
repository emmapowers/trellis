"""Lifecycle hook tracking for mount/unmount.

LifecycleTracker manages pending mount and unmount hooks to be called
after the render phase completes.
"""

from __future__ import annotations

__all__ = ["LifecycleTracker"]


class LifecycleTracker:
    """Tracks pending mount and unmount hooks.

    Mount and unmount hooks are tracked during rendering and processed
    after the tree is fully built. This ensures hooks can safely access
    the complete tree state.
    """

    __slots__ = ("_pending_mounts", "_pending_unmounts")

    def __init__(self) -> None:
        self._pending_mounts: list[str] = []
        self._pending_unmounts: list[str] = []

    def track_mount(self, node_id: str) -> None:
        """Track a node for mount hook.

        Args:
            node_id: The ID of the newly mounted node
        """
        self._pending_mounts.append(node_id)

    def track_unmount(self, node_id: str) -> None:
        """Track a node for unmount hook.

        Args:
            node_id: The ID of the node being unmounted
        """
        self._pending_unmounts.append(node_id)

    def pop_mounts(self) -> list[str]:
        """Pop and return all pending mount node IDs.

        Returns:
            List of node IDs needing mount hooks called
        """
        mounts = list(self._pending_mounts)
        self._pending_mounts.clear()
        return mounts

    def pop_unmounts(self) -> list[str]:
        """Pop and return all pending unmount node IDs.

        Returns:
            List of node IDs needing unmount hooks called
        """
        unmounts = list(self._pending_unmounts)
        self._pending_unmounts.clear()
        return unmounts

    def has_pending(self) -> bool:
        """Check if there are any pending hooks.

        Returns:
            True if there are pending mount or unmount hooks
        """
        return bool(self._pending_mounts) or bool(self._pending_unmounts)

    def clear(self) -> None:
        """Clear all pending hooks."""
        self._pending_mounts.clear()
        self._pending_unmounts.clear()
