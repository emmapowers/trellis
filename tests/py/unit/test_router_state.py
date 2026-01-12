"""Tests for RouterState class."""

import asyncio

import pytest

from trellis.routing.state import RouterState, router


class TestRouterStateInit:
    """Test RouterState initialization."""

    def test_default_path_is_root(self) -> None:
        state = RouterState()
        assert state.path == "/"

    def test_init_with_custom_path(self) -> None:
        state = RouterState(path="/users")
        assert state.path == "/users"

    def test_default_query_empty(self) -> None:
        """Query is empty when path has no query string."""
        state = RouterState()
        assert state.query == {}

    def test_query_parsed_from_path(self) -> None:
        """Query params are parsed from path."""
        state = RouterState(path="/users?page=1&sort=name")
        assert state.query == {"page": "1", "sort": "name"}

    def test_history_starts_with_initial_path(self) -> None:
        state = RouterState(path="/users")
        assert state.history == ["/users"]

    def test_history_index_starts_at_zero(self) -> None:
        state = RouterState()
        # INTERNAL TEST: Verify history index for navigation logic
        assert state._history_index == 0


class TestRouterStateNavigate:
    """Test RouterState.navigate() method."""

    def test_navigate_updates_path(self) -> None:
        state = RouterState()
        asyncio.run(state.navigate("/users"))
        assert state.path == "/users"

    def test_navigate_adds_to_history(self) -> None:
        state = RouterState()
        asyncio.run(state.navigate("/users"))
        assert state.history == ["/", "/users"]

    def test_navigate_increments_history_index(self) -> None:
        state = RouterState()
        asyncio.run(state.navigate("/users"))
        # INTERNAL TEST: Verify history index for navigation logic
        assert state._history_index == 1

    def test_navigate_multiple_times(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.navigate("/users/123")
            await state.navigate("/settings")
            assert state.path == "/settings"
            assert state.history == ["/", "/users", "/users/123", "/settings"]

        asyncio.run(run())

    def test_navigate_clears_forward_history(self) -> None:
        """When navigating after going back, forward history is discarded."""

        async def run() -> None:
            state = RouterState()
            await state.navigate("/a")
            await state.navigate("/b")
            await state.navigate("/c")
            await state.go_back()
            await state.go_back()
            # Now at /a, with /b and /c as forward history
            await state.navigate("/d")
            # Forward history (/b, /c) should be gone
            assert state.history == ["/", "/a", "/d"]
            assert state.path == "/d"

        asyncio.run(run())


class TestRouterStateGoBack:
    """Test RouterState.go_back() method."""

    def test_go_back_updates_path(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.go_back()
            assert state.path == "/"

        asyncio.run(run())

    def test_go_back_decrements_history_index(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.go_back()
            # INTERNAL TEST: Verify history index for navigation logic
            assert state._history_index == 0

        asyncio.run(run())

    def test_go_back_does_nothing_at_start(self) -> None:
        state = RouterState()
        asyncio.run(state.go_back())  # Should not raise
        assert state.path == "/"
        assert state._history_index == 0


class TestRouterStateGoForward:
    """Test RouterState.go_forward() method."""

    def test_go_forward_updates_path(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.go_back()
            await state.go_forward()
            assert state.path == "/users"

        asyncio.run(run())

    def test_go_forward_increments_history_index(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.go_back()
            await state.go_forward()
            # INTERNAL TEST: Verify history index for navigation logic
            assert state._history_index == 1

        asyncio.run(run())

    def test_go_forward_does_nothing_at_end(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.go_forward()  # Should not raise
            assert state.path == "/users"
            assert state._history_index == 1

        asyncio.run(run())


class TestRouterStateCanNavigate:
    """Test can_go_back and can_go_forward properties."""

    def test_cannot_go_back_initially(self) -> None:
        state = RouterState()
        assert state.can_go_back is False

    def test_can_go_back_after_navigate(self) -> None:
        state = RouterState()
        asyncio.run(state.navigate("/users"))
        assert state.can_go_back is True

    def test_cannot_go_forward_initially(self) -> None:
        state = RouterState()
        assert state.can_go_forward is False

    def test_cannot_go_forward_at_end(self) -> None:
        state = RouterState()
        asyncio.run(state.navigate("/users"))
        assert state.can_go_forward is False

    def test_can_go_forward_after_back(self) -> None:
        async def run() -> None:
            state = RouterState()
            await state.navigate("/users")
            await state.go_back()
            assert state.can_go_forward is True

        asyncio.run(run())


class TestRouterFunction:
    """Test router() helper function."""

    def test_router_outside_context_raises(self) -> None:
        """router() should raise when called outside render context."""
        with pytest.raises(RuntimeError, match=r"(?i)context"):
            router()
