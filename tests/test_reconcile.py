"""Tests for reconciliation and lifecycle hooks."""

from dataclasses import dataclass

from trellis.core.rendering import RenderTree
from trellis.core.composition_component import component
from trellis.core.state import Stateful


class TestReconciliation:
    """Tests for the reconciliation algorithm."""

    def test_key_based_matching_preserves_node_id(self) -> None:
        """Nodes with matching keys preserve their ID (for state continuity)."""
        render_order: list[str] = []
        items_ref = [["a", "b", "c"]]

        @component
        def Child(name: str = "") -> None:
            render_order.append(name)

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderTree(Parent)
        ctx.render()

        # Capture original node IDs (string IDs used for state tracking)
        original_children = list(ctx.root_node.children)
        original_node_ids = {c.key: c.id for c in original_children}

        # Re-render with reordered items
        render_order.clear()
        items_ref[0] = ["c", "a", "b"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Node IDs should be preserved (for state continuity) despite reordering
        new_children = list(ctx.root_node.children)
        for child in new_children:
            assert child.id == original_node_ids[child.key]

    def test_position_type_matching_without_keys(self) -> None:
        """Unkeyed elements match by position and type, preserving node IDs."""
        render_count = [0]
        count_ref = [3]

        @component
        def Child() -> None:
            render_count[0] += 1

        @component
        def Parent() -> None:
            for _ in range(count_ref[0]):
                Child()

        ctx = RenderTree(Parent)
        ctx.render()

        original_node_ids = [c.id for c in ctx.root_node.children]

        # Re-render with same count
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Same node IDs should be preserved (for state continuity)
        new_node_ids = [c.id for c in ctx.root_node.children]
        assert original_node_ids == new_node_ids

    def test_type_change_unmounts_old_mounts_new(self) -> None:
        """When component type changes, old unmounts and new mounts."""
        mount_log: list[str] = []
        unmount_log: list[str] = []

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_mount(self) -> None:
                mount_log.append(self.name)

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def TypeA() -> None:
            TrackedState(name="A")

        @component
        def TypeB() -> None:
            TrackedState(name="B")

        show_a = [True]

        @component
        def Parent() -> None:
            if show_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderTree(Parent)
        ctx.render()

        assert "A" in mount_log
        assert len(unmount_log) == 0

        # Switch type
        show_a[0] = False
        mount_log.clear()
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert "A" in unmount_log
        assert "B" in mount_log

    def test_removed_children_unmount(self) -> None:
        """Children that are removed get unmounted."""
        unmount_log: list[str] = []

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def Child(name: str = "") -> None:
            TrackedState(name=name)

        items = [["a", "b", "c"]]

        @component
        def Parent() -> None:
            for item in items[0]:
                Child(key=item, name=item)

        ctx = RenderTree(Parent)
        ctx.render()

        # Remove "b"
        items[0] = ["a", "c"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert "b" in unmount_log
        assert "a" not in unmount_log
        assert "c" not in unmount_log


class TestElementLifecycle:
    """Tests for Element on_mount/on_unmount hooks."""

    def test_element_on_mount_called(self) -> None:
        """on_mount is called when element is first rendered."""

        @component
        def MyComponent() -> None:
            pass

        ctx = RenderTree(MyComponent)
        ctx.render()

        assert ctx._element_state[ctx.root_node.id].mounted is True

    def test_element_not_remounted_on_rerender(self) -> None:
        """on_mount is not called again on re-render."""
        mount_count = [0]

        @dataclass
        class CountingState(Stateful):
            def on_mount(self) -> None:
                mount_count[0] += 1

        @component
        def MyComponent() -> None:
            CountingState()

        ctx = RenderTree(MyComponent)
        ctx.render()
        assert mount_count[0] == 1

        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()
        assert mount_count[0] == 1  # Still 1, not called again


class TestStatefulLifecycle:
    """Tests for Stateful on_mount/on_unmount hooks."""

    def test_stateful_on_mount_called(self) -> None:
        """Stateful.on_mount is called after element mounts."""
        mount_log: list[str] = []

        @dataclass
        class MyState(Stateful):
            def on_mount(self) -> None:
                mount_log.append("state_mounted")

        @component
        def MyComponent() -> None:
            MyState()

        ctx = RenderTree(MyComponent)
        ctx.render()

        assert "state_mounted" in mount_log

    def test_stateful_on_unmount_called(self) -> None:
        """Stateful.on_unmount is called before element unmounts."""
        unmount_log: list[str] = []

        @dataclass
        class MyState(Stateful):
            def on_unmount(self) -> None:
                unmount_log.append("state_unmounted")

        show = [True]

        @component
        def Child() -> None:
            MyState()

        @component
        def Parent() -> None:
            if show[0]:
                Child()

        ctx = RenderTree(Parent)
        ctx.render()

        # Remove child
        show[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert "state_unmounted" in unmount_log

    def test_state_cleanup_on_unmount(self) -> None:
        """State is removed from cache when element unmounts."""
        show = [True]

        @dataclass
        class MyState(Stateful):
            value: int = 0

        @component
        def Child() -> None:
            MyState()

        @component
        def Parent() -> None:
            if show[0]:
                Child()

        ctx = RenderTree(Parent)
        ctx.render()

        # State should be in cache on the child element
        child_node = ctx.root_node.children[0]
        child_state = ctx._element_state[child_node.id]
        assert len(child_state.local_state) == 1

        # Capture child ID before unmounting
        child_id = child_node.id

        # Remove child
        show[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Child was unmounted, state should be cleaned up from the dict
        assert child_id not in ctx._element_state


class TestLifecycleOrder:
    """Tests for correct ordering of lifecycle hooks."""

    def test_mount_order_parent_first(self) -> None:
        """Mount order: parent first, then children."""
        mount_order: list[str] = []

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_mount(self) -> None:
                mount_order.append(self.name)

        @component
        def Child(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def Parent() -> None:
            TrackedState(name="parent")
            Child(name="child1")
            Child(name="child2")

        ctx = RenderTree(Parent)
        ctx.render()

        # Parent should mount before children
        assert mount_order.index("parent") < mount_order.index("child1")
        assert mount_order.index("parent") < mount_order.index("child2")

    def test_unmount_order_children_first(self) -> None:
        """Unmount order: children first, then parent."""
        unmount_order: list[str] = []

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_unmount(self) -> None:
                unmount_order.append(self.name)

        @component
        def Child(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def InnerParent() -> None:
            TrackedState(name="inner_parent")
            Child(name="child1")
            Child(name="child2")

        show = [True]

        @component
        def OuterParent() -> None:
            if show[0]:
                InnerParent()

        ctx = RenderTree(OuterParent)
        ctx.render()

        # Remove inner parent and its children
        show[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Children should unmount before parent
        assert unmount_order.index("child1") < unmount_order.index("inner_parent")
        assert unmount_order.index("child2") < unmount_order.index("inner_parent")


class TestReconciliationAdditional:
    """Additional reconciliation edge case tests."""

    def test_component_type_change_with_deep_subtree(self) -> None:
        """Changing component type unmounts entire subtree."""
        unmount_log: list[str] = []
        use_type_a = [True]

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def DeepLeaf(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def Middle(prefix: str = "") -> None:
            TrackedState(name=f"{prefix}_middle")
            DeepLeaf(name=f"{prefix}_leaf1")
            DeepLeaf(name=f"{prefix}_leaf2")

        @component
        def TypeA() -> None:
            TrackedState(name="a_root")
            Middle(prefix="a")

        @component
        def TypeB() -> None:
            TrackedState(name="b_root")

        @component
        def Parent() -> None:
            if use_type_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderTree(Parent)
        ctx.render()

        # Switch type - entire TypeA subtree should unmount
        use_type_a[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # All TypeA components should be unmounted
        assert "a_root" in unmount_log
        assert "a_middle" in unmount_log
        assert "a_leaf1" in unmount_log
        assert "a_leaf2" in unmount_log

    def test_children_only_change(self) -> None:
        """Reconciliation when only children change, not props."""
        mount_log: list[str] = []
        unmount_log: list[str] = []
        items_ref = [["a", "b"]]

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_mount(self) -> None:
                mount_log.append(self.name)

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def Child(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderTree(Parent)
        ctx.render()

        assert set(mount_log) == {"a", "b"}
        mount_log.clear()

        # Add new item
        items_ref[0] = ["a", "b", "c"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert "c" in mount_log
        assert "a" not in mount_log  # Preserved
        assert "b" not in mount_log  # Preserved
        assert len(unmount_log) == 0

        # Remove item
        mount_log.clear()
        items_ref[0] = ["a", "c"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert "b" in unmount_log
        assert len(mount_log) == 0

    def test_multiple_states_unmount_in_reverse_order(self) -> None:
        """Multiple states on same element unmount in reverse creation order."""
        unmount_order: list[str] = []
        show_ref = [True]

        @dataclass
        class StateA(Stateful):
            def on_unmount(self) -> None:
                unmount_order.append("A")

        @dataclass
        class StateB(Stateful):
            def on_unmount(self) -> None:
                unmount_order.append("B")

        @dataclass
        class StateC(Stateful):
            def on_unmount(self) -> None:
                unmount_order.append("C")

        @component
        def Child() -> None:
            StateA()  # Created first
            StateB()  # Created second
            StateC()  # Created third

        @component
        def Parent() -> None:
            if show_ref[0]:
                Child()

        ctx = RenderTree(Parent)
        ctx.render()

        show_ref[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Should unmount in reverse order: C, B, A
        assert unmount_order == ["C", "B", "A"]

    def test_node_preserves_id_on_props_change(self) -> None:
        """Node ID is preserved when props change (for state continuity)."""

        @component
        def Child(value: int = 0) -> None:
            pass

        value_ref = [1]

        @component
        def Parent() -> None:
            Child(value=value_ref[0])

        ctx = RenderTree(Parent)
        ctx.render()

        # Capture original node ID
        child = ctx.root_node.children[0]
        original_node_id = child.id

        # Change props - triggers reconciliation but should preserve node ID
        value_ref[0] = 2
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Node ID should be preserved for state continuity
        new_child = ctx.root_node.children[0]
        assert new_child.id == original_node_id

        # But props should be updated
        props = dict(new_child.props)
        assert props.get("value") == 2

    def test_reconcile_empty_to_many_children(self) -> None:
        """Reconciling from no children to many children."""
        items_ref: list[list[str]] = [[]]  # Start empty
        mount_log: list[str] = []

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_mount(self) -> None:
                mount_log.append(self.name)

        @component
        def Child(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderTree(Parent)
        ctx.render()

        assert len(ctx.root_node.children) == 0
        assert len(mount_log) == 0

        # Add many children
        items_ref[0] = [f"item_{i}" for i in range(20)]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.children) == 20
        assert len(mount_log) == 20

    def test_reconcile_many_to_empty_children(self) -> None:
        """Reconciling from many children to no children."""
        items_ref = [[f"item_{i}" for i in range(20)]]
        unmount_log: list[str] = []

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def Child(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderTree(Parent)
        ctx.render()

        assert len(ctx.root_node.children) == 20

        # Remove all children
        items_ref[0] = []
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.children) == 0
        assert len(unmount_log) == 20
