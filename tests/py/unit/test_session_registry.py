"""Unit tests for SessionRegistry."""

from __future__ import annotations

from trellis.core.rendering.session import RenderSession, SessionRegistry


class TestSessionRegistry:
    """Tests for SessionRegistry."""

    def test_register_and_iterate(self, noop_component) -> None:
        """Registered sessions appear in iteration."""
        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)

        registry.register(session)

        sessions = list(registry)
        assert session in sessions

    def test_unregister_removes_session(self, noop_component) -> None:
        """Unregistered sessions don't appear in iteration."""
        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)

        registry.register(session)
        registry.unregister(session)

        sessions = list(registry)
        assert session not in sessions

    def test_len_counts_active_sessions(self, noop_component) -> None:
        """len() returns count of registered sessions."""
        registry = SessionRegistry()
        s1 = RenderSession(root_component=noop_component)
        s2 = RenderSession(root_component=noop_component)

        assert len(registry) == 0
        registry.register(s1)
        assert len(registry) == 1
        registry.register(s2)
        assert len(registry) == 2

    def test_dead_refs_cleaned_on_iteration(self, noop_component) -> None:
        """Dead weak refs are cleaned up during iteration."""
        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)
        registry.register(session)

        # Delete session, making the weakref dead
        del session

        # Iteration should clean up dead refs
        sessions = list(registry)
        assert len(sessions) == 0
        assert len(registry) == 0

    def test_register_same_session_twice(self, noop_component) -> None:
        """Registering the same session twice doesn't duplicate."""
        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)

        registry.register(session)
        registry.register(session)

        assert len(registry) == 1

    def test_unregister_nonexistent_session(self, noop_component) -> None:
        """Unregistering a non-registered session is safe."""
        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)

        # Should not raise
        registry.unregister(session)
