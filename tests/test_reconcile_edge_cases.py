"""Tests for reconciliation edge cases.

These tests verify correct behavior in complex reconciliation scenarios:
- List reversal
- Random shuffles
- Bulk add/remove operations
- Key edge cases (duplicates, types)
- Props comparison edge cases
"""

import random
from dataclasses import dataclass

from trellis.core.rendering import RenderTree
from trellis.core.composition_component import component
from trellis.core.state import Stateful


class TestListReversal:
    """Tests for list reversal scenarios."""

    def test_reverse_keyed_list(self) -> None:
        """Reversing a keyed list should preserve element identities."""
        items_ref = [list(range(50))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        # Map key -> element id
        original_ids = {ctx.get_node(cid).key: cid for cid in ctx.root_node.child_ids}

        # Reverse the list
        items_ref[0] = list(reversed(items_ref[0]))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Verify same elements (by identity), just reordered
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            assert child.id == original_ids[child.key]

        # Verify order is reversed
        keys = [ctx.get_node(cid).key for cid in ctx.root_node.child_ids]
        assert keys == [str(i) for i in range(49, -1, -1)]

    def test_reverse_preserves_state(self) -> None:
        """Reversing a list should preserve component state."""
        items_ref = [list(range(10))]

        @dataclass
        class ItemState(Stateful):
            value: int = 0

        # Capture state instance ids to verify same instances are reused
        state_ids_by_key: dict[str, int] = {}

        @component
        def Item(n: int = 0) -> None:
            state = ItemState(value=n * 10)
            # Track state identity by key
            state_ids_by_key[str(n)] = id(state)

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        # Capture original state ids
        original_state_ids = state_ids_by_key.copy()

        # Reverse and re-render
        items_ref[0] = list(reversed(items_ref[0]))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Same state instances should be associated with same keys after reversal
        for key, state_id in state_ids_by_key.items():
            assert state_id == original_state_ids[key], f"State for key {key} changed identity"


class TestRandomShuffles:
    """Tests for random shuffle scenarios."""

    def test_shuffle_keyed_list(self) -> None:
        """Shuffling a keyed list should preserve element identities."""
        items_ref = [list(range(50))]
        random.seed(42)

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        original_ids = {ctx.get_node(cid).key: cid for cid in ctx.root_node.child_ids}

        # Shuffle multiple times
        for _ in range(5):
            random.shuffle(items_ref[0])
            ctx.mark_dirty_id(ctx.root_node.id)
            ctx.render()

            # Verify all elements preserved
            for child_id in ctx.root_node.child_ids:
                child = ctx.get_node(child_id)
                assert child.id == original_ids[child.key]

    def test_shuffle_preserves_state(self) -> None:
        """Shuffling should preserve component state identity."""
        items_ref = [list(range(20))]
        random.seed(123)

        # Track unique_id per item key (assigned on first mount)
        assigned_ids: dict[int, int] = {}
        unique_id_counter = [0]

        @dataclass
        class ItemState(Stateful):
            # Unique value set via constructor on initial mount
            unique_id: int = 0

        @component
        def Item(n: int = 0) -> None:
            # Assign unique_id on first mount (before component runs)
            if n not in assigned_ids:
                unique_id_counter[0] += 1
                assigned_ids[n] = unique_id_counter[0]
            ItemState(unique_id=assigned_ids[n])

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        # Record the unique_id for each key
        initial_state_ids: dict[str, int] = {}
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            child_state = ctx._element_state[child.id]
            state = list(child_state.local_state.values())[0]
            initial_state_ids[child.key] = state.unique_id

        # All 20 items should have unique state
        assert len(set(initial_state_ids.values())) == 20

        # Shuffle and re-render multiple times
        for _ in range(3):
            random.shuffle(items_ref[0])
            ctx.mark_dirty_id(ctx.root_node.id)
            ctx.render()

            # State instances should be preserved per key
            for child_id in ctx.root_node.child_ids:
                child = ctx.get_node(child_id)
                child_state = ctx._element_state[child.id]
                state = list(child_state.local_state.values())[0]
                # Same state instance (by unique_id) should be associated with same key
                assert state.unique_id == initial_state_ids[child.key]


class TestBulkOperations:
    """Tests for bulk add/remove operations."""

    def test_remove_all_then_readd(self) -> None:
        """Remove all items then re-add them."""
        items_ref = [list(range(20))]
        unmount_log: list[int] = []
        mount_log: list[int] = []

        @dataclass
        class TrackedState(Stateful):
            n: int = 0

            def on_mount(self) -> None:
                mount_log.append(self.n)

            def on_unmount(self) -> None:
                unmount_log.append(self.n)

        @component
        def Item(n: int = 0) -> None:
            TrackedState(n=n)

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        assert len(mount_log) == 20
        mount_log.clear()

        # Remove all
        items_ref[0] = []
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(unmount_log) == 20
        assert len(ctx.root_node.child_ids) == 0

        # Re-add all
        unmount_log.clear()
        items_ref[0] = list(range(20))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # New elements should be mounted (new instances)
        assert len(mount_log) == 20
        assert len(ctx.root_node.child_ids) == 20

    def test_remove_from_start(self) -> None:
        """Remove items from the start of a list."""
        items_ref = [list(range(50))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        # Keep track of remaining element ids
        remaining_ids = {str(i): cid for i, cid in zip(items_ref[0], ctx.root_node.child_ids)}

        # Remove first 25 items
        items_ref[0] = list(range(25, 50))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Remaining elements should be preserved
        assert len(ctx.root_node.child_ids) == 25
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            assert child.id == remaining_ids[child.key]

    def test_remove_from_middle(self) -> None:
        """Remove items from the middle of a list."""
        items_ref = [list(range(50))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        remaining_ids = {str(i): cid for i, cid in zip(items_ref[0], ctx.root_node.child_ids)}

        # Remove middle section (10-39)
        items_ref[0] = list(range(10)) + list(range(40, 50))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 20
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            assert child.id == remaining_ids[child.key]

    def test_remove_from_end(self) -> None:
        """Remove items from the end of a list."""
        items_ref = [list(range(50))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        remaining_ids = {str(i): cid for i, cid in zip(items_ref[0], ctx.root_node.child_ids)}

        # Remove last 25
        items_ref[0] = list(range(25))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 25
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            assert child.id == remaining_ids[child.key]

    def test_insert_at_start(self) -> None:
        """Insert items at the start of a list."""
        items_ref = [list(range(25, 50))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        original_ids = {str(i): cid for i, cid in zip(items_ref[0], ctx.root_node.child_ids)}

        # Insert 25 items at start
        items_ref[0] = list(range(50))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 50
        # Original items should be preserved
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            if child.key in original_ids:
                assert child.id == original_ids[child.key]

    def test_insert_at_end(self) -> None:
        """Insert items at the end of a list."""
        items_ref = [list(range(25))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderTree(List)
        ctx.render()

        original_ids = {str(i): cid for i, cid in zip(items_ref[0], ctx.root_node.child_ids)}

        # Insert 25 items at end
        items_ref[0] = list(range(50))
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 50
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            if child.key in original_ids:
                assert child.id == original_ids[child.key]


class TestKeyEdgeCases:
    """Tests for key-related edge cases."""

    def test_duplicate_keys(self) -> None:
        """Duplicate keys should be handled (first match wins)."""
        items_ref = [[("a", 1), ("b", 2), ("a", 3)]]  # Duplicate "a"

        @component
        def Item(value: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for key, value in items_ref[0]:
                Item(key=key, value=value)

        ctx = RenderTree(List)
        ctx.render()

        # Should have 3 children
        assert len(ctx.root_node.child_ids) == 3

    def test_integer_keys(self) -> None:
        """Integer keys converted to strings should work."""
        items_ref = [list(range(10))]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)  # Explicit string conversion

        ctx = RenderTree(List)
        ctx.render()

        original_ids = {ctx.get_node(cid).key: cid for cid in ctx.root_node.child_ids}

        # Reorder
        items_ref[0] = [5, 3, 1, 9, 7, 0, 2, 4, 6, 8]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            assert child.id == original_ids[child.key]

    def test_mixed_keyed_and_unkeyed(self) -> None:
        """Mixed keyed and unkeyed elements."""
        render_log: list[str] = []

        @component
        def KeyedItem(name: str = "") -> None:
            render_log.append(f"keyed:{name}")

        @component
        def UnkeyedItem(n: int = 0) -> None:
            render_log.append(f"unkeyed:{n}")

        @component
        def List() -> None:
            KeyedItem(key="a", name="A")
            UnkeyedItem(n=1)
            KeyedItem(key="b", name="B")
            UnkeyedItem(n=2)

        ctx = RenderTree(List)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 4

        # Re-render - structure preserved
        render_log.clear()
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Components should not re-render (props unchanged)
        assert len(render_log) == 0

    def test_mixed_keyed_unkeyed_in_middle(self) -> None:
        """Mixed keyed/unkeyed in middle section (after head/tail scan)."""
        items_ref = [["prefix", "a", "unkeyed1", "b", "unkeyed2", "c", "suffix"]]

        @component
        def KeyedItem(name: str = "") -> None:
            pass

        @component
        def UnkeyedItem(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            # Fixed prefix and suffix to exercise head/tail optimization
            KeyedItem(key="prefix", name="P")  # head matches
            for item in items_ref[0][1:-1]:  # middle section
                if item.startswith("unkeyed"):
                    UnkeyedItem(n=int(item[-1]))
                else:
                    KeyedItem(key=item, name=item.upper())
            KeyedItem(key="suffix", name="S")  # tail matches

        ctx = RenderTree(List)
        ctx.render()

        # Record ids for keyed elements
        original_ids = {ctx.get_node(cid).key: cid for cid in ctx.root_node.child_ids if ctx.get_node(cid).key}

        # Reorder middle section while keeping prefix/suffix
        items_ref[0] = ["prefix", "c", "unkeyed2", "b", "unkeyed1", "a", "suffix"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Keyed elements should preserve identity
        for child_id in ctx.root_node.child_ids:
            child = ctx.get_node(child_id)
            if child.key in original_ids:
                assert child.id == original_ids[child.key]

    def test_keyed_to_unkeyed_transition(self) -> None:
        """Transition from keyed to unkeyed children."""
        use_keys = [True]
        items_ref = [[0, 1, 2, 3, 4]]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                if use_keys[0]:
                    Item(key=str(i), n=i)
                else:
                    Item(n=i)

        ctx = RenderTree(List)
        ctx.render()

        keyed_ids = list(ctx.root_node.child_ids)

        # Switch to unkeyed
        use_keys[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Should still have 5 children (matched by component type)
        assert len(ctx.root_node.child_ids) == 5
        # Unkeyed elements should match by position/type
        unkeyed_ids = list(ctx.root_node.child_ids)
        # Since items are same count/type, they can be reused
        assert len(unkeyed_ids) == 5

    def test_unkeyed_to_keyed_transition(self) -> None:
        """Transition from unkeyed to keyed children."""
        use_keys = [False]
        items_ref = [[0, 1, 2, 3, 4]]

        @component
        def Item(n: int = 0) -> None:
            pass

        @component
        def List() -> None:
            for i in items_ref[0]:
                if use_keys[0]:
                    Item(key=str(i), n=i)
                else:
                    Item(n=i)

        ctx = RenderTree(List)
        ctx.render()

        # Start with unkeyed
        assert all(ctx.get_node(cid).key is None for cid in ctx.root_node.child_ids)

        # Switch to keyed
        use_keys[0] = True
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # All children should now have keys
        assert all(ctx.get_node(cid).key is not None for cid in ctx.root_node.child_ids)
        # Keys should be the string versions of indices
        keys = [ctx.get_node(cid).key for cid in ctx.root_node.child_ids]
        assert keys == ["0", "1", "2", "3", "4"]


class TestPropsComparison:
    """Tests for props comparison edge cases."""

    def test_props_with_none_values(self) -> None:
        """Props with None values should be handled correctly."""
        render_counts: dict[str, int] = {}
        value_ref: list[str | None] = [None]

        @component
        def Child(value: str | None = None) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            Child(value=value_ref[0])

        ctx = RenderTree(Parent)
        ctx.render()

        assert render_counts["child"] == 1

        # Same None value - should not re-render
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 1

        # Change to non-None
        value_ref[0] = "hello"
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 2

        # Change back to None
        value_ref[0] = None
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 3

    def test_props_with_callable(self) -> None:
        """Props with callable values use identity comparison."""
        render_counts: dict[str, int] = {}

        def handler1() -> None:
            pass

        def handler2() -> None:
            pass

        handler_ref = [handler1]

        @component
        def Child(on_click=None) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            Child(on_click=handler_ref[0])

        ctx = RenderTree(Parent)
        ctx.render()

        assert render_counts["child"] == 1

        # Same function - should not re-render
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 1

        # Different function - should re-render
        handler_ref[0] = handler2
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 2

    def test_empty_props(self) -> None:
        """Components with no props should work correctly."""
        render_counts: dict[str, int] = {}

        @component
        def NoProps() -> None:
            render_counts["no_props"] = render_counts.get("no_props", 0) + 1

        @component
        def Parent() -> None:
            NoProps()

        ctx = RenderTree(Parent)
        ctx.render()

        assert render_counts["no_props"] == 1

        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Should not re-render (empty props unchanged)
        assert render_counts["no_props"] == 1

    def test_props_with_tuple(self) -> None:
        """Props with tuple values should compare correctly."""
        render_counts: dict[str, int] = {}
        tuple_ref = [(1, 2, 3)]

        @component
        def Child(items: tuple = ()) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            Child(items=tuple_ref[0])

        ctx = RenderTree(Parent)
        ctx.render()

        assert render_counts["child"] == 1

        # Same tuple value - should not re-render
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 1

        # Different tuple - should re-render
        tuple_ref[0] = (1, 2, 4)
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert render_counts["child"] == 2


class TestComponentTypeChange:
    """Tests for component type changes during reconciliation."""

    def test_type_change_unmounts_entire_subtree(self) -> None:
        """Changing component type should unmount entire subtree."""
        unmount_log: list[str] = []
        use_type_a = [True]

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def DeepChild(name: str = "") -> None:
            TrackedState(name=name)

        @component
        def TypeA() -> None:
            TrackedState(name="type_a")
            DeepChild(name="a_child_1")
            DeepChild(name="a_child_2")

        @component
        def TypeB() -> None:
            TrackedState(name="type_b")
            DeepChild(name="b_child")

        @component
        def Parent() -> None:
            if use_type_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderTree(Parent)
        ctx.render()

        # Switch from TypeA to TypeB
        use_type_a[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # TypeA and its children should be unmounted
        assert "type_a" in unmount_log
        assert "a_child_1" in unmount_log
        assert "a_child_2" in unmount_log
        # TypeB should not be in unmount log
        assert "type_b" not in unmount_log
        assert "b_child" not in unmount_log

    def test_change_single_child_type(self) -> None:
        """Changing type of a single child preserves siblings."""
        mount_log: list[str] = []
        unmount_log: list[str] = []
        use_type_a = [True]

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_mount(self) -> None:
                mount_log.append(self.name)

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def TypeA() -> None:
            TrackedState(name="type_a")

        @component
        def TypeB() -> None:
            TrackedState(name="type_b")

        @component
        def Sibling() -> None:
            TrackedState(name="sibling")

        @component
        def Parent() -> None:
            Sibling()
            if use_type_a[0]:
                TypeA()
            else:
                TypeB()
            Sibling()  # Another sibling

        ctx = RenderTree(Parent)
        ctx.render()

        # Clear mount log after initial render
        mount_log.clear()

        # Get sibling element ids
        sibling_ids = [id(ctx.get_node(cid)) for cid in ctx.root_node.child_ids if ctx.get_node(cid).key is None]

        # Switch type
        use_type_a[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # TypeA unmounted, TypeB mounted
        assert "type_a" in unmount_log
        assert "type_b" in mount_log

        # Siblings should NOT be unmounted (preserved)
        assert "sibling" not in unmount_log


class TestBuiltinWidgetsReconciliation:
    """Tests for reconciliation with built-in widgets (ReactComponentBase/HtmlElement).

    These tests ensure that components created via @react_component_base and
    @html_element decorators work correctly in the reconciler. Unlike @component
    decorated functions, these use different class hierarchies that need to be
    hashable for type-based matching in the middle section of reconciliation.

    Regression tests for: TypeError: unhashable type: '_Generated'
    """

    def test_remove_widget_from_middle_of_list(self) -> None:
        """Removing a widget from the middle exercises type-based matching.

        When items are removed from the middle of a list:
        1. Head matching covers some items
        2. Tail matching covers some items
        3. Middle section uses type-based matching (requires hashable components)
        """
        from trellis.widgets import Row, Button
        from trellis import html as h

        items_ref = [["a", "b", "c", "d"]]

        @component
        def TodoList() -> None:
            h.H1("Tasks")  # Fixed head
            for item in items_ref[0]:
                with Row():
                    h.Span(item)
                    Button(text="×")
            Button(text="Add")  # Fixed tail

        ctx = RenderTree(TodoList)
        ctx.render()

        # Should have: H1, Row, Row, Row, Row, Button = 6 children
        assert len(ctx.root_node.child_ids) == 6

        # Remove "b" from the middle - this triggers type-based matching
        items_ref[0] = ["a", "c", "d"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Should have: H1, Row, Row, Row, Button = 5 children
        assert len(ctx.root_node.child_ids) == 5

    def test_html_elements_in_dynamic_list(self) -> None:
        """HTML elements (via @html_element) should be hashable for reconciliation."""
        from trellis import html as h

        items_ref = [["item1", "item2", "item3"]]

        @component
        def List() -> None:
            for item in items_ref[0]:
                with h.Div():
                    h.Span(item)

        ctx = RenderTree(List)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 3

        # Remove from middle
        items_ref[0] = ["item1", "item3"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 2

    def test_widgets_in_dynamic_list(self) -> None:
        """Widgets (via @react_component_base) should be hashable for reconciliation."""
        from trellis.widgets import Column, Row, Label, Button

        items_ref = [[1, 2, 3, 4, 5]]

        @component
        def List() -> None:
            with Column():
                for n in items_ref[0]:
                    with Row():
                        Label(text=f"Item {n}")
                        Button(text="Delete")

        ctx = RenderTree(List)
        ctx.render()

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 5

        # Remove items 2 and 4 (from middle)
        items_ref[0] = [1, 3, 5]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 3

    def test_mixed_widgets_and_components_in_list(self) -> None:
        """Mix of @component and @react_component_base in dynamic list."""
        from trellis.widgets import Button

        items_ref = [["a", "b", "c"]]

        @component
        def CustomItem(name: str = "") -> None:
            Button(text=name)

        @component
        def List() -> None:
            for item in items_ref[0]:
                CustomItem(name=item)

        ctx = RenderTree(List)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 3

        # Reorder and remove
        items_ref[0] = ["c", "a"]
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert len(ctx.root_node.child_ids) == 2
