"""Session-scoped state container.

RenderSession holds state that persists across renders for a single session.
This is the target for the contextvar that tracks the active rendering context.
"""

from __future__ import annotations

import contextvars
import threading
import typing as tp
from dataclasses import dataclass, field

from trellis.core.dirty_tracker import DirtyTracker
from trellis.core.element_state import StateStore
from trellis.core.node_store import NodeStore

if tp.TYPE_CHECKING:
    from trellis.core.active_render import ActiveRender
    from trellis.core.component import Component

__all__ = [
    "RenderSession",
    "get_active_session",
    "is_render_active",
    "set_active_session",
]


# Thread-safe, task-local storage for the active render session.
# Using contextvars ensures each asyncio task or thread has its own context,
# enabling concurrent rendering (e.g., multiple WebSocket connections).
_active_session: contextvars.ContextVar[RenderSession | None] = contextvars.ContextVar(
    "active_session", default=None
)


def get_active_session() -> RenderSession | None:
    """Get the currently active render session, if any.

    Returns:
        The active RenderSession, or None if not currently rendering
    """
    return _active_session.get()


def set_active_session(session: RenderSession | None) -> None:
    """Set the active render session.

    This is called internally by render() to establish
    the current session for component execution.

    Args:
        session: The RenderSession to make active, or None to clear
    """
    _active_session.set(session)


def is_render_active() -> bool:
    """Check if currently inside a render context.

    Returns True if there is an active session with a node being executed.
    Used by Stateful and tracked collections to determine if dependency
    tracking should occur.

    Returns:
        True if inside render context, False otherwise
    """
    session = _active_session.get()
    return session is not None and session.is_executing()


@dataclass
class RenderSession:
    """Session-scoped state container.

    Holds state that persists across renders for a single session (e.g., one
    WebSocket connection). The contextvar points here to provide access to
    the current rendering context.

    Attributes:
        root_component: The top-level component for this session
        root_node_id: ID of the root node (after first render)
        nodes: Flat storage for all ElementNodes
        state: Storage for ElementState per node
        dirty: Tracker for dirty node IDs
        active: Render-scoped state (None when not rendering)
        lock: RLock for thread-safe operations
    """

    root_component: Component
    root_node_id: str | None = None

    # Fine-grained stores
    nodes: NodeStore = field(default_factory=NodeStore)
    state: StateStore = field(default_factory=StateStore)
    dirty: DirtyTracker = field(default_factory=DirtyTracker)

    # Render-scoped state (None when not rendering)
    active: ActiveRender | None = None

    # Thread safety
    lock: threading.RLock = field(default_factory=threading.RLock)

    # Render count - incremented at the start of each render pass
    render_count: int = 0

    def is_rendering(self) -> bool:
        """Check if currently inside a render pass.

        Returns:
            True if active is not None, False otherwise
        """
        return self.active is not None

    def is_executing(self) -> bool:
        """Check if currently executing a component.

        Returns:
            True if inside render and a node is being executed
        """
        return self.active is not None and self.active.current_node_id is not None

    @property
    def current_node_id(self) -> str | None:
        """Get the ID of the node currently being executed.

        Returns:
            The current node ID during execution, or None
        """
        if self.active is None:
            return None
        return self.active.current_node_id

    def get_callback(self, node_id: str, prop_name: str) -> tp.Callable[..., tp.Any] | None:
        """Get a callback from a node's props.

        Looks up the node by ID and finds the property. Returns the value
        if it's callable (including Mutable objects which have __call__).

        Args:
            node_id: The node's ID
            prop_name: The property name containing the callback

        Returns:
            The callable if found, None otherwise
        """
        node = self.nodes.get(node_id)
        if node is None:
            return None

        # node.props is a dict
        value = node.props.get(prop_name)

        if value is not None and callable(value):
            return tp.cast("tp.Callable[..., tp.Any]", value)
        return None
