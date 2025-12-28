"""Integration tests for reconciler key handling during full render cycles.

These tests verify that the reconciler handles keys correctly when components
render with explicit keys, including edge cases like duplicate keys.
"""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful
from trellis.widgets import Label


def rerender(ctx: RenderSession) -> None:
    """Mark root as dirty and re-render."""
    ctx.dirty.mark(ctx.root_element.id)
    render(ctx)


class TestExplicitKeyReconciliation:
    """Tests for reconciliation with explicit keys."""

    def test_same_key_across_renders_preserves_state(self) -> None:
        """Components with same key across renders are matched."""

        class AppState(Stateful):
            items: list[str] = ["a", "b", "c"]

        @component
        def App() -> None:
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            with state:
                App()

        ctx = RenderSession(Root)
        patches = render(ctx)

        # Capture initial child IDs
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_child_ids = set(app_element.child_ids)

        # Reorder items
        state.items = ["c", "a", "b"]
        rerender(ctx)

        # Child IDs should remain the same (matched by key)
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_child_ids = set(app_element.child_ids)

        assert initial_child_ids == final_child_ids

    def test_key_change_triggers_replacement(self) -> None:
        """Changing a component's key triggers removal and re-add."""

        class AppState(Stateful):
            key_suffix: str = "v1"

        @component
        def App() -> None:
            state = AppState.from_context()
            Label(text="Static", key=f"label-{state.key_suffix}")

        state = AppState()

        @component
        def Root() -> None:
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        # Get initial label ID
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_label_id = app_element.child_ids[0]

        # Change key
        state.key_suffix = "v2"
        rerender(ctx)

        # Label should have new ID (different key = new element)
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_label_id = app_element.child_ids[0]

        assert initial_label_id != final_label_id


class TestDuplicateKeyIntegration:
    """Integration tests for duplicate key handling."""

    def test_duplicate_keys_in_same_parent(self) -> None:
        """Duplicate keys in same parent don't crash."""

        @component
        def App() -> None:
            # Both labels have same key - edge case, but shouldn't crash
            Label(text="First", key="duplicate")
            Label(text="Second", key="duplicate")

        ctx = RenderSession(App)
        render(ctx)

        # Both elements should exist
        assert len(ctx.root_element.child_ids) == 2

    def test_duplicate_keys_rerender_stable(self) -> None:
        """Re-rendering with duplicate keys is stable."""

        class AppState(Stateful):
            count: int = 0

        @component
        def App() -> None:
            state = AppState.from_context()
            Label(text=f"First-{state.count}", key="dup")
            Label(text=f"Second-{state.count}", key="dup")

        state = AppState()

        @component
        def Root() -> None:
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        initial_count = len(ctx.root_element.child_ids[0])

        # Trigger re-render
        state.count = 1
        rerender(ctx)

        # Should still render without issues
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        assert len(app_element.child_ids) == 2

    def test_position_based_keys_unique(self) -> None:
        """Components without explicit keys get unique position-based IDs."""

        @component
        def App() -> None:
            for i in range(5):
                Label(text=f"Item {i}")  # No key - uses position

        ctx = RenderSession(App)
        render(ctx)

        # All 5 elements should have unique IDs
        child_ids = ctx.root_element.child_ids
        assert len(child_ids) == 5
        assert len(set(child_ids)) == 5  # All unique


class TestKeySpecialCharacters:
    """Tests for keys with special characters."""

    def test_key_with_slash(self) -> None:
        """Key containing slash is handled correctly."""

        @component
        def App() -> None:
            Label(text="Path", key="path/to/item")

        ctx = RenderSession(App)
        render(ctx)

        # Element should render without issues
        assert len(ctx.root_element.child_ids) == 1

    def test_key_with_colon(self) -> None:
        """Key containing colon is handled correctly."""

        @component
        def App() -> None:
            Label(text="Namespaced", key="ns:item")

        ctx = RenderSession(App)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 1

    def test_key_with_at_sign(self) -> None:
        """Key containing @ is handled correctly."""

        @component
        def App() -> None:
            Label(text="Email", key="user@example.com")

        ctx = RenderSession(App)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 1

    def test_key_with_unicode(self) -> None:
        """Key containing unicode characters is handled correctly."""

        @component
        def App() -> None:
            Label(text="Unicode", key="item-日本語")

        ctx = RenderSession(App)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 1


class TestKeyReorderingPatterns:
    """Tests for common key reordering patterns."""

    def test_reverse_order(self) -> None:
        """Reversing list order with keys maintains element identity."""

        class AppState(Stateful):
            items: list[str] = ["a", "b", "c"]

        @component
        def App() -> None:
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        # Get initial state
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_ids = app_element.child_ids[:]

        # Reverse
        state.items = ["c", "b", "a"]
        rerender(ctx)

        # Get final state
        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_ids = app_element.child_ids[:]

        # Same IDs, different order
        assert set(initial_ids) == set(final_ids)
        assert final_ids == list(reversed(initial_ids))

    def test_remove_middle_item(self) -> None:
        """Removing middle item with keys maintains other elements."""

        class AppState(Stateful):
            items: list[str] = ["a", "b", "c"]

        @component
        def App() -> None:
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_ids = {
            ctx.elements.get(id).key: id for id in app_element.child_ids
        }

        # Remove middle item
        state.items = ["a", "c"]
        rerender(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_ids = {
            ctx.elements.get(id).key: id for id in app_element.child_ids
        }

        # "a" and "c" should have same IDs
        assert initial_ids["a"] == final_ids["a"]
        assert initial_ids["c"] == final_ids["c"]
        assert len(app_element.child_ids) == 2

    def test_insert_middle_item(self) -> None:
        """Inserting item in middle with keys maintains other elements."""

        class AppState(Stateful):
            items: list[str] = ["a", "c"]

        @component
        def App() -> None:
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_ids = {
            ctx.elements.get(id).key: id for id in app_element.child_ids
        }

        # Insert in middle
        state.items = ["a", "b", "c"]
        rerender(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_ids = {
            ctx.elements.get(id).key: id for id in app_element.child_ids
        }

        # "a" and "c" should have same IDs
        assert initial_ids["a"] == final_ids["a"]
        assert initial_ids["c"] == final_ids["c"]
        # "b" is new
        assert "b" in final_ids
        assert len(app_element.child_ids) == 3
