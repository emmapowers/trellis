"""In-memory session store with TTL for SSR session resumption."""

from __future__ import annotations

import threading
import time
import typing as tp
from dataclasses import dataclass, field

if tp.TYPE_CHECKING:
    from trellis.core.rendering.session import RenderSession
    from trellis.platforms.common.messages import Patch

__all__ = [
    "SessionEntry",
    "SessionStore",
]


@dataclass
class SessionEntry:
    """A stored SSR session awaiting WebSocket resumption."""

    session: RenderSession
    deferred_mounts: list[str]
    deferred_unmounts: list[str]
    patches: list[Patch]
    created_at: float = field(default_factory=time.monotonic)


class SessionStore:
    """Thread-safe in-memory store for SSR sessions with TTL expiry."""

    def __init__(self, ttl_seconds: float = 30) -> None:
        self._ttl = ttl_seconds
        self._entries: dict[str, SessionEntry] = {}
        self._lock = threading.Lock()

    def store(self, session_id: str, entry: SessionEntry) -> None:
        """Store a session entry."""
        with self._lock:
            self._entries[session_id] = entry

    def pop(self, session_id: str) -> SessionEntry | None:
        """Remove and return a session entry if it exists and hasn't expired."""
        with self._lock:
            entry = self._entries.pop(session_id, None)
            if entry is None:
                return None
            if time.monotonic() - entry.created_at > self._ttl:
                return None
            return entry

    def cleanup_expired(self) -> None:
        """Remove all expired entries."""
        now = time.monotonic()
        with self._lock:
            expired = [
                sid for sid, entry in self._entries.items() if now - entry.created_at > self._ttl
            ]
            for sid in expired:
                del self._entries[sid]
