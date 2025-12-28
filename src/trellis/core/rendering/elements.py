"""Element storage for the render tree.

ElementStore provides flat storage for Element objects, keyed by ID.
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import Element

__all__ = ["ElementStore"]


class ElementStore:
    """Flat storage for Element objects, keyed by ID.

    Elements are stored in a dictionary and accessed by their position-based ID.
    This class provides a clean interface for element CRUD operations and
    supports cloning for snapshot comparisons during reconciliation.
    """

    __slots__ = ("_nodes",)

    def __init__(self) -> None:
        self._nodes: dict[str, Element] = {}

    def get(self, node_id: str) -> Element | None:
        """Get a node by ID.

        Args:
            node_id: The node's ID

        Returns:
            The Element, or None if not found
        """
        return self._nodes.get(node_id)

    def store(self, node: Element) -> None:
        """Store a node by its ID.

        Args:
            node: The node to store (must have id assigned)
        """
        self._nodes[node.id] = node

    def remove(self, node_id: str) -> None:
        """Remove a node by ID.

        Args:
            node_id: The ID of the node to remove
        """
        self._nodes.pop(node_id, None)

    def get_children(self, node: Element) -> list[Element]:
        """Get child nodes for a parent node.

        Args:
            node: The parent node

        Returns:
            List of child Elements (looked up from storage)
        """
        return [self._nodes[cid] for cid in node.child_ids if cid in self._nodes]

    def clone(self) -> ElementStore:
        """Create a shallow copy of this store.

        Used to snapshot elements before render for diff comparison.

        Returns:
            New ElementStore with same element references
        """
        new_store = ElementStore()
        new_store._nodes = dict(self._nodes)
        return new_store

    def clear(self) -> None:
        """Remove all nodes from the store."""
        self._nodes.clear()

    def __len__(self) -> int:
        """Return number of nodes in the store."""
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if a node ID exists in the store."""
        return node_id in self._nodes

    def __iter__(self) -> tp.Iterator[str]:
        """Iterate over node IDs."""
        return iter(self._nodes)

    def items(self) -> tp.ItemsView[str, Element]:
        """Return items view of (node_id, node) pairs."""
        return self._nodes.items()
