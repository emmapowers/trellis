"""Integration tests for Route component."""

import pytest

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.routing import Route, RouterState, Routes, router
from trellis.routing.state import CurrentRouteContext


class TestCurrentRouteContext:
    """Tests for CurrentRouteContext state."""

    def test_provides_pattern_to_descendants(self, capture_patches: type[PatchCapture]) -> None:
        """CurrentRouteContext provides pattern to descendant components."""
        captured_pattern: list[str] = []

        @component
        def Child() -> None:
            ctx = CurrentRouteContext.from_context()
            captured_pattern.append(ctx.pattern)

        @component
        def App() -> None:
            with CurrentRouteContext(pattern="/users/:id"):
                Child()

        capture = capture_patches(App)
        capture.render()

        assert captured_pattern == ["/users/:id"]


class TestOnDemandParams:
    """Tests for on-demand params computation from CurrentRouteContext."""

    def test_params_computed_from_context_pattern(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """router().params computes params from CurrentRouteContext pattern."""
        captured_params: dict[str, str] = {}

        @component
        def Child() -> None:
            captured_params.update(router().params)

        @component
        def App() -> None:
            with RouterState(path="/users/42"):
                with CurrentRouteContext(pattern="/users/:id"):
                    Child()

        capture = capture_patches(App)
        capture.render()

        assert captured_params == {"id": "42"}

    def test_params_raises_outside_route_context(self, capture_patches: type[PatchCapture]) -> None:
        """router().params raises RuntimeError when outside Route context."""

        @component
        def Child() -> None:
            _ = router().params  # Should raise - no Route context

        @component
        def App() -> None:
            with RouterState(path="/users/42"):
                Child()  # No Route wrapper

        capture = capture_patches(App)
        with pytest.raises(RuntimeError, match=r"outside of a Route context"):
            capture.render()


class TestOnDemandQuery:
    """Tests for on-demand query params computation from path."""

    def test_query_parsed_from_path(self, capture_patches: type[PatchCapture]) -> None:
        """router().query parses query string from path."""
        captured_query: dict[str, str] = {}

        @component
        def Child() -> None:
            captured_query.update(router().query)

        @component
        def App() -> None:
            with RouterState(path="/users?page=1&sort=name"):
                Child()

        capture = capture_patches(App)
        capture.render()

        assert captured_query == {"page": "1", "sort": "name"}

    def test_query_empty_when_no_query_string(self, capture_patches: type[PatchCapture]) -> None:
        """router().query returns empty dict when path has no query string."""
        captured_query: dict[str, str] = {}

        @component
        def Child() -> None:
            captured_query.update(router().query)

        @component
        def App() -> None:
            with RouterState(path="/users"):
                Child()

        capture = capture_patches(App)
        capture.render()

        assert captured_query == {}

    def test_query_handles_url_encoding(self, capture_patches: type[PatchCapture]) -> None:
        """router().query properly decodes URL-encoded values."""
        captured_query: dict[str, str] = {}

        @component
        def Child() -> None:
            captured_query.update(router().query)

        @component
        def App() -> None:
            with RouterState(path="/search?q=hello%20world"):
                Child()

        capture = capture_patches(App)
        capture.render()

        assert captured_query == {"q": "hello world"}


class TestRouteMatching:
    """Tests for Route component path matching."""

    def test_renders_when_path_matches(self, capture_patches: type[PatchCapture]) -> None:
        """Route renders children when path matches pattern."""
        rendered = []

        @component
        def MatchedContent() -> None:
            rendered.append("matched")

        @component
        def App() -> None:
            with RouterState(path="/users"):
                with Routes():
                    with Route(pattern="/users"):
                        MatchedContent()

        capture = capture_patches(App)
        capture.render()

        assert "matched" in rendered

    def test_does_not_render_when_path_does_not_match(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Route does not render children when path doesn't match."""
        rendered = []

        @component
        def NotMatched() -> None:
            rendered.append("should not render")

        @component
        def App() -> None:
            with RouterState(path="/other"):
                with Routes():
                    with Route(pattern="/users"):
                        NotMatched()

        capture = capture_patches(App)
        capture.render()

        assert rendered == []

    def test_wildcard_always_matches(self, capture_patches: type[PatchCapture]) -> None:
        """Route with wildcard pattern matches any path."""
        rendered = []

        @component
        def Fallback() -> None:
            rendered.append("fallback")

        @component
        def App() -> None:
            with RouterState(path="/any/random/path"):
                with Routes():
                    with Route(pattern="*"):
                        Fallback()

        capture = capture_patches(App)
        capture.render()

        assert "fallback" in rendered


class TestRouteParams:
    """Tests for Route component parameter extraction."""

    def test_extracts_params_from_path(self, capture_patches: type[PatchCapture]) -> None:
        """Route extracts params and makes them available via router()."""
        captured_params: dict[str, str] = {}

        @component
        def UserPage() -> None:
            captured_params.update(router().params)

        @component
        def App() -> None:
            with RouterState(path="/users/123"):
                with Routes():
                    with Route(pattern="/users/:id"):
                        UserPage()

        capture = capture_patches(App)
        capture.render()

        assert captured_params == {"id": "123"}

    def test_extracts_multiple_params(self, capture_patches: type[PatchCapture]) -> None:
        """Route extracts multiple params from path."""
        captured_params: dict[str, str] = {}

        @component
        def PostPage() -> None:
            captured_params.update(router().params)

        @component
        def App() -> None:
            with RouterState(path="/users/42/posts/99"):
                with Routes():
                    with Route(pattern="/users/:userId/posts/:postId"):
                        PostPage()

        capture = capture_patches(App)
        capture.render()

        assert captured_params == {"userId": "42", "postId": "99"}


class TestRouteReactivity:
    """Tests for Route component reactivity to path changes."""

    def test_rerenders_on_path_change(self, capture_patches: type[PatchCapture]) -> None:
        """Route re-renders when RouterState path changes."""
        render_count = [0]
        router_state = RouterState(path="/")

        @component
        def HomePage() -> None:
            render_count[0] += 1

        @component
        def App() -> None:
            with router_state:
                with Routes():
                    with Route(pattern="/"):
                        HomePage()

        capture = capture_patches(App)
        capture.render()
        assert render_count[0] == 1

        # Navigate to different path - HomePage should not render
        router_state.navigate("/other")
        capture.render()

        # Navigate back - HomePage should render again
        router_state.navigate("/")
        capture.render()
        assert render_count[0] == 2

    def test_shows_different_route_on_navigate(self, capture_patches: type[PatchCapture]) -> None:
        """Navigating shows different Route content."""
        rendered: list[str] = []
        router_state = RouterState(path="/")

        @component
        def HomePage() -> None:
            rendered.append("home")

        @component
        def UsersPage() -> None:
            rendered.append("users")

        @component
        def App() -> None:
            with router_state:
                with Routes():
                    with Route(pattern="/"):
                        HomePage()
                    with Route(pattern="/users"):
                        UsersPage()

        capture = capture_patches(App)
        capture.render()
        assert rendered == ["home"]

        rendered.clear()
        router_state.navigate("/users")
        capture.render()
        assert rendered == ["users"]


class TestMultipleRoutes:
    """Tests for multiple Route components."""

    def test_only_matching_route_renders(self, capture_patches: type[PatchCapture]) -> None:
        """Only the Route that matches renders its children."""
        rendered: list[str] = []

        @component
        def Home() -> None:
            rendered.append("home")

        @component
        def Users() -> None:
            rendered.append("users")

        @component
        def Settings() -> None:
            rendered.append("settings")

        @component
        def App() -> None:
            with RouterState(path="/users"):
                with Routes():
                    with Route(pattern="/"):
                        Home()
                    with Route(pattern="/users"):
                        Users()
                    with Route(pattern="/settings"):
                        Settings()

        capture = capture_patches(App)
        capture.render()

        assert rendered == ["users"]
