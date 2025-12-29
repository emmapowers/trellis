"""Unit tests for RenderSession class."""

import weakref
from typing import TYPE_CHECKING

from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.element import Element
from trellis.core.rendering.element_state import ElementStateStore
from trellis.core.rendering.elements import ElementStore
from trellis.core.rendering.session import RenderSession

if TYPE_CHECKING:
    from trellis.core.components.composition import CompositionComponent


class _MockElementComponent:
    """Minimal component for creating test Element nodes."""

    name = "MockElement"
    _has_children_param = False

    def render(self) -> None:
        pass


def _make_node(node_id: str, tree_ref=None) -> Element:
    """Create a test node with the given ID."""

    class FakeTree:
        pass

    if tree_ref is None:
        tree_ref = weakref.ref(FakeTree())

    node = Element(
        component=_MockElementComponent(),
        _session_ref=tree_ref,
        render_count=0,
        id=node_id,
    )
    return node


# =============================================================================
# RenderSession Tests
# =============================================================================


class TestRenderSession:
    def test_creation(self, noop_component: "CompositionComponent") -> None:
        session = RenderSession(root_component=noop_component)

        assert session.root_component is noop_component
        assert session.root_node_id is None
        assert isinstance(session.elements, ElementStore)
        assert isinstance(session.states, ElementStateStore)
        assert isinstance(session.dirty, DirtyTracker)
        assert session.active is None

    def test_is_rendering(self, noop_component: "CompositionComponent") -> None:
        session = RenderSession(root_component=noop_component)

        assert not session.is_rendering()

        session.active = ActiveRender()
        assert session.is_rendering()

        session.active = None
        assert not session.is_rendering()

    def test_is_executing(self, noop_component: "CompositionComponent") -> None:
        session = RenderSession(root_component=noop_component)

        assert not session.is_executing()

        session.active = ActiveRender()
        assert not session.is_executing()

        session.active.current_node_id = "e1"
        assert session.is_executing()

    def test_current_node_id(self, noop_component: "CompositionComponent") -> None:
        session = RenderSession(root_component=noop_component)

        assert session.current_node_id is None

        session.active = ActiveRender()
        session.active.current_node_id = "e1"
        assert session.current_node_id == "e1"

    def test_get_callback_from_node_props(self, noop_component: "CompositionComponent") -> None:
        """get_callback looks up callbacks from node props."""
        session = RenderSession(root_component=noop_component)

        def my_callback():
            return "called"

        # Create a node and store it
        node = _make_node("e1")
        node.props["on_click"] = my_callback
        session.elements.store(node)

        # get_callback should find it
        result = session.get_callback("e1", "on_click")
        assert result is not None
        assert result() == "called"

        # Non-existent prop returns None
        assert session.get_callback("e1", "on_missing") is None

        # Non-existent node returns None
        assert session.get_callback("nonexistent", "on_click") is None

    def test_stores_integration(self, noop_component: "CompositionComponent") -> None:
        """Test that stores work correctly within RenderSession."""
        session = RenderSession(root_component=noop_component)

        # Nodes
        node = _make_node("e1")
        session.elements.store(node)
        assert session.elements.get("e1") is node

        # State
        state = session.states.get_or_create("e1")
        assert state is not None

        # Dirty
        session.dirty.mark("e1")
        assert session.dirty.has_dirty()

    def test_lock_is_reentrant(self, noop_component: "CompositionComponent") -> None:
        """Test that the lock is reentrant (RLock)."""
        session = RenderSession(root_component=noop_component)

        with session.lock:
            with session.lock:
                # Should not deadlock
                pass
