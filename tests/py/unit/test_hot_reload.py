"""Unit tests for hot reload functionality."""

from __future__ import annotations

import sys
from pathlib import Path


class TestIsUserModule:
    """Tests for the is_user_module() filter function."""

    def test_excludes_none(self) -> None:
        """None filename should be excluded."""
        from trellis.utils.hot_reload import is_user_module

        assert is_user_module(None) is False

    def test_excludes_stdlib_paths(self) -> None:
        """Stdlib paths (under sys.prefix) should be excluded."""
        from trellis.utils.hot_reload import is_user_module

        # sys.prefix is typically something like /usr/local or ~/.pyenv/...
        stdlib_path = f"{sys.prefix}/lib/python3.13/os.py"
        assert is_user_module(stdlib_path) is False

    def test_excludes_site_packages(self) -> None:
        """Site-packages paths should be excluded."""
        from trellis.utils.hot_reload import is_user_module

        site_packages_path = "/some/path/site-packages/requests/__init__.py"
        assert is_user_module(site_packages_path) is False

    def test_excludes_trellis_package(self) -> None:
        """Trellis package itself should be excluded."""
        # Get actual trellis path
        import trellis
        from trellis.utils.hot_reload import is_user_module

        trellis_path = Path(trellis.__file__).parent
        trellis_module = str(trellis_path / "core" / "rendering" / "render.py")
        assert is_user_module(trellis_module) is False

    def test_includes_user_application_paths(self) -> None:
        """User application paths should be included."""
        from trellis.utils.hot_reload import is_user_module

        # A path that's not in stdlib, site-packages, or trellis
        user_app_path = "/home/user/myapp/main.py"
        assert is_user_module(user_app_path) is True

    def test_includes_current_directory_paths(self) -> None:
        """Paths in current working directory should be included."""
        from trellis.utils.hot_reload import is_user_module

        # Relative-looking absolute path
        user_app_path = "/Users/developer/projects/myapp/app.py"
        assert is_user_module(user_app_path) is True


class TestSessionRegistry:
    """Tests for the SessionRegistry class."""

    def test_register_session(self, noop_component) -> None:
        """Can register a session."""
        from trellis.core.rendering.session import RenderSession
        from trellis.utils.hot_reload import SessionRegistry

        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)

        registry.register(session)
        assert session in list(registry)

    def test_iterate_sessions(self, noop_component) -> None:
        """Can iterate over registered sessions."""
        from trellis.core.rendering.session import RenderSession
        from trellis.utils.hot_reload import SessionRegistry

        registry = SessionRegistry()
        session1 = RenderSession(root_component=noop_component)
        session2 = RenderSession(root_component=noop_component)

        registry.register(session1)
        registry.register(session2)

        sessions = list(registry)
        assert len(sessions) == 2
        assert session1 in sessions
        assert session2 in sessions

    def test_auto_removal_on_gc(self, noop_component) -> None:
        """Sessions are automatically removed when garbage collected."""
        import gc

        from trellis.core.rendering.session import RenderSession
        from trellis.utils.hot_reload import SessionRegistry

        registry = SessionRegistry()
        session = RenderSession(root_component=noop_component)

        registry.register(session)
        assert len(list(registry)) == 1

        # Delete the session and force GC
        del session
        gc.collect()

        # Session should be automatically removed from registry
        assert len(list(registry)) == 0

    def test_len(self, noop_component) -> None:
        """Can get length of registry."""
        from trellis.core.rendering.session import RenderSession
        from trellis.utils.hot_reload import SessionRegistry

        registry = SessionRegistry()
        assert len(registry) == 0

        session = RenderSession(root_component=noop_component)
        registry.register(session)
        assert len(registry) == 1


class TestHotReload:
    """Tests for the HotReload class."""

    def test_creates_session_registry(self) -> None:
        """HotReload has a session registry."""
        from trellis.utils.hot_reload import HotReload, SessionRegistry

        hr = HotReload()
        assert isinstance(hr.sessions, SessionRegistry)

    def test_invalidate_all_sessions_marks_all_elements_dirty(self, noop_component) -> None:
        """Invalidating sessions marks ALL elements dirty, not just root."""
        from trellis import component
        from trellis.core.rendering.render import render
        from trellis.core.rendering.session import RenderSession
        from trellis.utils.hot_reload import HotReload
        from trellis.widgets import Column, Label

        @component
        def TestApp():
            with Column():
                Label(text="Hello")
                Label(text="World")

        session = RenderSession(root_component=TestApp)
        render(session)

        # Session should have multiple elements
        element_count = len(session.elements)
        assert element_count > 1, "Expected multiple elements in tree"

        # Initially no dirty elements
        assert not session.dirty.has_dirty()

        # Create HotReload and register session
        hr = HotReload()
        hr.sessions.register(session)

        # Trigger invalidation
        hr._invalidate_all_sessions()

        # ALL elements should now be dirty
        dirty_count = len(list(session.dirty.pop_all()))
        assert (
            dirty_count == element_count
        ), f"Expected {element_count} dirty elements, got {dirty_count}"

    def test_invalidate_with_no_sessions(self) -> None:
        """Invalidating with no sessions doesn't error."""
        from trellis.utils.hot_reload import HotReload

        hr = HotReload()
        # Should not raise
        hr._invalidate_all_sessions()

    def test_invalidate_with_empty_session(self, noop_component) -> None:
        """Invalidating a session with no elements is safe."""
        from trellis.core.rendering.session import RenderSession
        from trellis.utils.hot_reload import HotReload

        session = RenderSession(root_component=noop_component)
        # Don't render - session has no elements

        hr = HotReload()
        hr.sessions.register(session)

        # Should not raise
        hr._invalidate_all_sessions()
