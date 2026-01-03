"""Tests for ElementStore and ElementStateStore classes."""

import weakref
from dataclasses import replace

from trellis.core.rendering.element import Element
from trellis.core.rendering.element_state import ElementState, ElementStateStore
from trellis.core.rendering.element_store import ElementStore


class MockComponent:
    """Minimal component for testing."""

    name = "MockComponent"
    _has_children_param = False

    def render(self):
        pass


def make_node(node_id: str, tree_ref=None) -> Element:
    """Create a test node with the given ID."""

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
# ElementStore Tests
# =============================================================================


class TestElementStore:
    def test_store_and_get(self):
        store = ElementStore()
        node = make_node("e1")

        store.store(node)
        assert store.get("e1") is node

    def test_get_nonexistent_returns_none(self):
        store = ElementStore()
        assert store.get("nonexistent") is None

    def test_remove(self):
        store = ElementStore()
        node = make_node("e1")
        store.store(node)

        store.remove("e1")
        assert store.get("e1") is None

    def test_remove_nonexistent_no_error(self):
        store = ElementStore()
        store.remove("nonexistent")  # Should not raise

    def test_contains(self):
        store = ElementStore()
        node = make_node("e1")
        store.store(node)

        assert "e1" in store
        assert "e2" not in store

    def test_len(self):
        store = ElementStore()
        assert len(store) == 0

        store.store(make_node("e1"))
        assert len(store) == 1

        store.store(make_node("e2"))
        assert len(store) == 2

    def test_clear(self):
        store = ElementStore()
        store.store(make_node("e1"))
        store.store(make_node("e2"))

        store.clear()
        assert len(store) == 0

    def test_clone(self):
        store = ElementStore()
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
        store = ElementStore()
        child1 = make_node("c1")
        child2 = make_node("c2")
        store.store(child1)
        store.store(child2)

        # Create parent with child_ids
        parent = replace(make_node("p1"), child_ids=("c1", "c2"))
        store.store(parent)

        children = store.get_children(parent)
        assert len(children) == 2
        assert children[0] is child1
        assert children[1] is child2

    def test_get_children_missing_child(self):
        """get_children skips missing children."""
        store = ElementStore()
        child1 = make_node("c1")
        store.store(child1)

        parent = replace(make_node("p1"), child_ids=("c1", "c2"))
        store.store(parent)

        children = store.get_children(parent)
        assert len(children) == 1
        assert children[0] is child1

    def test_iter(self):
        store = ElementStore()
        store.store(make_node("e1"))
        store.store(make_node("e2"))

        ids = list(store)
        assert set(ids) == {"e1", "e2"}

    def test_items(self):
        store = ElementStore()
        node1 = make_node("e1")
        node2 = make_node("e2")
        store.store(node1)
        store.store(node2)

        items = dict(store.items())
        assert items["e1"] is node1
        assert items["e2"] is node2


# =============================================================================
# ElementStateStore Tests
# =============================================================================


class TestElementStateStore:
    def test_get_nonexistent_returns_none(self):
        store = ElementStateStore()
        assert store.get("e1") is None

    def test_set_and_get(self):
        store = ElementStateStore()
        state = ElementState(mounted=True)

        store.set("e1", state)
        assert store.get("e1") is state

    def test_get_or_create_new(self):
        store = ElementStateStore()

        state = store.get_or_create("e1")
        assert state is not None
        assert isinstance(state, ElementState)
        assert store.get("e1") is state

    def test_get_or_create_existing(self):
        store = ElementStateStore()
        existing = ElementState(mounted=True)
        store.set("e1", existing)

        state = store.get_or_create("e1")
        assert state is existing

    def test_remove(self):
        store = ElementStateStore()
        store.set("e1", ElementState())

        store.remove("e1")
        assert store.get("e1") is None

    def test_remove_nonexistent_no_error(self):
        store = ElementStateStore()
        store.remove("nonexistent")  # Should not raise

    def test_contains(self):
        store = ElementStateStore()
        store.set("e1", ElementState())

        assert "e1" in store
        assert "e2" not in store

    def test_len(self):
        store = ElementStateStore()
        assert len(store) == 0

        store.set("e1", ElementState())
        assert len(store) == 1

    def test_iter(self):
        store = ElementStateStore()
        store.set("e1", ElementState())
        store.set("e2", ElementState())

        ids = list(store)
        assert set(ids) == {"e1", "e2"}
