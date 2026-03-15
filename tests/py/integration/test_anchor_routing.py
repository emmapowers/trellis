"""Integration tests for A element auto-routing with relative URLs."""

import asyncio
import inspect
import typing as tp

from tests.conftest import PatchCapture, find_element_by_type
from trellis.core.callback_context import callback_context
from trellis.core.components.composition import component
from trellis.core.rendering.session import RenderSession
from trellis.html import MouseEvent
from trellis.html.links import A
from trellis.platforms.common.serialization import parse_callback_id, serialize_element
from trellis.routing import RouterState


def has_router_link_marker(anchor: dict[str, tp.Any]) -> bool:
    """Return whether serialized anchor props contain the router-link data marker."""
    data = anchor.get("props", {}).get("data")
    return isinstance(data, dict) and data.get("trellis-router-link") == "true"


def invoke_callback(session: RenderSession, cb_id: str, *args: tp.Any) -> None:
    """Invoke a callback with proper callback_context.

    Handles both sync and async callbacks.
    """
    element_id, prop_name = parse_callback_id(cb_id)
    callback = session.get_callback(element_id, prop_name)
    assert callback is not None, f"Callback {cb_id} not found"
    with callback_context(session, element_id):
        result = callback(*args)
        # Handle async callbacks
        if inspect.iscoroutine(result):
            asyncio.run(result)


class TestAnchorAutoRouting:
    """Tests for A element auto-routing with relative URLs."""

    def test_relative_path_gets_onclick_handler(self, capture_patches: type[PatchCapture]) -> None:
        """A with relative path automatically gets on_click for routing."""

        @component
        def App() -> None:
            with RouterState():
                A("About", href="/about")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        # Should have on_click handler for router navigation
        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is not None, "A with relative href should have on_click"
        assert "__callback__" in on_click_data
        assert has_router_link_marker(anchor)

    def test_relative_path_click_navigates(self, capture_patches: type[PatchCapture]) -> None:
        """Clicking A with relative path navigates via router."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:
                A("About", href="/about")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        cb_id = anchor.get("props", {}).get("on_click")["__callback__"]

        event = MouseEvent(type="click")
        invoke_callback(capture.session, cb_id, event)

        assert router_state.path == "/about"

    def test_absolute_url_no_onclick_handler(self, capture_patches: type[PatchCapture]) -> None:
        """A with absolute URL (http/https) does NOT get auto on_click."""

        @component
        def App() -> None:
            with RouterState():
                A("External", href="https://example.com")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        # Should NOT have on_click handler - let browser handle it
        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None, "A with absolute URL should not have auto on_click"
        assert not has_router_link_marker(anchor)

    def test_protocol_relative_url_no_onclick(self, capture_patches: type[PatchCapture]) -> None:
        """A with protocol-relative URL (//host) does NOT get auto on_click."""

        @component
        def App() -> None:
            with RouterState():
                A("External", href="//example.com/path")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None

    def test_user_onclick_not_overridden(self, capture_patches: type[PatchCapture]) -> None:
        """User-provided on_click is respected, not overridden."""
        custom_handler_called = []

        def custom_handler(_event: object) -> None:
            custom_handler_called.append(True)

        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:
                A("About", href="/about", on_click=custom_handler)

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        cb_id = anchor.get("props", {}).get("on_click")["__callback__"]

        event = MouseEvent(type="click")
        invoke_callback(capture.session, cb_id, event)

        # Custom handler should be called, not router navigation
        assert custom_handler_called == [True]
        # Path should NOT change (user handler doesn't navigate)
        assert router_state.path == "/"

    def test_no_href_no_onclick(self, capture_patches: type[PatchCapture]) -> None:
        """A without href does NOT get auto on_click."""

        @component
        def App() -> None:
            with RouterState():
                A("No link")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None

    def test_works_as_container_with_children(self, capture_patches: type[PatchCapture]) -> None:
        """A with relative href works as container and routes on click."""
        router_state = RouterState(path="/")
        child_rendered = []

        @component
        def Child() -> None:
            child_rendered.append(True)

        @component
        def App() -> None:
            with router_state:
                with A(href="/users"):
                    Child()

        capture = capture_patches(App)
        capture.render()

        # Child should be rendered
        assert child_rendered == [True]

        # Should have on_click for routing
        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        cb_id = anchor.get("props", {}).get("on_click")["__callback__"]

        event = MouseEvent(type="click")
        invoke_callback(capture.session, cb_id, event)

        assert router_state.path == "/users"

    def test_target_blank_no_onclick(self, capture_patches: type[PatchCapture]) -> None:
        """A with target='_blank' does NOT get auto on_click even for relative URLs.

        Opening in a new tab should always use browser navigation, not the router.
        """

        @component
        def App() -> None:
            with RouterState():
                A("Playground", href="/playground#code=abc", target="_blank")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        # Should NOT have on_click handler - browser opens new tab
        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None, "A with target='_blank' should not have auto on_click"
        assert not has_router_link_marker(anchor)

    def test_use_router_false_no_onclick(self, capture_patches: type[PatchCapture]) -> None:
        """A with use_router=False does NOT get auto on_click even for relative URLs."""

        @component
        def App() -> None:
            with RouterState():
                A("About", href="/about", use_router=False)

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        # Should NOT have on_click handler - browser handles navigation
        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None, "A with use_router=False should not have auto on_click"

    def test_download_no_onclick_handler(self, capture_patches: type[PatchCapture]) -> None:
        """A with download should keep native browser behavior."""

        @component
        def App() -> None:
            with RouterState():
                A("Export", href="/reports/latest.csv", download=True)

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None, "A with download should not have auto on_click"
        assert not has_router_link_marker(anchor)

    def test_download_false_still_gets_router_onclick(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """A with download=False should still be router-eligible."""

        @component
        def App() -> None:
            with RouterState():
                A("Dashboard", href="/dashboard", download=False)

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is not None
        assert "__callback__" in on_click_data
        assert has_router_link_marker(anchor)

    def test_download_filename_no_onclick_handler(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """A with download filename should keep native browser behavior."""

        @component
        def App() -> None:
            with RouterState():
                A("Export", href="/reports/latest.csv", download="latest.csv")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None
        assert not has_router_link_marker(anchor)

    def test_download_empty_string_no_onclick_handler(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """A with empty-string download should keep native browser behavior."""

        @component
        def App() -> None:
            with RouterState():
                A("Export", href="/reports/latest.csv", download="")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_element(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        on_click_data = anchor.get("props", {}).get("on_click")
        assert on_click_data is None
        assert not has_router_link_marker(anchor)
