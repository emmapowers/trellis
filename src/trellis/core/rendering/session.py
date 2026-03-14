"""Session-scoped state container."""

from __future__ import annotations

import asyncio
import contextvars
import logging
import re
import threading
import typing as tp
import weakref
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
    "SessionRegistry",
    "get_render_session",
    "get_session_registry",
    "is_render_active",
    "set_render_session",
]

logger = logging.getLogger(__name__)


# Task-local storage for the render session bound to this connection.
# Using contextvars ensures each asyncio task or thread has its own context,
# enabling concurrent rendering (e.g., multiple WebSocket connections).
_render_session: contextvars.ContextVar[RenderSession | None] = contextvars.ContextVar(
    "render_session", default=None
)


def get_render_session() -> RenderSession | None:
    """Get the render session for the current connection, if any."""
    return _render_session.get()


def set_render_session(session: RenderSession | None) -> None:
    """Set the render session for the current connection."""
    _render_session.set(session)


def is_render_active() -> bool:
    """Check if currently inside a render context."""
    session = _render_session.get()
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

    # Session-scoped async tasks for non-critical background work.
    _tasks: set[asyncio.Task[tp.Any]] = field(default_factory=set)
    _shutting_down: bool = False

    # Initial URL path from client HelloMessage (for routing)
    initial_path: str = "/"

    def __post_init__(self) -> None:
        self.dirty.set_lock(self.lock)

    def spawn[T](
        self,
        coro: tp.Coroutine[tp.Any, tp.Any, T],
        *,
        label: str,
    ) -> asyncio.Task[T]:
        """Create and track a session-scoped task for non-critical background work."""
        if self._shutting_down:
            coro.close()
            raise RuntimeError("Cannot spawn task on a shutting down session.")

        async def run_managed_task() -> T | None:
            try:
                return await coro
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in %s", label)
                return None

        task = tp.cast("asyncio.Task[T]", asyncio.create_task(run_managed_task()))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self) -> None:
        """Cancel and await all remaining session-scoped tasks."""
        if self._shutting_down:
            return

        self._shutting_down = True
        current_task = asyncio.current_task()
        tasks_to_cancel = [task for task in self._tasks if task is not current_task]

        for task in tasks_to_cancel:
            task.cancel()

        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

        self._tasks.clear()

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


class SessionRegistry:
    """Registry of active RenderSession instances.

    Uses weak references to automatically remove sessions when they are
    garbage collected (e.g., when a WebSocket connection closes).

    Note: RenderSession is a dataclass and unhashable, so we can't use
    WeakSet directly. Instead we use a dict keyed by id() with weakref values.
    """

    def __init__(self) -> None:
        # Dict mapping id(session) -> weakref.ref(session)
        self._sessions: dict[int, weakref.ref[RenderSession]] = {}
        self._lock = threading.Lock()

    def _cleanup_dead_refs(self) -> None:
        """Remove any dead weak references from the registry."""
        dead_ids = [sid for sid, ref in self._sessions.items() if ref() is None]
        for sid in dead_ids:
            del self._sessions[sid]

    def register(self, session: RenderSession) -> None:
        """Register a session.

        Args:
            session: The RenderSession to register
        """
        with self._lock:
            self._cleanup_dead_refs()
            self._sessions[id(session)] = weakref.ref(session)

    def unregister(self, session: RenderSession) -> None:
        """Unregister a session.

        Args:
            session: The RenderSession to unregister
        """
        with self._lock:
            self._sessions.pop(id(session), None)

    def __iter__(self) -> tp.Iterator[RenderSession]:
        """Iterate over registered sessions.

        Returns a snapshot of live sessions to avoid issues with concurrent
        modification during iteration. Dead references are skipped.
        """
        with self._lock:
            self._cleanup_dead_refs()
            # Dereference and filter out any None values
            sessions: list[RenderSession] = []
            for ref in self._sessions.values():
                session = ref()
                if session is not None:
                    sessions.append(session)
            return iter(sessions)

    def __len__(self) -> int:
        """Return the number of registered sessions."""
        with self._lock:
            self._cleanup_dead_refs()
            return len(self._sessions)


# Global singleton instance
_session_registry: SessionRegistry | None = None


def get_session_registry() -> SessionRegistry:
    """Get the global SessionRegistry instance, creating it if needed.

    Returns:
        The global SessionRegistry instance
    """
    global _session_registry
    if _session_registry is None:
        _session_registry = SessionRegistry()
    return _session_registry
