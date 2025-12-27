"""Node storage for the render tree.

NodeStore provides flat storage for ElementNode objects, keyed by ID.
"""

from __future__ import annotations

import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import ElementNode

__all__ = ["NodeStore"]


class NodeStore:
    """Flat storage for ElementNode objects, keyed by ID.

    Nodes are stored in a dictionary and accessed by their position-based ID.
    This class provides a clean interface for node CRUD operations and
    supports cloning for snapshot comparisons during reconciliation.
    """

    __slots__ = ("_nodes",)

    def __init__(self) -> None:
        self._nodes: dict[str, ElementNode] = {}

    def get(self, node_id: str) -> ElementNode | None:
        """Get a node by ID.

        Args:
            node_id: The node's ID

        Returns:
            The ElementNode, or None if not found
        """
        return self._nodes.get(node_id)

    def store(self, node: ElementNode) -> None:
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

    def get_children(self, node: ElementNode) -> list[ElementNode]:
        """Get child nodes for a parent node.

        Args:
            node: The parent node

        Returns:
            List of child ElementNodes (looked up from storage)
        """
        return [self._nodes[cid] for cid in node.child_ids if cid in self._nodes]

    def clone(self) -> NodeStore:
        """Create a shallow copy of this store.

        Used to snapshot nodes before render for diff comparison.

        Returns:
            New NodeStore with same node references
        """
        new_store = NodeStore()
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

    def items(self) -> tp.ItemsView[str, ElementNode]:
        """Return items view of (node_id, node) pairs."""
        return self._nodes.items()
