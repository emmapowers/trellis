"""Integration tests for Routes container component."""

import asyncio

import pytest

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.routing import Route, RouterState, Routes, router
from trellis.widgets.basic import Label


class TestRoutesExclusiveMatching:
    """Tests for Routes exclusive matching behavior."""

    def test_first_matching_route_renders(self, capture_patches: type[PatchCapture]) -> None:
        """Only the first matching Route renders its content."""
        rendered: list[str] = []

        @component
        def Home() -> None:
            rendered.append("home")

        @component
        def Fallback() -> None:
            rendered.append("fallback")

        @component
        def App() -> None:
            with RouterState(path="/"):
                with Routes():
                    with Route(pattern="/"):
                        Home()
                    with Route(pattern="*"):
                        Fallback()

        capture = capture_patches(App)
        capture.render()

        # Only Home should render, not Fallback (even though * matches everything)
        assert rendered == ["home"]

    def test_fallback_renders_when_no_match(self, capture_patches: type[PatchCapture]) -> None:
        """Fallback route renders when no other route matches."""
        rendered: list[str] = []

        @component
        def Home() -> None:
            rendered.append("home")

        @component
        def Fallback() -> None:
            rendered.append("fallback")

        @component
        def App() -> None:
            with RouterState(path="/unknown"):
                with Routes():
                    with Route(pattern="/"):
                        Home()
                    with Route(pattern="*"):
                        Fallback()

        capture = capture_patches(App)
        capture.render()

        assert rendered == ["fallback"]

    def test_multiple_routes_only_first_match(self, capture_patches: type[PatchCapture]) -> None:
        """With multiple potential matches, only first renders."""
        rendered: list[str] = []

        @component
        def Users() -> None:
            rendered.append("users")

        @component
        def UserDetail() -> None:
            rendered.append("user-detail")

        @component
        def Fallback() -> None:
            rendered.append("fallback")

        @component
        def App() -> None:
            with RouterState(path="/users"):
                with Routes():
                    with Route(pattern="/users"):
                        Users()
                    with Route(pattern="/users/:id"):
                        UserDetail()
                    with Route(pattern="*"):
                        Fallback()

        capture = capture_patches(App)
        capture.render()

        # /users matches first route, so others don't render
        assert rendered == ["users"]


class TestRoutesParams:
    """Tests for param handling within Routes."""

    def test_params_set_from_matching_route(self, capture_patches: type[PatchCapture]) -> None:
        """Matching route sets params on router state."""
        captured_params: dict[str, str] = {}

        @component
        def UserPage() -> None:
            captured_params.update(router().params)

        @component
        def Fallback() -> None:
            pass

        @component
        def App() -> None:
            with RouterState(path="/users/123"):
                with Routes():
                    with Route(pattern="/users/:id"):
                        UserPage()
                    with Route(pattern="*"):
                        Fallback()

        capture = capture_patches(App)
        capture.render()

        assert captured_params == {"id": "123"}

    def test_no_params_from_skipped_route(self, capture_patches: type[PatchCapture]) -> None:
        """Skipped routes don't set params."""
        captured_params: dict[str, str] = {}

        @component
        def Home() -> None:
            captured_params.update(router().params)

        @component
        def PageRoute() -> None:
            pass

        @component
        def App() -> None:
            with RouterState(path="/"):
                with Routes():
                    with Route(pattern="/"):
                        Home()
                    with Route(pattern="/:page"):
                        PageRoute()

        capture = capture_patches(App)
        capture.render()

        # Home matched first, so no params from fallback /:page
        assert captured_params == {}


class TestRoutesReactivity:
    """Tests for Routes reactivity to path changes."""

    def test_routes_update_on_navigate(self, capture_patches: type[PatchCapture]) -> None:
        """Routes re-evaluate on path change."""
        rendered: list[str] = []
        router_state = RouterState(path="/")

        @component
        def Home() -> None:
            rendered.append("home")

        @component
        def About() -> None:
            rendered.append("about")

        @component
        def App() -> None:
            with router_state:
                with Routes():
                    with Route(pattern="/"):
                        Home()
                    with Route(pattern="/about"):
                        About()

        capture = capture_patches(App)
        capture.render()
        assert rendered == ["home"]

        rendered.clear()
        asyncio.run(router_state.navigate("/about"))
        capture.render()
        assert rendered == ["about"]


class TestRouteWithoutRoutes:
    """Tests for Route behavior outside Routes container."""

    def test_route_outside_routes_raises(self, capture_patches: type[PatchCapture]) -> None:
        """Route outside Routes container raises RuntimeError."""

        @component
        def Home() -> None:
            pass

        @component
        def App() -> None:
            with RouterState(path="/"):
                # No Routes container - should raise
                with Route(pattern="/"):
                    Home()

        capture = capture_patches(App)

        with pytest.raises(RuntimeError, match="Routes container"):
            capture.render()


class TestRoutesParamConflict:
    """Integration tests for param conflict detection with Routes."""

    def test_routes_container_prevents_param_conflict(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Routes container prevents conflict by only running first match."""
        rendered: list[str] = []

        @component
        def Content1() -> None:
            rendered.append("content1")

        @component
        def Content2() -> None:
            rendered.append("content2")

        @component
        def App() -> None:
            with RouterState(path="/users/123"):
                with Routes():
                    with Route(pattern="/users/:id"):
                        Content1()
                    with Route(pattern="/users/:userId"):
                        Content2()

        capture = capture_patches(App)
        capture.render()  # Should not raise - second route is skipped

        assert rendered == ["content1"]


class TestEmptyRoutes:
    """Tests for empty Routes container."""

    def test_empty_routes_renders_nothing(self, capture_patches: type[PatchCapture]) -> None:
        """Empty Routes container renders without error."""
        rendered: list[str] = []

        @component
        def App() -> None:
            rendered.append("app")
            with RouterState(path="/"):
                with Routes():
                    pass  # No routes

        capture = capture_patches(App)
        capture.render()  # Should not raise

        assert rendered == ["app"]


class TestRoutesValidation:
    """Tests for Routes child validation."""

    def test_non_route_child_raises_type_error(self, capture_patches: type[PatchCapture]) -> None:
        """Routes raises TypeError when child is not a Route component."""

        @component
        def App() -> None:
            with RouterState(path="/"):
                with Routes():
                    Label(text="Not a route")  # Should raise

        capture = capture_patches(App)

        with pytest.raises(TypeError, match="Routes children must be Route components"):
            capture.render()

    def test_non_route_child_error_includes_component_name(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Error message includes the name of the invalid component."""

        @component
        def App() -> None:
            with RouterState(path="/"):
                with Routes():
                    Label(text="Invalid")

        capture = capture_patches(App)

        with pytest.raises(TypeError, match="Label"):
            capture.render()
