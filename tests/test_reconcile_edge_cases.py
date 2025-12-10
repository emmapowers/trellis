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

from trellis.core.rendering import RenderContext
from trellis.core.functional_component import component
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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        # Map key -> element id
        original_ids = {c.key: id(c) for c in ctx.root_element.children}

        # Reverse the list
        items_ref[0] = list(reversed(items_ref[0]))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Verify same elements (by identity), just reordered
        for child in ctx.root_element.children:
            assert id(child) == original_ids[child.key]

        # Verify order is reversed
        keys = [c.key for c in ctx.root_element.children]
        assert keys == [str(i) for i in range(49, -1, -1)]

    def test_reverse_preserves_state(self) -> None:
        """Reversing a list should preserve component state."""
        items_ref = [list(range(10))]
        state_values: dict[int, int] = {}

        @dataclass
        class ItemState(Stateful):
            value: int = 0

        @component
        def Item(n: int = 0) -> None:
            state = ItemState()
            # Initialize state value on first render
            if state.value == 0:
                state.value = n * 10
            state_values[n] = state.value

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        # Each item should have state value = n * 10
        assert state_values == {i: i * 10 for i in range(10)}

        # Reverse and re-render
        state_values.clear()
        items_ref[0] = list(reversed(items_ref[0]))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # State should be preserved per key (elements don't re-render since props unchanged)
        # But wait - after reversal, the elements don't re-execute since props unchanged
        # So state_values would be empty after clear(). Let me re-check the logic.
        # Actually, the elements ARE keyed but parent re-renders them. The props (n) are unchanged
        # per key, so execution is skipped. Let me not clear and instead verify the state persists.

        # Actually let's verify differently - elements have state, let's check the state is preserved
        # by checking element._local_state
        for child in ctx.root_element.children:
            # Get the n prop from the descriptor
            n = dict(child.descriptor.props).get("n", 0)
            # State should have value = n * 10
            state = list(child._local_state.values())[0]
            assert state.value == n * 10


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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        original_ids = {c.key: id(c) for c in ctx.root_element.children}

        # Shuffle multiple times
        for _ in range(5):
            random.shuffle(items_ref[0])
            ctx.mark_dirty(ctx.root_element)
            ctx.render_dirty()

            # Verify all elements preserved
            for child in ctx.root_element.children:
                assert id(child) == original_ids[child.key]

    def test_shuffle_preserves_state(self) -> None:
        """Shuffling should preserve component state identity."""
        items_ref = [list(range(20))]
        random.seed(123)

        @dataclass
        class ItemState(Stateful):
            # Unique value set only on initial mount
            unique_id: int = 0

        unique_id_counter = [0]

        @component
        def Item(n: int = 0) -> None:
            state = ItemState()
            # Only set unique_id if not already set (on first mount)
            if state.unique_id == 0:
                unique_id_counter[0] += 1
                state.unique_id = unique_id_counter[0]

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        # Record the unique_id for each key
        initial_state_ids: dict[str, int] = {}
        for child in ctx.root_element.children:
            state = list(child._local_state.values())[0]
            initial_state_ids[child.key] = state.unique_id

        # All 20 items should have unique state
        assert len(set(initial_state_ids.values())) == 20

        # Shuffle and re-render multiple times
        for _ in range(3):
            random.shuffle(items_ref[0])
            ctx.mark_dirty(ctx.root_element)
            ctx.render_dirty()

            # State instances should be preserved per key
            for child in ctx.root_element.children:
                state = list(child._local_state.values())[0]
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
            state = TrackedState()
            state.n = n

        @component
        def List() -> None:
            for i in items_ref[0]:
                Item(key=str(i), n=i)

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        assert len(mount_log) == 20
        mount_log.clear()

        # Remove all
        items_ref[0] = []
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(unmount_log) == 20
        assert len(ctx.root_element.children) == 0

        # Re-add all
        unmount_log.clear()
        items_ref[0] = list(range(20))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # New elements should be mounted (new instances)
        assert len(mount_log) == 20
        assert len(ctx.root_element.children) == 20

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        # Keep track of remaining element ids
        remaining_ids = {str(i): id(c) for i, c in zip(items_ref[0], ctx.root_element.children)}

        # Remove first 25 items
        items_ref[0] = list(range(25, 50))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Remaining elements should be preserved
        assert len(ctx.root_element.children) == 25
        for child in ctx.root_element.children:
            assert id(child) == remaining_ids[child.key]

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        remaining_ids = {str(i): id(c) for i, c in zip(items_ref[0], ctx.root_element.children)}

        # Remove middle section (10-39)
        items_ref[0] = list(range(10)) + list(range(40, 50))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 20
        for child in ctx.root_element.children:
            assert id(child) == remaining_ids[child.key]

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        remaining_ids = {str(i): id(c) for i, c in zip(items_ref[0], ctx.root_element.children)}

        # Remove last 25
        items_ref[0] = list(range(25))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 25
        for child in ctx.root_element.children:
            assert id(child) == remaining_ids[child.key]

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        original_ids = {str(i): id(c) for i, c in zip(items_ref[0], ctx.root_element.children)}

        # Insert 25 items at start
        items_ref[0] = list(range(50))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 50
        # Original items should be preserved
        for child in ctx.root_element.children:
            if child.key in original_ids:
                assert id(child) == original_ids[child.key]

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        original_ids = {str(i): id(c) for i, c in zip(items_ref[0], ctx.root_element.children)}

        # Insert 25 items at end
        items_ref[0] = list(range(50))
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert len(ctx.root_element.children) == 50
        for child in ctx.root_element.children:
            if child.key in original_ids:
                assert id(child) == original_ids[child.key]


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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        # Should have 3 children
        assert len(ctx.root_element.children) == 3

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        original_ids = {c.key: id(c) for c in ctx.root_element.children}

        # Reorder
        items_ref[0] = [5, 3, 1, 9, 7, 0, 2, 4, 6, 8]
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        for child in ctx.root_element.children:
            assert id(child) == original_ids[child.key]

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

        ctx = RenderContext(List)
        ctx.render_tree(from_element=None)

        assert len(ctx.root_element.children) == 4

        # Re-render - structure preserved
        render_log.clear()
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Components should not re-render (props unchanged)
        assert len(render_log) == 0


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

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        assert render_counts["child"] == 1

        # Same None value - should not re-render
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert render_counts["child"] == 1

        # Change to non-None
        value_ref[0] = "hello"
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert render_counts["child"] == 2

        # Change back to None
        value_ref[0] = None
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        assert render_counts["child"] == 1

        # Same function - should not re-render
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert render_counts["child"] == 1

        # Different function - should re-render
        handler_ref[0] = handler2
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        assert render_counts["no_props"] == 1

        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        assert render_counts["child"] == 1

        # Same tuple value - should not re-render
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert render_counts["child"] == 1

        # Different tuple - should re-render
        tuple_ref[0] = (1, 2, 4)
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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
            state = TrackedState()
            state.name = name

        @component
        def TypeA() -> None:
            state = TrackedState()
            state.name = "type_a"
            DeepChild(name="a_child_1")
            DeepChild(name="a_child_2")

        @component
        def TypeB() -> None:
            state = TrackedState()
            state.name = "type_b"
            DeepChild(name="b_child")

        @component
        def Parent() -> None:
            if use_type_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        # Switch from TypeA to TypeB
        use_type_a[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

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
            state = TrackedState()
            state.name = "type_a"

        @component
        def TypeB() -> None:
            state = TrackedState()
            state.name = "type_b"

        @component
        def Sibling() -> None:
            state = TrackedState()
            state.name = "sibling"

        @component
        def Parent() -> None:
            Sibling()
            if use_type_a[0]:
                TypeA()
            else:
                TypeB()
            Sibling()  # Another sibling

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        # Clear mount log after initial render
        mount_log.clear()

        # Get sibling element ids
        sibling_ids = [id(c) for c in ctx.root_element.children if c.key == ""]

        # Switch type
        use_type_a[0] = False
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # TypeA unmounted, TypeB mounted
        assert "type_a" in unmount_log
        assert "type_b" in mount_log

        # Siblings should NOT be unmounted (preserved)
        assert "sibling" not in unmount_log
