"""State storage for element elements.

ElementStateStore provides storage for ElementState objects, keyed by element ID.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field

S = tp.TypeVar("S")

__all__ = ["ElementStateStore"]


@dataclass
class ElementState:
    """Mutable runtime state for an Element.

    ElementState holds all per-element mutable data (local state, context, etc.)
    keyed by element.id in RenderSession.state.

    Attributes:
        mounted: Whether on_mount() has been called
        local_state: Cached Stateful instances, keyed by (class, call_index)
        state_call_count: Counter for consistent Stateful() instantiation ordering
        context: State context from `with state:` blocks
        parent_id: Parent element's ID (for context walking)
        element_type: Element class type, for trait hook dispatch after removal
        _trait_state: Per-trait state keyed by state type
    """

    mounted: bool = False
    local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    state_call_count: int = 0
    context: dict[type, tp.Any] = field(default_factory=dict)
    _entered_context_types: set[type] = field(default_factory=set)
    parent_id: str | None = None
    element_type: type | None = None
    _trait_state: dict[type, tp.Any] = field(default_factory=dict)

    def trait(self, state_type: type[S]) -> S:
        """Get or create typed trait state.

        Each state_type gets a single instance, created on first access
        and cached for subsequent calls.
        """
        existing: S | None = self._trait_state.get(state_type)
        if existing is not None:
            return existing
        instance = state_type()
        self._trait_state[state_type] = instance
        return instance


class ElementStateStore:
    """Storage for ElementState objects, keyed by element ID.

    ElementState holds mutable runtime state for each element (dirty flag,
    local_state, context, etc.). This class provides a clean interface
    for state CRUD operations.
    """

    __slots__ = ("_state",)

    def __init__(self) -> None:
        self._state: dict[str, ElementState] = {}

    def get(self, element_id: str) -> ElementState | None:
        """Get state for an element ID.

        Args:
            element_id: The element's ID

        Returns:
            The ElementState, or None if not found
        """
        return self._state.get(element_id)

    def get_or_create(self, element_id: str) -> ElementState:
        """Get or create ElementState for an element ID.

        Args:
            element_id: The element's ID
        Returns:
            The ElementState for this element (created if needed)
        """

        if element_id not in self._state:
            self._state[element_id] = ElementState()
        return self._state[element_id]

    def set(self, element_id: str, state: ElementState) -> None:
        """Set state for an element ID.

        Args:
            element_id: The element's ID
            state: The ElementState to store
        """
        self._state[element_id] = state

    def remove(self, element_id: str) -> None:
        """Remove state for an element ID.

        Args:
            element_id: The ID of the element whose state to remove
        """
        self._state.pop(element_id, None)

    def __contains__(self, element_id: str) -> bool:
        """Check if state exists for an element ID."""
        return element_id in self._state

    def __len__(self) -> int:
        """Return number of states in the store."""
        return len(self._state)

    def __iter__(self) -> tp.Iterator[str]:
        """Iterate over element IDs with state."""
        return iter(self._state)

    def items(self) -> tp.ItemsView[str, ElementState]:
        """Return items view of (element_id, state) pairs."""
        return self._state.items()
