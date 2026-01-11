"""Hot reload support for Trellis applications.

This module provides hot reload functionality using Jurigged to watch for
source code changes and automatically re-render active sessions.
"""

from __future__ import annotations

import asyncio
import sys
import threading
import typing as tp
import weakref
from pathlib import Path

from trellis.utils.logger import logger

if tp.TYPE_CHECKING:
    from trellis.core.rendering.session import RenderSession

__all__ = [
    "HotReload",
    "SessionRegistry",
    "get_hot_reload",
    "get_or_create_hot_reload",
    "is_user_module",
]

# Cache trellis package path for exclusion check
_TRELLIS_PATH: str | None = None


def _get_trellis_path() -> str:
    """Get the trellis package path (cached)."""
    global _TRELLIS_PATH
    if _TRELLIS_PATH is None:
        # hot_reload.py is at trellis/utils/hot_reload.py
        # trellis package root is two levels up
        _TRELLIS_PATH = str(Path(__file__).parent.parent)
    return _TRELLIS_PATH


def is_user_module(filename: str | None) -> bool:
    """Check if a filename belongs to a user application module.

    This filter is used to determine which modules should be watched for
    hot reload. It excludes:
    - None filenames
    - Standard library modules (under sys.prefix)
    - Site-packages (third-party packages)
    - The trellis package itself

    Args:
        filename: Absolute path to the module file, or None

    Returns:
        True if the module should be watched for hot reload
    """
    if filename is None:
        return False

    # Exclude stdlib (under sys.prefix)
    if filename.startswith(sys.prefix):
        return False

    # Exclude site-packages
    if "site-packages" in filename:
        return False

    # Exclude trellis package itself
    trellis_path = _get_trellis_path()
    if filename.startswith(trellis_path):
        return False

    return True


class SessionRegistry:
    """Registry of active RenderSession instances for hot reload.

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
        """Register a session for hot reload notifications.

        Args:
            session: The RenderSession to register
        """
        with self._lock:
            self._cleanup_dead_refs()
            self._sessions[id(session)] = weakref.ref(session)

    def unregister(self, session: RenderSession) -> None:
        """Unregister a session from hot reload notifications.

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
_hot_reload: HotReload | None = None


class HotReload:
    """Hot reload manager for Trellis applications.

    Watches for source code changes using Jurigged and triggers re-renders
    of all active sessions when code is updated.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Initialize hot reload manager.

        Args:
            loop: The asyncio event loop to use for marshaling callbacks.
                  If None, callbacks run directly on the watchdog thread.
        """
        self.sessions = SessionRegistry()
        self._watcher: tp.Any = None  # jurigged.live.Watcher
        self._loop = loop
        self._started = False

    def start(self) -> None:
        """Start watching for file changes.

        Sets up Jurigged to watch user application modules and register
        a callback for when code is reloaded.
        """
        if self._started:
            return

        from jurigged.live import Watcher
        from jurigged.register import registry

        # Register existing modules and install import sniffer for new ones
        registry.auto_register(filter=is_user_module)

        # Suppress Jurigged's built-in logging
        registry.set_logger(lambda x: None)

        # Create watcher and register postrun hook
        self._watcher = Watcher(registry, debounce=0.05)
        self._watcher.postrun.register(self._on_reload)
        self._watcher.start()

        self._started = True
        logger.info("Hot reload started")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
        self._started = False

    def _on_reload(self, path: str, codefile: tp.Any) -> None:
        """Handle file reload event from Jurigged.

        This is called from the watchdog thread, so we marshal to the
        asyncio event loop if one was provided.

        Args:
            path: Path to the reloaded file
            codefile: Jurigged CodeFile object
        """
        logger.info("Hot reload: %s", path)

        if self._loop is not None:
            # Marshal to asyncio event loop
            self._loop.call_soon_threadsafe(self._invalidate_all_sessions)
        else:
            # Run directly on watchdog thread
            self._invalidate_all_sessions()

    def _invalidate_all_sessions(self) -> None:
        """Mark all elements in all sessions as dirty.

        This forces a full re-render of all component trees, which is
        necessary because:
        1. Jurigged patches component methods but doesn't change instances
        2. The _place() REUSE CHECK compares component instances and props
        3. Without marking all elements dirty, children with unchanged props
           would be reused without re-executing their updated code
        """
        for session in self.sessions:
            for element_id in session.elements:
                session.dirty.mark(element_id)


def get_hot_reload() -> HotReload | None:
    """Get the global HotReload instance, if it exists.

    Returns:
        The global HotReload instance, or None if not created
    """
    return _hot_reload


def get_or_create_hot_reload(
    loop: asyncio.AbstractEventLoop | None = None,
) -> HotReload:
    """Get or create the global HotReload instance.

    Args:
        loop: The asyncio event loop to use (only used on first call)

    Returns:
        The global HotReload instance
    """
    global _hot_reload
    if _hot_reload is None:
        _hot_reload = HotReload(loop=loop)
    return _hot_reload
