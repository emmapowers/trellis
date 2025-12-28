"""Session-scoped state container.

RenderSession holds state that persists across renders for a single session.
This is the target for the contextvar that tracks the active rendering context.
"""

from __future__ import annotations

import contextvars
import re
import threading
import typing as tp
from dataclasses import dataclass, field

from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.element_state import ElementStateStore
from trellis.core.rendering.elements import ElementStore

if tp.TYPE_CHECKING:
    from trellis.core.components.base import Component
    from trellis.core.rendering.active import ActiveRender
    from trellis.core.rendering.element import Element

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


# Pattern to parse prop paths: matches "name", "[0]", or ".name" segments
_PATH_SEGMENT_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)|^\[(\d+)\]|^\.([a-zA-Z_][a-zA-Z0-9_]*)")


@dataclass
class RenderSession:
    """Session-scoped state container.

    Holds state that persists across renders for a single session (e.g., one
    WebSocket connection). The contextvar points here to provide access to
    the current rendering context.

    Attributes:
        root_component: The top-level component for this session
        root_node_id: ID of the root element (after first render)
        elements: Flat storage for all Elements
        states: Storage for ElementState per element
        dirty: Tracker for dirty element IDs
        active: Render-scoped state (None when not rendering)
        lock: RLock for thread-safe operations
    """

    root_component: Component
    root_node_id: str | None = None

    # Fine-grained stores
    elements: ElementStore = field(default_factory=ElementStore)
    states: ElementStateStore = field(default_factory=ElementStateStore)
    dirty: DirtyTracker = field(default_factory=DirtyTracker)

    # Render-scoped state (None when not rendering)
    active: ActiveRender | None = None

    # Thread safety
    lock: threading.RLock = field(default_factory=threading.RLock)

    # Render count - incremented at the start of each render pass
    render_count: int = 0

    def __post_init__(self) -> None:
        """Link the dirty tracker to the session lock for thread-safe marking."""
        self.dirty.set_lock(self.lock)

    @property
    def root_element(self) -> Element | None:
        """Get the root element node for this session.

        Returns:
            The root Element, or None if not yet rendered
        """
        if self.root_node_id is None:
            return None
        return self.elements.get(self.root_node_id)

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

        Supports nested paths from serialization:
        - "on_click" -> props["on_click"]
        - "handlers[0]" -> props["handlers"][0]
        - "config.on_change" -> props["config"]["on_change"]
        - "handlers[0].callback" -> props["handlers"][0]["callback"]

        Args:
            node_id: The node's ID
            prop_name: The property name or path containing the callback

        Returns:
            The callable if found, None otherwise
        """
        node = self.elements.get(node_id)
        if node is None:
            return None

        value = _resolve_prop_path(node.props, prop_name)

        if value is not None and callable(value):
            return tp.cast("tp.Callable[..., tp.Any]", value)
        return None


def _resolve_prop_path(props: dict[str, tp.Any], path: str) -> tp.Any:
    """Resolve a nested property path to its value.

    Parses paths like:
    - "on_click" -> props["on_click"]
    - "handlers[0]" -> props["handlers"][0]
    - "config.on_change" -> props["config"]["on_change"]
    - "handlers[0].callback" -> props["handlers"][0]["callback"]

    Args:
        props: The props dict to traverse
        path: The property path to resolve

    Returns:
        The value at the path, or None if not found
    """
    value: tp.Any = props
    pos = 0

    while pos < len(path):
        match = _PATH_SEGMENT_RE.match(path[pos:])
        if not match:
            return None

        if match.group(1) is not None:
            # Initial identifier: props["name"]
            key = match.group(1)
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        elif match.group(2) is not None:
            # Array index: [0]
            idx = int(match.group(2))
            if not isinstance(value, (list, tuple)) or idx >= len(value):
                return None
            value = value[idx]
        elif match.group(3) is not None:
            # Dot accessor: .name
            key = match.group(3)
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]

        pos += match.end()

    return value
