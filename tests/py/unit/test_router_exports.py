"""Tests for routing module exports.

Verifies that the routing API is properly exported from the main trellis package
as specified in the router implementation plan.
"""



class TestRoutingExportsFromMainPackage:
    """Test that routing components are exported from trellis package."""

    def test_router_state_exported(self) -> None:
        """RouterState should be importable from trellis."""
        from trellis import RouterState

        # Verify it's the actual class
        assert hasattr(RouterState, "navigate")
        assert hasattr(RouterState, "go_back")
        assert hasattr(RouterState, "go_forward")

    def test_router_function_exported(self) -> None:
        """router() function should be importable from trellis."""
        from trellis import router

        # Verify it's a callable
        assert callable(router)

    def test_route_component_exported(self) -> None:
        """Route component should be importable from trellis."""
        from trellis import Route

        # Verify it's a component (has component attributes)
        assert callable(Route)

    def test_link_component_exported(self) -> None:
        """Link component should be importable from trellis."""
        from trellis import Link

        # Verify it's a component (has component attributes)
        assert callable(Link)

    def test_all_routing_exports_together(self) -> None:
        """All routing exports should work in a single import statement."""
        from trellis import Link, Route, RouterState, router

        # All should be valid
        assert RouterState is not None
        assert router is not None
        assert Route is not None
        assert Link is not None

    def test_routing_exports_in_all(self) -> None:
        """Routing exports should be listed in __all__."""
        import trellis

        assert "RouterState" in trellis.__all__
        assert "router" in trellis.__all__
        assert "Route" in trellis.__all__
        assert "Link" in trellis.__all__


class TestRoutingSubmoduleExports:
    """Test that trellis.routing submodule exports correctly."""

    def test_routing_submodule_public_api(self) -> None:
        """Routing submodule should export only public API."""
        from trellis import routing

        # Public API should be in __all__
        assert "RouterState" in routing.__all__
        assert "router" in routing.__all__
        assert "Route" in routing.__all__
        assert "Link" in routing.__all__

    def test_match_path_not_in_public_api(self) -> None:
        """match_path is internal and should not be in public __all__."""
        from trellis import routing

        # match_path is internal implementation detail
        assert "match_path" not in routing.__all__

    def test_match_path_still_accessible(self) -> None:
        """match_path should still be accessible for internal use."""
        from trellis.routing.path_matching import match_path

        # Should still work for internal imports
        matched, params = match_path("/users/:id", "/users/123")
        assert matched is True
        assert params == {"id": "123"}
