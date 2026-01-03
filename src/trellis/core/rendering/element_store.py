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

    __slots__ = ("_elements",)

    def __init__(self) -> None:
        self._elements: dict[str, Element] = {}

    def get(self, element_id: str) -> Element | None:
        """Get an element by ID.

        Args:
            element_id: The element's ID
        Returns:
            The Element, or None if not found
        """
        return self._elements.get(element_id)

    def store(self, element: Element) -> None:
        """Store an element by its ID.

        Args:
            element: The element to store (must have id assigned)
        """
        self._elements[element.id] = element

    def remove(self, element_id: str) -> None:
        """Remove an element by ID.

        Args:
            element_id: The ID of the element to remove
        """
        self._elements.pop(element_id, None)

    def get_children(self, element: Element) -> list[Element]:
        """Get child elements for a parent element.

        Args:
            element: The parent element

        Returns:
            List of child Elements (looked up from storage)
        """
        return [self._elements[cid] for cid in element.child_ids if cid in self._elements]

    def clone(self) -> ElementStore:
        """Create a shallow copy of this store.

        Used to snapshot elements before render for diff comparison.

        Returns:
            New ElementStore with same element references
        """
        new_store = ElementStore()
        new_store._elements = dict(self._elements)
        return new_store

    def clear(self) -> None:
        """Remove all elements from the store."""
        self._elements.clear()

    def __len__(self) -> int:
        """Return number of elements in the store."""
        return len(self._elements)

    def __contains__(self, element_id: str) -> bool:
        """Check if an element ID exists in the store."""
        return element_id in self._elements

    def __iter__(self) -> tp.Iterator[str]:
        """Iterate over element IDs."""
        return iter(self._elements)

    def items(self) -> tp.ItemsView[str, Element]:
        """Return items view of (element_id, element) pairs."""
        return self._elements.items()
