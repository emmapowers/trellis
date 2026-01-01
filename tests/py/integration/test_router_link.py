"""Integration tests for Link component."""

from tests.conftest import PatchCapture, find_element_by_type
from trellis.core.components.composition import component
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import parse_callback_id, serialize_node
from trellis.routing import Link, RouterState


def get_callback_from_id(session: RenderSession, cb_id: str):
    """Helper to get callback using the two-arg API."""
    node_id, prop_name = parse_callback_id(cb_id)
    return session.get_callback(node_id, prop_name)


class TestLinkRendering:
    """Tests for Link component rendering."""

    def test_renders_anchor_element(self, capture_patches: type[PatchCapture]) -> None:
        """Link renders as an anchor (a) element."""

        @component
        def App() -> None:
            with RouterState():
                Link(to="/about")

        capture = capture_patches(App)
        capture.render()

        # Find the anchor element in the tree
        tree = serialize_node(capture.session.root_element, capture.session)
        anchor_found = find_element_by_type(tree, "a")
        assert anchor_found, "Link should render an anchor element"

    def test_has_href_attribute(self, capture_patches: type[PatchCapture]) -> None:
        """Link has href attribute matching 'to' prop."""

        @component
        def App() -> None:
            with RouterState():
                Link(to="/users")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_node(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None
        assert anchor.get("props", {}).get("href") == "/users"

    def test_renders_text_content(self, capture_patches: type[PatchCapture]) -> None:
        """Link renders text content when provided."""

        @component
        def App() -> None:
            with RouterState():
                Link(to="/about", text="Go to About")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_node(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None
        # Text is stored in _text prop for hybrid elements
        assert anchor.get("props", {}).get("_text") == "Go to About"


class TestLinkNavigation:
    """Tests for Link component navigation behavior."""

    def test_click_navigates_to_path(self, capture_patches: type[PatchCapture]) -> None:
        """Clicking Link navigates to the specified path."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:
                Link(to="/about")

        capture = capture_patches(App)
        capture.render()

        # Find the anchor and get its onClick handler
        tree = serialize_node(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        assert anchor is not None

        # Get the onClick callback ID and invoke it
        on_click_data = anchor.get("props", {}).get("onClick")
        assert on_click_data is not None, "Link should have onClick handler"
        cb_id = on_click_data["__callback__"]

        # Invoke the callback
        callback = get_callback_from_id(capture.session, cb_id)
        assert callback is not None, f"Callback {cb_id} not found"
        callback()

        # Verify navigation occurred
        assert router_state.path == "/about"

    def test_click_updates_history(self, capture_patches: type[PatchCapture]) -> None:
        """Clicking Link adds path to history."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:
                Link(to="/users")

        capture = capture_patches(App)
        capture.render()

        tree = serialize_node(capture.session.root_element, capture.session)
        anchor = find_element_by_type(tree, "a")
        cb_id = anchor.get("props", {}).get("onClick")["__callback__"]
        callback = get_callback_from_id(capture.session, cb_id)
        callback()

        assert router_state.history == ["/", "/users"]


class TestLinkWithChildren:
    """Tests for Link with child components."""

    def test_renders_children(self, capture_patches: type[PatchCapture]) -> None:
        """Link renders child components inside anchor."""
        rendered_children: list[str] = []

        @component
        def ChildComp() -> None:
            rendered_children.append("child")

        @component
        def App() -> None:
            with RouterState():
                with Link(to="/path"):
                    ChildComp()

        capture = capture_patches(App)
        capture.render()

        assert "child" in rendered_children
