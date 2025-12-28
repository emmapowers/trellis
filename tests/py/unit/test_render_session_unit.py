"""Unit tests for RenderSession class."""

import weakref

from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.element import Element
from trellis.core.rendering.element_state import ElementStateStore
from trellis.core.rendering.elements import ElementStore
from trellis.core.rendering.session import RenderSession


class MockComponent:
    """Minimal component for testing."""

    name = "MockComponent"
    _has_children_param = False

    def render(self):
        """
        Perform a single render pass for this active render instance.
        
        This executes one cycle of the render process, processing the current node (and any nodes it enqueues) and updating the render/session state as needed.
        """
        pass


def make_node(node_id: str, tree_ref=None) -> Element:
    """
    Create a test Element with the specified node id and an associated tree reference.
    
    Parameters:
        node_id (str): Identifier to assign to the created Element.
        tree_ref (optional): A weakref.ref to a tree object to use as the Element's session/tree reference.
            If omitted, a weak reference to a temporary FakeTree instance will be created.
    
    Returns:
        Element: A test Element whose component is a MockComponent, whose `_session_ref` is set to
        `tree_ref` (or the generated weak reference), and whose `render_count` is initialized to 0.
    """

    class FakeTree:
        pass

    if tree_ref is None:
        tree_ref = weakref.ref(FakeTree())

    node = Element(
        component=MockComponent(),
        _session_ref=tree_ref,
        render_count=0,
        id=node_id,
    )
    return node


# =============================================================================
# RenderSession Tests
# =============================================================================


class TestRenderSession:
    def test_creation(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        assert session.root_component is comp
        assert session.root_node_id is None
        assert isinstance(session.elements, ElementStore)
        assert isinstance(session.states, ElementStateStore)
        assert isinstance(session.dirty, DirtyTracker)
        assert session.active is None

    def test_is_rendering(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        assert not session.is_rendering()

        session.active = ActiveRender()
        assert session.is_rendering()

        session.active = None
        assert not session.is_rendering()

    def test_is_executing(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        assert not session.is_executing()

        session.active = ActiveRender()
        assert not session.is_executing()

        session.active.current_node_id = "e1"
        assert session.is_executing()

    def test_current_node_id(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        assert session.current_node_id is None

        session.active = ActiveRender()
        session.active.current_node_id = "e1"
        assert session.current_node_id == "e1"

    def test_get_callback_from_node_props(self):
        """get_callback looks up callbacks from node props."""
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        def my_callback():
            """
            Produce the string "called".
            
            Returns:
                str: The string "called".
            """
            return "called"

        # Create a node and store it
        node = make_node("e1")
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

    def test_stores_integration(self):
        """Test that stores work correctly within RenderSession."""
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        # Nodes
        node = make_node("e1")
        session.elements.store(node)
        assert session.elements.get("e1") is node

        # State
        state = session.states.get_or_create("e1")
        assert state is not None

        # Dirty
        session.dirty.mark("e1")
        assert session.dirty.has_dirty()

    def test_lock_is_reentrant(self):
        """Test that the lock is reentrant (RLock)."""
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        with session.lock:
            with session.lock:
                # Should not deadlock
                pass