"""Integration tests for Route component."""


from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.routing import Route, RouterState, router


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
                Route(pattern="/users", content=MatchedContent)

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
                Route(pattern="/users", content=NotMatched)

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
                Route(pattern="*", content=Fallback)

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
                Route(pattern="/users/:id", content=UserPage)

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
                Route(pattern="/users/:userId/posts/:postId", content=PostPage)

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
                Route(pattern="/", content=HomePage)

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
                Route(pattern="/", content=HomePage)
                Route(pattern="/users", content=UsersPage)

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
                Route(pattern="/", content=Home)
                Route(pattern="/users", content=Users)
                Route(pattern="/settings", content=Settings)

        capture = capture_patches(App)
        capture.render()

        assert rendered == ["users"]
