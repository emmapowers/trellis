"""Tests for fine-grained decomposition classes.

Tests for NodeStore, StateStore, DirtyTracker, FrameStack,
PatchCollector, LifecycleTracker, ActiveRender, and RenderSession.
"""

import pytest

from trellis.core.active_render import ActiveRender
from trellis.core.dirty_tracker import DirtyTracker
from trellis.core.frame_stack import Frame, FrameStack
from trellis.core.lifecycle_tracker import LifecycleTracker
from trellis.core.messages import AddPatch, RemovePatch, UpdatePatch
from trellis.core.node_store import NodeStore
from trellis.core.patch_collector import PatchCollector
from trellis.core.element_node import ElementNode
from trellis.core.element_state import ElementState, StateStore
from trellis.core.session import RenderSession


# =============================================================================
# Mock component for testing
# =============================================================================


class MockComponent:
    """Minimal component for testing."""

    name = "MockComponent"
    _has_children_param = False

    def render(self):
        pass


def make_node(node_id: str, tree_ref=None) -> ElementNode:
    """Create a test node with the given ID."""
    import weakref

    class FakeTree:
        pass

    if tree_ref is None:
        tree_ref = weakref.ref(FakeTree())

    node = ElementNode(
        component=MockComponent(),
        _session_ref=tree_ref,
        id=node_id,
    )
    return node


# =============================================================================
# NodeStore Tests
# =============================================================================


class TestNodeStore:
    def test_store_and_get(self):
        store = NodeStore()
        node = make_node("e1")

        store.store(node)
        assert store.get("e1") is node

    def test_get_nonexistent_returns_none(self):
        store = NodeStore()
        assert store.get("nonexistent") is None

    def test_remove(self):
        store = NodeStore()
        node = make_node("e1")
        store.store(node)

        store.remove("e1")
        assert store.get("e1") is None

    def test_remove_nonexistent_no_error(self):
        store = NodeStore()
        store.remove("nonexistent")  # Should not raise

    def test_contains(self):
        store = NodeStore()
        node = make_node("e1")
        store.store(node)

        assert "e1" in store
        assert "e2" not in store

    def test_len(self):
        store = NodeStore()
        assert len(store) == 0

        store.store(make_node("e1"))
        assert len(store) == 1

        store.store(make_node("e2"))
        assert len(store) == 2

    def test_clear(self):
        store = NodeStore()
        store.store(make_node("e1"))
        store.store(make_node("e2"))

        store.clear()
        assert len(store) == 0

    def test_clone(self):
        store = NodeStore()
        node1 = make_node("e1")
        node2 = make_node("e2")
        store.store(node1)
        store.store(node2)

        cloned = store.clone()

        # Clone has same nodes
        assert cloned.get("e1") is node1
        assert cloned.get("e2") is node2

        # Modifying original doesn't affect clone
        store.remove("e1")
        assert store.get("e1") is None
        assert cloned.get("e1") is node1

    def test_get_children(self):
        store = NodeStore()
        child1 = make_node("c1")
        child2 = make_node("c2")
        store.store(child1)
        store.store(child2)

        # Create parent with child_ids
        from dataclasses import replace

        parent = replace(make_node("p1"), child_ids=("c1", "c2"))
        store.store(parent)

        children = store.get_children(parent)
        assert len(children) == 2
        assert children[0] is child1
        assert children[1] is child2

    def test_get_children_missing_child(self):
        """get_children skips missing children."""
        store = NodeStore()
        child1 = make_node("c1")
        store.store(child1)

        from dataclasses import replace

        parent = replace(make_node("p1"), child_ids=("c1", "c2"))
        store.store(parent)

        children = store.get_children(parent)
        assert len(children) == 1
        assert children[0] is child1

    def test_iter(self):
        store = NodeStore()
        store.store(make_node("e1"))
        store.store(make_node("e2"))

        ids = list(store)
        assert set(ids) == {"e1", "e2"}

    def test_items(self):
        store = NodeStore()
        node1 = make_node("e1")
        node2 = make_node("e2")
        store.store(node1)
        store.store(node2)

        items = dict(store.items())
        assert items["e1"] is node1
        assert items["e2"] is node2


# =============================================================================
# StateStore Tests
# =============================================================================


class TestStateStore:
    def test_get_nonexistent_returns_none(self):
        store = StateStore()
        assert store.get("e1") is None

    def test_set_and_get(self):
        store = StateStore()
        state = ElementState(dirty=True)

        store.set("e1", state)
        assert store.get("e1") is state

    def test_get_or_create_new(self):
        store = StateStore()

        state = store.get_or_create("e1")
        assert state is not None
        assert isinstance(state, ElementState)
        assert store.get("e1") is state

    def test_get_or_create_existing(self):
        store = StateStore()
        existing = ElementState(dirty=True)
        store.set("e1", existing)

        state = store.get_or_create("e1")
        assert state is existing

    def test_remove(self):
        store = StateStore()
        store.set("e1", ElementState())

        store.remove("e1")
        assert store.get("e1") is None

    def test_remove_nonexistent_no_error(self):
        store = StateStore()
        store.remove("nonexistent")  # Should not raise

    def test_contains(self):
        store = StateStore()
        store.set("e1", ElementState())

        assert "e1" in store
        assert "e2" not in store

    def test_len(self):
        store = StateStore()
        assert len(store) == 0

        store.set("e1", ElementState())
        assert len(store) == 1

    def test_iter(self):
        store = StateStore()
        store.set("e1", ElementState())
        store.set("e2", ElementState())

        ids = list(store)
        assert set(ids) == {"e1", "e2"}


# =============================================================================
# DirtyTracker Tests
# =============================================================================


class TestDirtyTracker:
    def test_mark_and_contains(self):
        tracker = DirtyTracker()

        tracker.mark("e1")
        assert "e1" in tracker
        assert "e2" not in tracker

    def test_clear(self):
        tracker = DirtyTracker()
        tracker.mark("e1")

        tracker.clear("e1")
        assert "e1" not in tracker

    def test_clear_nonexistent_no_error(self):
        tracker = DirtyTracker()
        tracker.clear("nonexistent")  # Should not raise

    def test_discard(self):
        tracker = DirtyTracker()
        tracker.mark("e1")

        tracker.discard("e1")
        assert "e1" not in tracker

    def test_has_dirty(self):
        tracker = DirtyTracker()
        assert not tracker.has_dirty()

        tracker.mark("e1")
        assert tracker.has_dirty()

        tracker.clear("e1")
        assert not tracker.has_dirty()

    def test_pop_all(self):
        tracker = DirtyTracker()
        tracker.mark("e1")
        tracker.mark("e2")
        tracker.mark("e3")

        ids = tracker.pop_all()
        assert set(ids) == {"e1", "e2", "e3"}
        assert not tracker.has_dirty()
        assert len(tracker) == 0

    def test_len(self):
        tracker = DirtyTracker()
        assert len(tracker) == 0

        tracker.mark("e1")
        assert len(tracker) == 1

        tracker.mark("e1")  # Duplicate
        assert len(tracker) == 1

        tracker.mark("e2")
        assert len(tracker) == 2


# =============================================================================
# FrameStack Tests
# =============================================================================


class TestFrame:
    def test_default_values(self):
        frame = Frame()
        assert frame.child_ids == []
        assert frame.parent_id == ""
        assert frame.position == 0

    def test_with_parent_id(self):
        frame = Frame(parent_id="parent")
        assert frame.parent_id == "parent"


class TestFrameStack:
    def test_push_and_pop(self):
        stack = FrameStack()

        frame = stack.push("parent")
        assert frame.parent_id == "parent"
        assert len(stack) == 1

        child_ids = stack.pop()
        assert child_ids == []
        assert len(stack) == 0

    def test_current(self):
        stack = FrameStack()
        assert stack.current() is None

        frame = stack.push("parent")
        assert stack.current() is frame

        stack.pop()
        assert stack.current() is None

    def test_add_child(self):
        stack = FrameStack()
        stack.push("parent")

        stack.add_child("c1")
        stack.add_child("c2")

        child_ids = stack.pop()
        assert child_ids == ["c1", "c2"]

    def test_add_child_no_frame(self):
        """add_child does nothing when no frame is active."""
        stack = FrameStack()
        stack.add_child("c1")  # Should not raise

    def test_has_active(self):
        stack = FrameStack()
        assert not stack.has_active()

        stack.push("parent")
        assert stack.has_active()

        stack.pop()
        assert not stack.has_active()

    def test_nested_frames(self):
        stack = FrameStack()

        stack.push("parent")
        stack.add_child("c1")

        stack.push("child")
        stack.add_child("gc1")
        stack.add_child("gc2")

        grandchild_ids = stack.pop()
        assert grandchild_ids == ["gc1", "gc2"]

        stack.add_child("c2")
        child_ids = stack.pop()
        assert child_ids == ["c1", "c2"]

    def test_next_child_id_positional(self):
        stack = FrameStack()
        stack.push("/@123")

        comp = MockComponent()
        comp_id = id(comp)

        id1 = stack.next_child_id(comp, None)
        assert id1 == f"/@123/0@{comp_id}"

        id2 = stack.next_child_id(comp, None)
        assert id2 == f"/@123/1@{comp_id}"

    def test_next_child_id_keyed(self):
        stack = FrameStack()
        stack.push("/@123")

        comp = MockComponent()
        comp_id = id(comp)

        child_id = stack.next_child_id(comp, "my-key")
        assert child_id == f"/@123/:my-key@{comp_id}"

    def test_next_child_id_escapes_special_chars(self):
        stack = FrameStack()
        stack.push("/@123")

        comp = MockComponent()
        comp_id = id(comp)

        # Key with special chars
        child_id = stack.next_child_id(comp, "a:b/c@d")
        assert child_id == f"/@123/:a%3Ab%2Fc%40d@{comp_id}"

    def test_next_child_id_no_frame_raises(self):
        stack = FrameStack()
        comp = MockComponent()

        with pytest.raises(RuntimeError, match="no active frame"):
            stack.next_child_id(comp, None)

    def test_root_id(self):
        stack = FrameStack()
        comp = MockComponent()
        comp_id = id(comp)

        root_id = stack.root_id(comp)
        assert root_id == f"/@{comp_id}"


# =============================================================================
# PatchCollector Tests
# =============================================================================


class TestPatchCollector:
    def test_emit_and_get_all(self):
        collector = PatchCollector()

        patch1 = AddPatch(parent_id="p1", children=["c1"], node={"key": "c1"})
        patch2 = UpdatePatch(id="e1", props={"text": "hello"})
        patch3 = RemovePatch(id="e2")

        collector.emit(patch1)
        collector.emit(patch2)
        collector.emit(patch3)

        patches = collector.get_all()
        assert len(patches) == 3
        assert patches[0] is patch1
        assert patches[1] is patch2
        assert patches[2] is patch3

    def test_pop_all(self):
        collector = PatchCollector()
        collector.emit(AddPatch(parent_id=None, children=[], node={}))
        collector.emit(RemovePatch(id="e1"))

        patches = collector.pop_all()
        assert len(patches) == 2
        assert len(collector) == 0

    def test_clear(self):
        collector = PatchCollector()
        collector.emit(RemovePatch(id="e1"))

        collector.clear()
        assert len(collector) == 0

    def test_len(self):
        collector = PatchCollector()
        assert len(collector) == 0

        collector.emit(RemovePatch(id="e1"))
        assert len(collector) == 1

    def test_iter(self):
        collector = PatchCollector()
        patch1 = RemovePatch(id="e1")
        patch2 = RemovePatch(id="e2")
        collector.emit(patch1)
        collector.emit(patch2)

        patches = list(collector)
        assert patches == [patch1, patch2]


# =============================================================================
# LifecycleTracker Tests
# =============================================================================


class TestLifecycleTracker:
    def test_track_mount(self):
        tracker = LifecycleTracker()

        tracker.track_mount("e1")
        tracker.track_mount("e2")

        mounts = tracker.pop_mounts()
        assert mounts == ["e1", "e2"]

    def test_track_unmount(self):
        tracker = LifecycleTracker()

        tracker.track_unmount("e1")
        tracker.track_unmount("e2")

        unmounts = tracker.pop_unmounts()
        assert unmounts == ["e1", "e2"]

    def test_pop_mounts_clears(self):
        tracker = LifecycleTracker()
        tracker.track_mount("e1")

        tracker.pop_mounts()
        assert tracker.pop_mounts() == []

    def test_pop_unmounts_clears(self):
        tracker = LifecycleTracker()
        tracker.track_unmount("e1")

        tracker.pop_unmounts()
        assert tracker.pop_unmounts() == []

    def test_has_pending(self):
        tracker = LifecycleTracker()
        assert not tracker.has_pending()

        tracker.track_mount("e1")
        assert tracker.has_pending()

        tracker.pop_mounts()
        assert not tracker.has_pending()

        tracker.track_unmount("e1")
        assert tracker.has_pending()

    def test_clear(self):
        tracker = LifecycleTracker()
        tracker.track_mount("e1")
        tracker.track_unmount("e2")

        tracker.clear()
        assert not tracker.has_pending()
        assert tracker.pop_mounts() == []
        assert tracker.pop_unmounts() == []


# =============================================================================
# ActiveRender Tests
# =============================================================================


class TestActiveRender:
    def test_default_values(self):
        active = ActiveRender()

        assert isinstance(active.frames, FrameStack)
        assert isinstance(active.patches, PatchCollector)
        assert isinstance(active.lifecycle, LifecycleTracker)
        assert isinstance(active.old_nodes, NodeStore)
        assert active.current_node_id is None
        assert active.last_property_access is None

    def test_current_node_id(self):
        active = ActiveRender()

        active.current_node_id = "e1"
        assert active.current_node_id == "e1"

    def test_last_property_access(self):
        active = ActiveRender()

        class FakeOwner:
            pass

        owner = FakeOwner()
        active.last_property_access = (owner, "value", 42)
        assert active.last_property_access == (owner, "value", 42)

    def test_frames_integration(self):
        """Test that frames work correctly within ActiveRender."""
        active = ActiveRender()

        active.frames.push("parent")
        active.frames.add_child("c1")
        active.frames.add_child("c2")

        child_ids = active.frames.pop()
        assert child_ids == ["c1", "c2"]

    def test_patches_integration(self):
        """Test that patches work correctly within ActiveRender."""
        active = ActiveRender()

        active.patches.emit(RemovePatch(id="e1"))
        assert len(active.patches) == 1

    def test_lifecycle_integration(self):
        """Test that lifecycle works correctly within ActiveRender."""
        active = ActiveRender()

        active.lifecycle.track_mount("e1")
        active.lifecycle.track_unmount("e2")

        assert active.lifecycle.pop_mounts() == ["e1"]
        assert active.lifecycle.pop_unmounts() == ["e2"]


# =============================================================================
# RenderSession Tests
# =============================================================================


class TestRenderSession:
    def test_creation(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        assert session.root_component is comp
        assert session.root_node_id is None
        assert isinstance(session.nodes, NodeStore)
        assert isinstance(session.state, StateStore)
        assert isinstance(session.dirty, DirtyTracker)
        assert session.callbacks == {}
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

    def test_register_callback(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        def my_callback():
            pass

        cb_id = session.register_callback(my_callback, "/@123/0@456", "on_click")
        assert cb_id == "/@123/0@456:on_click"
        assert session.callbacks[cb_id] is my_callback

    def test_get_callback(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        def my_callback():
            pass

        session.register_callback(my_callback, "e1", "on_click")

        assert session.get_callback("e1:on_click") is my_callback
        assert session.get_callback("nonexistent") is None

    def test_clear_callbacks_for_node(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        session.register_callback(lambda: None, "e1", "on_click")
        session.register_callback(lambda: None, "e1", "on_hover")
        session.register_callback(lambda: None, "e2", "on_click")

        session.clear_callbacks_for_node("e1")

        assert "e1:on_click" not in session.callbacks
        assert "e1:on_hover" not in session.callbacks
        assert "e2:on_click" in session.callbacks

    def test_clear_callbacks(self):
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        session.register_callback(lambda: None, "e1", "on_click")
        session.register_callback(lambda: None, "e2", "on_click")

        session.clear_callbacks()
        assert session.callbacks == {}

    def test_stores_integration(self):
        """Test that stores work correctly within RenderSession."""
        comp = MockComponent()
        session = RenderSession(root_component=comp)

        # Nodes
        node = make_node("e1")
        session.nodes.store(node)
        assert session.nodes.get("e1") is node

        # State
        state = session.state.get_or_create("e1")
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


# =============================================================================
# ElementState callbacks field Tests
# =============================================================================


class TestElementStateCallbacks:
    def test_callbacks_default_empty(self):
        state = ElementState()
        assert state.callbacks == {}

    def test_callbacks_can_store_callables(self):
        state = ElementState()

        def my_callback():
            pass

        state.callbacks["on_click"] = my_callback
        assert state.callbacks["on_click"] is my_callback

    def test_callbacks_multiple(self):
        state = ElementState()

        def cb1():
            pass

        def cb2():
            pass

        state.callbacks["on_click"] = cb1
        state.callbacks["on_hover"] = cb2

        assert len(state.callbacks) == 2
        assert state.callbacks["on_click"] is cb1
        assert state.callbacks["on_hover"] is cb2
