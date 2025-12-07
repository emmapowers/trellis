"""Tests for reconciliation and lifecycle hooks."""

from dataclasses import dataclass

from trellis.core.rendering import RenderContext
from trellis.core.functional_component import component
from trellis.core.state import Stateful


class TestReconciliation:
    """Tests for the reconciliation algorithm."""

    def test_key_based_matching_preserves_element(self) -> None:
        """Elements with matching keys preserve identity."""
        render_order: list[str] = []
        items_ref = [["a", "b", "c"]]

        @component
        def Child(name: str = "") -> None:
            render_order.append(name)

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        # Capture original element ids
        original_children = list(ctx.root_element.children)
        original_ids = {c.key: id(c) for c in original_children}

        # Re-render with reordered items
        render_order.clear()
        items_ref[0] = ["c", "a", "b"]
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Elements should be preserved (same id) despite reordering
        new_children = list(ctx.root_element.children)
        for child in new_children:
            assert id(child) == original_ids[child.key]

    def test_position_type_matching_without_keys(self) -> None:
        """Unkeyed elements match by position and type."""
        render_count = [0]
        count_ref = [3]

        @component
        def Child() -> None:
            render_count[0] += 1

        @component
        def Parent() -> None:
            for _ in range(count_ref[0]):
                Child()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        original_ids = [id(c) for c in ctx.root_element.children]

        # Re-render with same count
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Same elements should be reused
        new_ids = [id(c) for c in ctx.root_element.children]
        assert original_ids == new_ids

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
            state = TrackedState()
            state.name = "A"

        @component
        def TypeB() -> None:
            state = TrackedState()
            state.name = "B"

        show_a = [True]

        @component
        def Parent() -> None:
            if show_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert "A" in mount_log
        assert len(unmount_log) == 0

        # Switch type
        show_a[0] = False
        mount_log.clear()
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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
            state = TrackedState()
            state.name = name

        items = [["a", "b", "c"]]

        @component
        def Parent() -> None:
            for item in items[0]:
                Child(key=item, name=item)

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        # Remove "b"
        items[0] = ["a", "c"]
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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

        ctx = RenderContext(MyComponent)
        ctx.render(from_element=None)

        assert ctx.root_element._mounted is True

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

        ctx = RenderContext(MyComponent)
        ctx.render(from_element=None)
        assert mount_count[0] == 1

        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()
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

        ctx = RenderContext(MyComponent)
        ctx.render(from_element=None)

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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        # Remove child
        show[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        # State should be in cache on the child element
        child_element = ctx.root_element.children[0]
        assert len(child_element._local_state) == 1

        # Remove child
        show[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Child was unmounted, state should be cleaned up
        assert len(child_element._local_state) == 0


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
            state = TrackedState()
            state.name = name

        @component
        def Parent() -> None:
            state = TrackedState()
            state.name = "parent"
            Child(name="child1")
            Child(name="child2")

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

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
            state = TrackedState()
            state.name = name

        @component
        def InnerParent() -> None:
            state = TrackedState()
            state.name = "inner_parent"
            Child(name="child1")
            Child(name="child2")

        show = [True]

        @component
        def OuterParent() -> None:
            if show[0]:
                InnerParent()

        ctx = RenderContext(OuterParent)
        ctx.render(from_element=None)

        # Remove inner parent and its children
        show[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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
            state = TrackedState()
            state.name = name

        @component
        def Middle(prefix: str = "") -> None:
            state = TrackedState()
            state.name = f"{prefix}_middle"
            DeepLeaf(name=f"{prefix}_leaf1")
            DeepLeaf(name=f"{prefix}_leaf2")

        @component
        def TypeA() -> None:
            state = TrackedState()
            state.name = "a_root"
            Middle(prefix="a")

        @component
        def TypeB() -> None:
            state = TrackedState()
            state.name = "b_root"

        @component
        def Parent() -> None:
            if use_type_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        # Switch type - entire TypeA subtree should unmount
        use_type_a[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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
            state = TrackedState()
            state.name = name

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert set(mount_log) == {"a", "b"}
        mount_log.clear()

        # Add new item
        items_ref[0] = ["a", "b", "c"]
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert "c" in mount_log
        assert "a" not in mount_log  # Preserved
        assert "b" not in mount_log  # Preserved
        assert len(unmount_log) == 0

        # Remove item
        mount_log.clear()
        items_ref[0] = ["a", "c"]
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        show_ref[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Should unmount in reverse order: C, B, A
        assert unmount_order == ["C", "B", "A"]

    def test_element_replace_preserves_identity(self) -> None:
        """Element.replace() updates fields but preserves object identity."""
        element_refs: list[int] = []

        @component
        def Child(value: int = 0) -> None:
            pass

        value_ref = [1]

        @component
        def Parent() -> None:
            Child(value=value_ref[0])

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        # Capture original element id
        child = ctx.root_element.children[0]
        original_id = id(child)
        element_refs.append(original_id)

        # Change props - triggers reconciliation but should preserve element
        value_ref[0] = 2
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Same element object
        new_child = ctx.root_element.children[0]
        assert id(new_child) == original_id

        # But props should be updated
        props = dict(new_child.descriptor.props)
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
            state = TrackedState()
            state.name = name

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 0
        assert len(mount_log) == 0

        # Add many children
        items_ref[0] = [f"item_{i}" for i in range(20)]
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 20
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
            state = TrackedState()
            state.name = name

        @component
        def Parent() -> None:
            for item in items_ref[0]:
                Child(key=item, name=item)

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

        assert len(ctx.root_element.children) == 20

        # Remove all children
        items_ref[0] = []
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 0
        assert len(unmount_log) == 20
