"""Tests for event handling and callback invocation."""

from dataclasses import dataclass

from trellis.core.functional_component import component
from trellis.core.rendering import RenderContext
from trellis.core.serialization import (
    clear_callbacks,
    get_callback,
    serialize_element,
)
from trellis.core.state import Stateful
from trellis.widgets import Button, Column, Label


class TestCallbackInvocation:
    """Tests for callback lookup and invocation."""

    def setup_method(self) -> None:
        """Clear callback registry between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up callbacks after tests."""
        clear_callbacks()

    def test_callback_invoked_by_id(self) -> None:
        """Callback can be looked up by ID and invoked."""
        invocations: list[str] = []

        def on_click() -> None:
            invocations.append("clicked")

        @component
        def App() -> None:
            Button(text="Click", on_click=on_click)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        # Get callback ID from serialized tree
        assert ctx.root_element is not None
        tree = serialize_element(ctx.root_element)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Simulate event handling
        callback = get_callback(cb_id)
        assert callback is not None
        callback()

        assert invocations == ["clicked"]

    def test_callback_with_args(self) -> None:
        """Callback can receive arguments from event."""
        received_args: list[tuple] = []

        def on_change(*args: object) -> None:
            received_args.append(args)

        @component
        def App() -> None:
            Button(text="Test", on_click=on_change)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        tree = serialize_element(ctx.root_element)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        callback = get_callback(cb_id)
        assert callback is not None
        callback("arg1", 42, True)

        assert received_args == [("arg1", 42, True)]

    def test_unknown_callback_returns_none(self) -> None:
        """get_callback returns None for unknown IDs."""
        result = get_callback("nonexistent_cb_999")
        assert result is None


class TestStateUpdateOnEvent:
    """Tests for state updates triggered by events."""

    def setup_method(self) -> None:
        """Clear callback registry between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up callbacks after tests."""
        clear_callbacks()

    def test_callback_updates_state(self) -> None:
        """Callback can modify Stateful and trigger re-render."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @component
        def Counter() -> None:
            state = CounterState()

            def increment() -> None:
                state.count += 1

            Label(text=str(state.count))
            Button(text="+", on_click=increment)

        ctx = RenderContext(Counter)
        ctx.render(from_element=None)

        # Get initial state
        assert ctx.root_element is not None
        tree = serialize_element(ctx.root_element)
        label = tree["children"][0]
        assert label["props"]["text"] == "0"

        # Get callback and invoke it
        button = tree["children"][1]
        cb_id = button["props"]["on_click"]["__callback__"]
        callback = get_callback(cb_id)
        assert callback is not None
        callback()

        # Re-render dirty elements
        clear_callbacks()
        ctx.render_dirty()

        # Verify state updated
        tree = serialize_element(ctx.root_element)
        label = tree["children"][0]
        assert label["props"]["text"] == "1"

    def test_multiple_state_updates(self) -> None:
        """Multiple callbacks can update state sequentially."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 5

        @component
        def Counter() -> None:
            state = CounterState()

            def increment() -> None:
                state.count += 1

            def decrement() -> None:
                state.count -= 1

            Button(text="-", on_click=decrement)
            Label(text=str(state.count))
            Button(text="+", on_click=increment)

        ctx = RenderContext(Counter)
        ctx.render(from_element=None)

        assert ctx.root_element is not None

        # Increment twice
        for _ in range(2):
            tree = serialize_element(ctx.root_element)
            inc_button = tree["children"][2]
            cb_id = inc_button["props"]["on_click"]["__callback__"]
            callback = get_callback(cb_id)
            assert callback is not None
            callback()
            clear_callbacks()
            ctx.render_dirty()

        tree = serialize_element(ctx.root_element)
        label = tree["children"][1]
        assert label["props"]["text"] == "7"

        # Decrement once
        tree = serialize_element(ctx.root_element)
        dec_button = tree["children"][0]
        cb_id = dec_button["props"]["on_click"]["__callback__"]
        callback = get_callback(cb_id)
        assert callback is not None
        callback()
        clear_callbacks()
        ctx.render_dirty()

        tree = serialize_element(ctx.root_element)
        label = tree["children"][1]
        assert label["props"]["text"] == "6"


class TestDisabledStateOnBoundary:
    """Tests for disabled state based on value boundaries."""

    def setup_method(self) -> None:
        """Clear callback registry between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up callbacks after tests."""
        clear_callbacks()

    def test_button_disabled_at_min(self) -> None:
        """Decrement button disabled when at minimum value."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 1

        @component
        def Counter() -> None:
            state = CounterState()

            def decrement() -> None:
                state.count = max(1, state.count - 1)

            Button(text="-", on_click=decrement, disabled=state.count <= 1)
            Label(text=str(state.count))

        ctx = RenderContext(Counter)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        tree = serialize_element(ctx.root_element)
        dec_button = tree["children"][0]

        # Button should be disabled at count=1
        assert dec_button["props"]["disabled"] is True

    def test_button_disabled_at_max(self) -> None:
        """Increment button disabled when at maximum value."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 10

        @component
        def Counter() -> None:
            state = CounterState()

            def increment() -> None:
                state.count = min(10, state.count + 1)

            Label(text=str(state.count))
            Button(text="+", on_click=increment, disabled=state.count >= 10)

        ctx = RenderContext(Counter)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        tree = serialize_element(ctx.root_element)
        inc_button = tree["children"][1]

        # Button should be disabled at count=10
        assert inc_button["props"]["disabled"] is True

    def test_button_enabled_in_range(self) -> None:
        """Buttons enabled when value is within range."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 5

        @component
        def Counter() -> None:
            state = CounterState()

            def increment() -> None:
                state.count = min(10, state.count + 1)

            def decrement() -> None:
                state.count = max(1, state.count - 1)

            Button(text="-", on_click=decrement, disabled=state.count <= 1)
            Label(text=str(state.count))
            Button(text="+", on_click=increment, disabled=state.count >= 10)

        ctx = RenderContext(Counter)
        ctx.render(from_element=None)

        assert ctx.root_element is not None
        tree = serialize_element(ctx.root_element)
        dec_button = tree["children"][0]
        inc_button = tree["children"][2]

        # Both buttons should be enabled at count=5
        assert dec_button["props"]["disabled"] is False
        assert inc_button["props"]["disabled"] is False

    def test_disabled_state_updates_on_boundary(self) -> None:
        """Button disabled state updates when hitting boundary."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 2

        @component
        def Counter() -> None:
            state = CounterState()

            def decrement() -> None:
                state.count = max(1, state.count - 1)

            Button(text="-", on_click=decrement, disabled=state.count <= 1)
            Label(text=str(state.count))

        ctx = RenderContext(Counter)
        ctx.render(from_element=None)

        assert ctx.root_element is not None

        # Initially enabled at count=2
        tree = serialize_element(ctx.root_element)
        dec_button = tree["children"][0]
        assert dec_button["props"]["disabled"] is False

        # Decrement to 1
        cb_id = dec_button["props"]["on_click"]["__callback__"]
        callback = get_callback(cb_id)
        assert callback is not None
        callback()
        clear_callbacks()
        ctx.render_dirty()

        # Now should be disabled at count=1
        tree = serialize_element(ctx.root_element)
        dec_button = tree["children"][0]
        assert dec_button["props"]["disabled"] is True
        label = tree["children"][1]
        assert label["props"]["text"] == "1"
