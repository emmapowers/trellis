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
