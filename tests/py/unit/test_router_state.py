"""Tests for RouterState class."""

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

    def test_default_params_empty(self) -> None:
        state = RouterState()
        assert state.params == {}

    def test_default_query_empty(self) -> None:
        state = RouterState()
        assert state.query == {}

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
        state.navigate("/users")
        assert state.path == "/users"

    def test_navigate_adds_to_history(self) -> None:
        state = RouterState()
        state.navigate("/users")
        assert state.history == ["/", "/users"]

    def test_navigate_increments_history_index(self) -> None:
        state = RouterState()
        state.navigate("/users")
        # INTERNAL TEST: Verify history index for navigation logic
        assert state._history_index == 1

    def test_navigate_multiple_times(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.navigate("/users/123")
        state.navigate("/settings")
        assert state.path == "/settings"
        assert state.history == ["/", "/users", "/users/123", "/settings"]

    def test_navigate_clears_forward_history(self) -> None:
        """When navigating after going back, forward history is discarded."""
        state = RouterState()
        state.navigate("/a")
        state.navigate("/b")
        state.navigate("/c")
        state.go_back()
        state.go_back()
        # Now at /a, with /b and /c as forward history
        state.navigate("/d")
        # Forward history (/b, /c) should be gone
        assert state.history == ["/", "/a", "/d"]
        assert state.path == "/d"


class TestRouterStateParams:
    """Test RouterState params handling."""

    def test_set_params(self) -> None:
        state = RouterState()
        state.set_params({"id": "123", "tab": "settings"})
        assert state.params == {"id": "123", "tab": "settings"}

    def test_params_are_read_only_copy(self) -> None:
        """Params property returns a copy to prevent mutation."""
        state = RouterState()
        state.set_params({"id": "123"})
        params = state.params
        params["id"] = "456"  # Mutate the copy
        assert state.params == {"id": "123"}  # Original unchanged


class TestRouterStateQuery:
    """Test RouterState query handling."""

    def test_set_query(self) -> None:
        state = RouterState()
        state.set_query({"page": "1", "sort": "name"})
        assert state.query == {"page": "1", "sort": "name"}

    def test_query_are_read_only_copy(self) -> None:
        """Query property returns a copy to prevent mutation."""
        state = RouterState()
        state.set_query({"page": "1"})
        query = state.query
        query["page"] = "2"  # Mutate the copy
        assert state.query == {"page": "1"}  # Original unchanged


class TestRouterStateGoBack:
    """Test RouterState.go_back() method."""

    def test_go_back_updates_path(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.go_back()
        assert state.path == "/"

    def test_go_back_decrements_history_index(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.go_back()
        # INTERNAL TEST: Verify history index for navigation logic
        assert state._history_index == 0

    def test_go_back_does_nothing_at_start(self) -> None:
        state = RouterState()
        state.go_back()  # Should not raise
        assert state.path == "/"
        assert state._history_index == 0


class TestRouterStateGoForward:
    """Test RouterState.go_forward() method."""

    def test_go_forward_updates_path(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.go_back()
        state.go_forward()
        assert state.path == "/users"

    def test_go_forward_increments_history_index(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.go_back()
        state.go_forward()
        # INTERNAL TEST: Verify history index for navigation logic
        assert state._history_index == 1

    def test_go_forward_does_nothing_at_end(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.go_forward()  # Should not raise
        assert state.path == "/users"
        assert state._history_index == 1


class TestRouterStateCanNavigate:
    """Test can_go_back and can_go_forward properties."""

    def test_cannot_go_back_initially(self) -> None:
        state = RouterState()
        assert state.can_go_back is False

    def test_can_go_back_after_navigate(self) -> None:
        state = RouterState()
        state.navigate("/users")
        assert state.can_go_back is True

    def test_cannot_go_forward_initially(self) -> None:
        state = RouterState()
        assert state.can_go_forward is False

    def test_cannot_go_forward_at_end(self) -> None:
        state = RouterState()
        state.navigate("/users")
        assert state.can_go_forward is False

    def test_can_go_forward_after_back(self) -> None:
        state = RouterState()
        state.navigate("/users")
        state.go_back()
        assert state.can_go_forward is True


class TestRouterFunction:
    """Test router() helper function."""

    def test_router_outside_context_raises(self) -> None:
        """router() should raise when called outside render context."""
        with pytest.raises(RuntimeError, match=r"(?i)context"):
            router()
