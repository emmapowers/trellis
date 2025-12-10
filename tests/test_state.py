"""Tests for trellis.core.state module."""

from dataclasses import dataclass

from trellis.core.rendering import RenderContext
from trellis.core.functional_component import component
from trellis.core.state import Stateful


class TestStateful:
    def test_stateful_set_and_get(self) -> None:
        """State values can be set and retrieved."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "hello"
        assert state.value == "hello"

    def test_stateful_tracks_dependencies(self) -> None:
        """Accessing state during render registers the element as dependent."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> None:
            _ = state.text  # Access the state

        ctx = RenderContext(MyComponent)
        ctx.render_tree(from_element=None)

        # The component should be registered as dependent on state.text
        state_info = state._state_deps["text"]
        assert len(state_info.elements) == 1

    def test_stateful_marks_dirty_on_change(self) -> None:
        """Changing state marks dependent elements as dirty."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> None:
            _ = state.text

        ctx = RenderContext(MyComponent)
        ctx.render_tree(from_element=None)

        # Clear dirty state
        ctx.dirty_elements.clear()
        ctx.root_element.dirty = False

        # Change state
        state.text = "world"

        # Element should be marked dirty
        assert ctx.root_element in ctx.dirty_elements
        assert ctx.root_element.dirty is True

    def test_stateful_render_dirty_updates(self) -> None:
        """render_dirty() re-renders components affected by state changes."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "initial"
        render_count = [0]

        @component
        def MyComponent() -> None:
            render_count[0] += 1
            _ = state.text

        ctx = RenderContext(MyComponent)
        ctx.render_tree(from_element=None)
        assert render_count[0] == 1

        state.text = "changed"
        ctx.render_dirty()
        assert render_count[0] == 2

    def test_fine_grained_tracking(self) -> None:
        """Only components that read a specific property should re-render."""

        @dataclass(kw_only=True, repr=False)
        class MyState(Stateful):
            name: str = ""
            count: int = 0

        state = MyState()
        state.name = ""
        state.count = 0

        name_renders = [0]
        count_renders = [0]

        @component
        def NameComponent() -> None:
            name_renders[0] += 1
            _ = state.name

        @component
        def CountComponent() -> None:
            count_renders[0] += 1
            _ = state.count

        @component
        def Parent() -> None:
            NameComponent()
            CountComponent()

        ctx = RenderContext(Parent)
        ctx.render_tree(from_element=None)

        assert name_renders[0] == 1
        assert count_renders[0] == 1

        # Change only name - only NameComponent should re-render
        state.name = "updated"
        ctx.render_dirty()

        assert name_renders[0] == 2
        assert count_renders[0] == 1  # Should NOT have re-rendered

    def test_state_change_without_render_context(self) -> None:
        """State can be changed outside of a render context."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "one"
        state.value = "two"
        assert state.value == "two"


class TestLocalStatePersistence:
    """Tests for component-local state that persists across re-renders."""

    def test_local_state_persists_across_rerenders(self) -> None:
        """State created in a component persists when re-rendered."""

        instances_created = [0]

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

            def __init__(self) -> None:
                # Track if this is a fresh instance (before super().__init__ sets _initialized)
                is_new = not getattr(self, "_initialized", False)
                super().__init__()
                if is_new:
                    instances_created[0] += 1

        captured_states: list[Stateful] = []

        @component
        def Counter() -> None:
            state = CounterState()
            captured_states.append(state)
            _ = state.count  # Access to register dependency

        ctx = RenderContext(Counter)
        ctx.render_tree(from_element=None)

        assert instances_created[0] == 1

        # Re-render by marking dirty - should reuse same instance
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        assert instances_created[0] == 1  # Still 1, not 2
        assert len(captured_states) == 2
        assert captured_states[0] is captured_states[1]  # Same instance

    def test_local_state_values_preserved(self) -> None:
        """State values are preserved across re-renders."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        observed_counts: list[int] = []

        @component
        def Counter() -> None:
            state = CounterState()
            state.count = state.count  # Initialize on first render
            observed_counts.append(state.count)
            state.count += 1  # Increment each render

        ctx = RenderContext(Counter)
        ctx.render_tree(from_element=None)
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Should see 0, 1, 2 as count persists and increments
        assert observed_counts == [0, 1, 2]

    def test_multiple_state_instances_same_type(self) -> None:
        """Multiple instances of same state type use call order."""

        @dataclass(kw_only=True)
        class ToggleState(Stateful):
            on: bool = False

        @component
        def MultiToggle() -> None:
            first = ToggleState()
            second = ToggleState()
            first.on = True
            second.on = False

        ctx = RenderContext(MultiToggle)
        ctx.render_tree(from_element=None)

        # Re-render - each should get its own cached instance
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        # Check that we have 2 distinct state entries in the root element's cache
        state_keys = [k for k in ctx.root_element._local_state.keys() if k[0].__name__ == "ToggleState"]
        assert len(state_keys) == 2

        # Check they have different call indices
        indices = [k[1] for k in state_keys]
        assert 0 in indices
        assert 1 in indices

    def test_subclass_state_works(self) -> None:
        """Subclassed state types work correctly."""

        @dataclass(kw_only=True)
        class BaseState(Stateful):
            value: int = 0

        @dataclass(kw_only=True)
        class ExtendedState(BaseState):
            extra: str = ""

        @component
        def MyComponent() -> None:
            base = BaseState()
            extended = ExtendedState()
            base.value = 10
            extended.value = 20
            extended.extra = "hello"

        ctx = RenderContext(MyComponent)
        ctx.render_tree(from_element=None)

        # Both should be cached separately by their actual types on the element
        local_state = ctx.root_element._local_state
        base_keys = [k for k in local_state.keys() if k[0].__name__ == "BaseState"]
        ext_keys = [k for k in local_state.keys() if k[0].__name__ == "ExtendedState"]

        assert len(base_keys) == 1
        assert len(ext_keys) == 1

        # Values should be preserved on re-render
        ctx.mark_dirty(ctx.root_element)
        ctx.render_dirty()

        base_instance = local_state[base_keys[0]]
        ext_instance = local_state[ext_keys[0]]

        assert base_instance.value == 10
        assert ext_instance.value == 20
        assert ext_instance.extra == "hello"

    def test_state_outside_render_not_cached(self) -> None:
        """State created outside render context is not cached."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: int = 0

        # Create outside any render
        state1 = MyState()
        state2 = MyState()

        # Should be different instances
        assert state1 is not state2
