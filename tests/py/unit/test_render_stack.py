"""Tests for Frame, FrameStack, PatchCollector, and ActiveRender classes."""

import pytest

from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.elements import ElementStore
from trellis.core.rendering.frames import Frame, FrameStack
from trellis.core.rendering.lifecycle import LifecycleTracker
from trellis.core.rendering.patches import PatchCollector
from trellis.platforms.common.messages import AddPatch, RemovePatch, UpdatePatch


class MockComponent:
    """Minimal component for testing."""

    name = "MockComponent"
    _has_children_param = False

    def render(self):
        pass


# =============================================================================
# Frame Tests
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


# =============================================================================
# FrameStack Tests
# =============================================================================


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
# ActiveRender Tests
# =============================================================================


class TestActiveRender:
    def test_default_values(self):
        active = ActiveRender()

        assert isinstance(active.frames, FrameStack)
        assert isinstance(active.patches, PatchCollector)
        assert isinstance(active.lifecycle, LifecycleTracker)
        assert isinstance(active.old_elements, ElementStore)
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
