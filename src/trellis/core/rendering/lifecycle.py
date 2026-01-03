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

    def track_mount(self, element_id: str) -> None:
        """Track an element for mount hook.

        Args:
            element_id: The ID of the newly mounted element
        """
        self._pending_mounts.append(element_id)

    def track_unmount(self, element_id: str) -> None:
        """Track an element for unmount hook.

        Args:
            element_id: The ID of the element being unmounted
        """
        self._pending_unmounts.append(element_id)

    def pop_mounts(self) -> list[str]:
        """Pop and return all pending mount element IDs.

        Returns:
            List of element IDs needing mount hooks called
        """
        mounts = list(self._pending_mounts)
        self._pending_mounts.clear()
        return mounts

    def pop_unmounts(self) -> list[str]:
        """Pop and return all pending unmount element IDs.

        Returns:
            List of element IDs needing unmount hooks called
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
