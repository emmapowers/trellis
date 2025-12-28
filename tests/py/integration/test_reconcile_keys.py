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
    """
    Mark the session's root element as dirty and trigger a render pass.
    
    Parameters:
        ctx (RenderSession): Render session whose root element will be re-rendered.
    """
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
            """
            Render a Label for each item in the current AppState, using each item value as the element key.
            
            This function obtains the AppState from the render context and iterates over state.items, rendering a Label with text set to the item and key set to the item for each entry.
            """
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            """
            Root component that mounts the App inside the surrounding stateful context.
            
            Used by tests to render the App with `state` active so the component tree is created within the shared state scope.
            """
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

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
            """
            Render a single Label whose key is derived from the current AppState from context.
            
            Reads AppState from the component context and renders a Label with text "Static"
            and a key formed as "label-{state.key_suffix}".
            """
            state = AppState.from_context()
            Label(text="Static", key=f"label-{state.key_suffix}")

        state = AppState()

        @component
        def Root() -> None:
            """
            Root component that mounts the App inside the surrounding stateful context.
            
            Used by tests to render the App with `state` active so the component tree is created within the shared state scope.
            """
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
        """
        Verify that rendering two sibling elements with the same explicit key does not crash and both elements are created.
        
        Renders two Label components that share the same key and asserts that the root contains two child elements.
        """

        @component
        def App() -> None:
            # Both labels have same key - edge case, but shouldn't crash
            """
            Render two Label widgets that share the same explicit key to exercise duplicate-key reconciliation behavior.
            
            Used by integration tests to verify the renderer accepts duplicate keys under the same parent and still produces both label elements.
            """
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
            """
            Render two Label widgets that share the same explicit key to exercise duplicate-key reconciliation.
            
            Each Label's displayed text includes the current state's `count`; both Labels use the key "dup" so they are rendered as distinct sibling elements with identical keys for testing duplicate-key behavior.
            """
            state = AppState.from_context()
            Label(text=f"First-{state.count}", key="dup")
            Label(text=f"Second-{state.count}", key="dup")

        state = AppState()

        @component
        def Root() -> None:
            """
            Root component that mounts the App inside the surrounding stateful context.
            
            Used by tests to render the App with `state` active so the component tree is created within the shared state scope.
            """
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

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
            """
            Render five Label widgets without explicit keys, relying on their position for element identity.
            
            Each rendered Label displays text "Item 0" through "Item 4".
            """
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
            """
            Render a single Label whose key contains a slash.
            
            Used by tests to verify that reconciliation correctly handles keys with forward slashes.
            """
            Label(text="Path", key="path/to/item")

        ctx = RenderSession(App)
        render(ctx)

        # Element should render without issues
        assert len(ctx.root_element.child_ids) == 1

    def test_key_with_colon(self) -> None:
        """Key containing colon is handled correctly."""

        @component
        def App() -> None:
            """
            Render a Label widget that uses a namespaced explicit key.
            
            Renders a Label with the text "Namespaced" and the explicit key "ns:item" to test key handling for namespaced keys.
            """
            Label(text="Namespaced", key="ns:item")

        ctx = RenderSession(App)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 1

    def test_key_with_at_sign(self) -> None:
        """
        Verify that an element with a key containing the '@' character is rendered and reconciled as a single child.
        
        Renders a Label with the key "user@example.com" and asserts the root element contains exactly one child.
        """

        @component
        def App() -> None:
            """
            Render a Label with the text "Email" and the explicit key "user@example.com".
            
            Creates a single Label element labeled "Email" and assigns the key "user@example.com" to control reconciliation identity.
            """
            Label(text="Email", key="user@example.com")

        ctx = RenderSession(App)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 1

    def test_key_with_unicode(self) -> None:
        """Key containing unicode characters is handled correctly."""

        @component
        def App() -> None:
            """
            Render a simple component that emits a Label with a Unicode-containing key.
            
            Renders a Label widget with text "Unicode" and the explicit key "item-日本語" to exercise handling of keys that include non-ASCII characters.
            """
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
            """
            Render a Label for each item in the current AppState, using each item value as the element key.
            
            This function obtains the AppState from the render context and iterates over state.items, rendering a Label with text set to the item and key set to the item for each entry.
            """
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            """
            Root component that mounts the App inside the surrounding stateful context.
            
            Used by tests to render the App with `state` active so the component tree is created within the shared state scope.
            """
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
            """
            Render a Label for each item in the current AppState, using each item value as the element key.
            
            This function obtains the AppState from the render context and iterates over state.items, rendering a Label with text set to the item and key set to the item for each entry.
            """
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            """
            Root component that mounts the App inside the surrounding stateful context.
            
            Used by tests to render the App with `state` active so the component tree is created within the shared state scope.
            """
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_ids = {ctx.elements.get(id).key: id for id in app_element.child_ids}

        # Remove middle item
        state.items = ["a", "c"]
        rerender(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_ids = {ctx.elements.get(id).key: id for id in app_element.child_ids}

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
            """
            Render a Label for each item in the current AppState, using each item value as the element key.
            
            This function obtains the AppState from the render context and iterates over state.items, rendering a Label with text set to the item and key set to the item for each entry.
            """
            state = AppState.from_context()
            for item in state.items:
                Label(text=item, key=item)

        state = AppState()

        @component
        def Root() -> None:
            """
            Root component that mounts the App inside the surrounding stateful context.
            
            Used by tests to render the App with `state` active so the component tree is created within the shared state scope.
            """
            with state:
                App()

        ctx = RenderSession(Root)
        render(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        initial_ids = {ctx.elements.get(id).key: id for id in app_element.child_ids}

        # Insert in middle
        state.items = ["a", "b", "c"]
        rerender(ctx)

        app_element = ctx.elements.get(ctx.root_element.child_ids[0])
        final_ids = {ctx.elements.get(id).key: id for id in app_element.child_ids}

        # "a" and "c" should have same IDs
        assert initial_ids["a"] == final_ids["a"]
        assert initial_ids["c"] == final_ids["c"]
        # "b" is new
        assert "b" in final_ids
        assert len(app_element.child_ids) == 3