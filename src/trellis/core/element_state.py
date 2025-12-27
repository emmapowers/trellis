"""State storage for element nodes.

StateStore provides storage for ElementState objects, keyed by node ID.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode

__all__ = ["StateStore"]

@dataclass
class ElementState:
    """Mutable runtime state for an ElementNode.

    ElementState holds all per-node mutable data (local state, context, etc.)
    keyed by node.id in RenderSession.state.

    Attributes:
        dirty: Whether this node needs re-rendering
        mounted: Whether on_mount() has been called
        local_state: Cached Stateful instances, keyed by (class, call_index)
        state_call_count: Counter for consistent Stateful() instantiation ordering
        context: State context from `with state:` blocks
        parent_id: Parent node's ID (for context walking)
    """

    dirty: bool = False
    mounted: bool = False
    local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    state_call_count: int = 0
    context: dict[type, tp.Any] = field(default_factory=dict)
    parent_id: str | None = None
    # Keep reference to node registered in WeakSets during render
    # This prevents GC until the next render when it's replaced
    _render_node: ElementNode | None = None
    

class StateStore:
    """Storage for ElementState objects, keyed by node ID.

    ElementState holds mutable runtime state for each node (dirty flag,
    local_state, context, etc.). This class provides a clean interface
    for state CRUD operations.
    """

    __slots__ = ("_state",)

    def __init__(self) -> None:
        self._state: dict[str, ElementState] = {}

    def get(self, node_id: str) -> ElementState | None:
        """Get state for a node ID.

        Args:
            node_id: The node's ID

        Returns:
            The ElementState, or None if not found
        """
        return self._state.get(node_id)

    def get_or_create(self, node_id: str) -> ElementState:
        """Get or create ElementState for a node ID.

        Args:
            node_id: The node's ID

        Returns:
            The ElementState for this node (created if needed)
        """

        if node_id not in self._state:
            self._state[node_id] = ElementState()
        return self._state[node_id]

    def set(self, node_id: str, state: ElementState) -> None:
        """Set state for a node ID.

        Args:
            node_id: The node's ID
            state: The ElementState to store
        """
        self._state[node_id] = state

    def remove(self, node_id: str) -> None:
        """Remove state for a node ID.

        Args:
            node_id: The ID of the node whose state to remove
        """
        self._state.pop(node_id, None)

    def __contains__(self, node_id: str) -> bool:
        """Check if state exists for a node ID."""
        return node_id in self._state

    def __len__(self) -> int:
        """Return number of states in the store."""
        return len(self._state)

    def __iter__(self) -> tp.Iterator[str]:
        """Iterate over node IDs with state."""
        return iter(self._state)

    def items(self) -> tp.ItemsView[str, ElementState]:
        """Return items view of (node_id, state) pairs."""
        return self._state.items()
