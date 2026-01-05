"""Session-scoped state container."""

from __future__ import annotations

import asyncio
import contextvars
import re
import threading
import typing as tp
from dataclasses import dataclass, field

from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.element_state import ElementStateStore
from trellis.core.rendering.element_store import ElementStore

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
    """Get the currently active render session, if any."""
    return _active_session.get()


def set_active_session(session: RenderSession | None) -> None:
    """Set the active render session."""
    _active_session.set(session)


def is_render_active() -> bool:
    """Check if currently inside a render context."""
    session = _active_session.get()
    return session is not None and session.is_rendering()


# Pattern to parse prop paths: matches "name", "[0]", or ".name" segments
_PATH_SEGMENT_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)|^\[(\d+)\]|^\.([a-zA-Z_][a-zA-Z0-9_]*)")


@dataclass
class RenderSession:
    """Session-scoped state container."""

    root_component: Component
    root_element_id: str | None = None

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

    # Background tasks for async lifecycle hooks (prevents GC)
    _background_tasks: set[asyncio.Task[None]] = field(default_factory=set)

    # Initial URL path from client HelloMessage (for routing)
    initial_path: str = "/"

    def __post_init__(self) -> None:
        self.dirty.set_lock(self.lock)

    @property
    def root_element(self) -> Element | None:
        """Get the root element for this session."""
        if self.root_element_id is None:
            return None
        return self.elements.get(self.root_element_id)

    def is_rendering(self) -> bool:
        """Check if currently inside a render pass."""
        return self.active is not None

    def is_executing(self) -> bool:
        """Check if currently executing a component."""
        return self.active is not None and self.active.current_element_id is not None

    @property
    def current_element_id(self) -> str | None:
        """Get the ID of the element currently being executed."""
        if self.active is None:
            return None
        return self.active.current_element_id

    def get_callback(self, element_id: str, prop_name: str) -> tp.Callable[..., tp.Any] | None:
        """Get a callback from a element's props by path."""
        element = self.elements.get(element_id)
        if element is None:
            return None

        value = _resolve_prop_path(element.props, prop_name)

        if value is not None and callable(value):
            return tp.cast("tp.Callable[..., tp.Any]", value)
        return None


def _resolve_prop_path(props: dict[str, tp.Any], path: str) -> tp.Any:
    """Resolve a nested property path to its value."""
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
