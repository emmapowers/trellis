"""Tests for trellis.core.state module."""

from dataclasses import dataclass

from trellis.core.rendering import Elements, RenderContext
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
        def MyComponent() -> Elements:
            _ = state.text  # Access the state
            return None

        ctx = RenderContext(MyComponent)
        ctx.render(from_element=None)

        # The component should be registered as dependent on state.text
        state_info = state._state_properties["text"]
        assert len(state_info.elements) == 1

    def test_stateful_marks_dirty_on_change(self) -> None:
        """Changing state marks dependent elements as dirty."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> Elements:
            _ = state.text
            return None

        ctx = RenderContext(MyComponent)
        ctx.render(from_element=None)

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
        def MyComponent() -> Elements:
            render_count[0] += 1
            _ = state.text
            return None

        ctx = RenderContext(MyComponent)
        ctx.render(from_element=None)
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
        def NameComponent() -> Elements:
            name_renders[0] += 1
            _ = state.name
            return None

        @component
        def CountComponent() -> Elements:
            count_renders[0] += 1
            _ = state.count
            return None

        @component
        def Parent() -> Elements:
            NameComponent()
            CountComponent()
            return None

        ctx = RenderContext(Parent)
        ctx.render(from_element=None)

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
