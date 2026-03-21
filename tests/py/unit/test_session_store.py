"""Tests for SSR session store with TTL."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from trellis.platforms.server.session_store import SessionEntry, SessionStore


class TestSessionStore:
    def test_store_and_pop(self) -> None:
        store = SessionStore(ttl_seconds=30)
        entry = SessionEntry(
            session=MagicMock(),
            deferred_mounts=["el-1"],
            deferred_unmounts=[],
            patches=[],
        )
        store.store("session-1", entry)

        result = store.pop("session-1")
        assert result is entry

    def test_pop_removes_entry(self) -> None:
        store = SessionStore(ttl_seconds=30)
        entry = SessionEntry(
            session=MagicMock(),
            deferred_mounts=[],
            deferred_unmounts=[],
            patches=[],
        )
        store.store("session-1", entry)
        store.pop("session-1")

        assert store.pop("session-1") is None

    def test_pop_unknown_returns_none(self) -> None:
        store = SessionStore(ttl_seconds=30)
        assert store.pop("nonexistent") is None

    def test_pop_expired_returns_none(self) -> None:
        store = SessionStore(ttl_seconds=0.01)
        entry = SessionEntry(
            session=MagicMock(),
            deferred_mounts=[],
            deferred_unmounts=[],
            patches=[],
        )
        store.store("session-1", entry)
        time.sleep(0.02)

        assert store.pop("session-1") is None

    def test_cleanup_expired(self) -> None:
        store = SessionStore(ttl_seconds=0.01)
        entry = SessionEntry(
            session=MagicMock(),
            deferred_mounts=[],
            deferred_unmounts=[],
            patches=[],
        )
        store.store("session-1", entry)
        store.store("session-2", entry)
        time.sleep(0.02)

        store.cleanup_expired()
        assert store.pop("session-1") is None
        assert store.pop("session-2") is None

    def test_cleanup_keeps_valid(self) -> None:
        store = SessionStore(ttl_seconds=30)
        entry = SessionEntry(
            session=MagicMock(),
            deferred_mounts=[],
            deferred_unmounts=[],
            patches=[],
        )
        store.store("session-1", entry)
        store.cleanup_expired()

        result = store.pop("session-1")
        assert result is entry

    def test_multiple_sessions(self) -> None:
        store = SessionStore(ttl_seconds=30)
        entry_1 = SessionEntry(
            session=MagicMock(),
            deferred_mounts=["a"],
            deferred_unmounts=[],
            patches=[],
        )
        entry_2 = SessionEntry(
            session=MagicMock(),
            deferred_mounts=["b"],
            deferred_unmounts=[],
            patches=[],
        )
        store.store("s1", entry_1)
        store.store("s2", entry_2)

        assert store.pop("s1") is entry_1
        assert store.pop("s2") is entry_2
