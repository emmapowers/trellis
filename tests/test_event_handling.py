"""Tests for event handling and callback invocation."""

import inspect
from dataclasses import dataclass

from trellis.core.composition_component import component
from trellis.core.rendering import RenderSession, render
from trellis.core.serialization import serialize_node
from trellis.core.state import Stateful
from trellis.html.events import (
    BaseEvent,
    ChangeEvent,
    KeyboardEvent,
    MouseEvent,
)
from trellis.core.message_handler import (
    _convert_event_arg,
    _extract_args_kwargs,
    _process_callback_args,
)
from trellis.widgets import Button, Label


class TestCallbackInvocation:
    """Tests for callback lookup and invocation."""

    def test_callback_invoked_by_id(self) -> None:
        """Callback can be looked up by ID and invoked."""
        invocations: list[str] = []

        def on_click() -> None:
            invocations.append("clicked")

        @component
        def App() -> None:
            Button(text="Click", on_click=on_click)

        ctx = RenderSession(App)
        render(ctx)

        # Get callback ID from serialized tree
        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Simulate event handling
        callback = ctx.get_callback(cb_id)
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

        ctx = RenderSession(App)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        callback = ctx.get_callback(cb_id)
        assert callback is not None
        callback("arg1", 42, True)

        assert received_args == [("arg1", 42, True)]

    def test_unknown_callback_returns_none(self) -> None:
        """get_callback returns None for unknown IDs."""
        ctx = RenderSession(lambda: None)
        result = ctx.get_callback("nonexistent_cb_999")
        assert result is None


class TestStateUpdateOnEvent:
    """Tests for state updates triggered by events."""

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

        ctx = RenderSession(Counter)
        render(ctx)

        # Get initial state
        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
        label = tree["children"][0]
        assert label["props"]["text"] == "0"

        # Get callback and invoke it
        button = tree["children"][1]
        cb_id = button["props"]["on_click"]["__callback__"]
        callback = ctx.get_callback(cb_id)
        assert callback is not None
        callback()

        # Re-render dirty elements
        ctx.clear_callbacks()
        render(ctx)

        # Verify state updated
        tree = serialize_node(ctx.root_node, ctx)
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

        ctx = RenderSession(Counter)
        render(ctx)

        assert ctx.root_node is not None

        # Increment twice
        for _ in range(2):
            tree = serialize_node(ctx.root_node, ctx)
            inc_button = tree["children"][2]
            cb_id = inc_button["props"]["on_click"]["__callback__"]
            callback = ctx.get_callback(cb_id)
            assert callback is not None
            callback()
            ctx.clear_callbacks()
            render(ctx)

        tree = serialize_node(ctx.root_node, ctx)
        label = tree["children"][1]
        assert label["props"]["text"] == "7"

        # Decrement once
        tree = serialize_node(ctx.root_node, ctx)
        dec_button = tree["children"][0]
        cb_id = dec_button["props"]["on_click"]["__callback__"]
        callback = ctx.get_callback(cb_id)
        assert callback is not None
        callback()
        ctx.clear_callbacks()
        render(ctx)

        tree = serialize_node(ctx.root_node, ctx)
        label = tree["children"][1]
        assert label["props"]["text"] == "6"


class TestDisabledStateOnBoundary:
    """Tests for disabled state based on value boundaries."""

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

        ctx = RenderSession(Counter)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
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

        ctx = RenderSession(Counter)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
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

        ctx = RenderSession(Counter)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
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

        ctx = RenderSession(Counter)
        render(ctx)

        assert ctx.root_node is not None

        # Initially enabled at count=2
        tree = serialize_node(ctx.root_node, ctx)
        dec_button = tree["children"][0]
        assert dec_button["props"]["disabled"] is False

        # Decrement to 1
        cb_id = dec_button["props"]["on_click"]["__callback__"]
        callback = ctx.get_callback(cb_id)
        assert callback is not None
        callback()
        ctx.clear_callbacks()
        render(ctx)

        # Now should be disabled at count=1
        tree = serialize_node(ctx.root_node, ctx)
        dec_button = tree["children"][0]
        assert dec_button["props"]["disabled"] is True
        label = tree["children"][1]
        assert label["props"]["text"] == "1"


class TestArgsKwargsExtraction:
    """Tests for _extract_args_kwargs helper."""

    def test_empty_args(self) -> None:
        """Empty args returns empty lists."""
        args, kwargs = _extract_args_kwargs([])
        assert args == []
        assert kwargs == {}

    def test_positional_only(self) -> None:
        """Regular args pass through without modification."""
        args, kwargs = _extract_args_kwargs(["a", 1, True])
        assert args == ["a", 1, True]
        assert kwargs == {}

    def test_kwargs_marker_extracts_kwargs(self) -> None:
        """Dict with __kwargs__: True is unpacked as kwargs."""
        args, kwargs = _extract_args_kwargs(
            ["arg1", {"__kwargs__": True, "key": "value", "num": 42}]
        )
        assert args == ["arg1"]
        assert kwargs == {"key": "value", "num": 42}

    def test_kwargs_only(self) -> None:
        """Kwargs-only invocation works."""
        args, kwargs = _extract_args_kwargs(
            [{"__kwargs__": True, "name": "test"}]
        )
        assert args == []
        assert kwargs == {"name": "test"}

    def test_dict_without_marker_not_kwargs(self) -> None:
        """Regular dict without __kwargs__ is not treated as kwargs."""
        args, kwargs = _extract_args_kwargs([{"key": "value"}])
        assert args == [{"key": "value"}]
        assert kwargs == {}

    def test_kwargs_marker_false_not_kwargs(self) -> None:
        """Dict with __kwargs__: False is not treated as kwargs."""
        args, kwargs = _extract_args_kwargs(
            [{"__kwargs__": False, "key": "value"}]
        )
        assert args == [{"__kwargs__": False, "key": "value"}]
        assert kwargs == {}


class TestEventConversion:
    """Tests for _convert_event_arg helper."""

    def test_mouse_event_converted(self) -> None:
        """Mouse event dict becomes MouseEvent dataclass."""
        event_dict = {
            "type": "click",
            "timestamp": 1234.5,
            "clientX": 100,
            "clientY": 200,
            "button": 0,
            "altKey": True,
        }
        result = _convert_event_arg(event_dict)
        assert isinstance(result, MouseEvent)
        assert result.type == "click"
        assert result.timestamp == 1234.5
        assert result.clientX == 100
        assert result.clientY == 200
        assert result.button == 0
        assert result.altKey is True

    def test_keyboard_event_converted(self) -> None:
        """Keyboard event dict becomes KeyboardEvent dataclass."""
        event_dict = {
            "type": "keydown",
            "timestamp": 5678.9,
            "key": "Enter",
            "code": "Enter",
            "ctrlKey": True,
        }
        result = _convert_event_arg(event_dict)
        assert isinstance(result, KeyboardEvent)
        assert result.type == "keydown"
        assert result.key == "Enter"
        assert result.code == "Enter"
        assert result.ctrlKey is True

    def test_change_event_converted(self) -> None:
        """Change event dict becomes ChangeEvent dataclass."""
        event_dict = {
            "type": "change",
            "timestamp": 9999.0,
            "value": "hello",
            "checked": False,
        }
        result = _convert_event_arg(event_dict)
        assert isinstance(result, ChangeEvent)
        assert result.type == "change"
        assert result.value == "hello"
        assert result.checked is False

    def test_unknown_event_type_fallback(self) -> None:
        """Unknown event type falls back to BaseEvent."""
        event_dict = {
            "type": "custom-event",
            "timestamp": 1000.0,
        }
        result = _convert_event_arg(event_dict)
        assert isinstance(result, BaseEvent)
        assert result.type == "custom-event"

    def test_non_event_dict_unchanged(self) -> None:
        """Dict without 'type' passes through unchanged."""
        data = {"key": "value", "number": 42}
        result = _convert_event_arg(data)
        assert result == data

    def test_non_dict_unchanged(self) -> None:
        """Non-dict values pass through unchanged."""
        assert _convert_event_arg("string") == "string"
        assert _convert_event_arg(42) == 42
        assert _convert_event_arg(None) is None
        assert _convert_event_arg([1, 2, 3]) == [1, 2, 3]

    def test_extra_fields_filtered(self) -> None:
        """Extra fields not in dataclass are filtered out."""
        event_dict = {
            "type": "click",
            "clientX": 100,
            "unknownField": "ignored",
            "anotherExtra": 999,
        }
        result = _convert_event_arg(event_dict)
        assert isinstance(result, MouseEvent)
        assert result.clientX == 100
        # Extra fields should not cause error or be present
        assert not hasattr(result, "unknownField")


class TestProcessCallbackArgs:
    """Tests for _process_callback_args helper."""

    def test_event_conversion_and_kwargs(self) -> None:
        """Events are converted and kwargs extracted in one call."""
        raw_args = [
            {"type": "click", "clientX": 50},
            {"__kwargs__": True, "extra": "data"},
        ]
        args, kwargs = _process_callback_args(raw_args)

        assert len(args) == 1
        assert isinstance(args[0], MouseEvent)
        assert args[0].clientX == 50
        assert kwargs == {"extra": "data"}

    def test_multiple_events_converted(self) -> None:
        """Multiple event args are all converted."""
        raw_args = [
            {"type": "click", "clientX": 10},
            {"type": "keydown", "key": "a"},
        ]
        args, kwargs = _process_callback_args(raw_args)

        assert len(args) == 2
        assert isinstance(args[0], MouseEvent)
        assert isinstance(args[1], KeyboardEvent)
        assert kwargs == {}

    def test_mixed_args(self) -> None:
        """Mix of events, regular args, and kwargs works."""
        raw_args = [
            "string",
            42,
            {"type": "change", "value": "test"},
            {"__kwargs__": True, "opt": True},
        ]
        args, kwargs = _process_callback_args(raw_args)

        assert args[0] == "string"
        assert args[1] == 42
        assert isinstance(args[2], ChangeEvent)
        assert args[2].value == "test"
        assert kwargs == {"opt": True}


class TestAsyncCallbackDetection:
    """Tests for async callback detection."""

    def test_sync_callback_detected(self) -> None:
        """Sync callbacks are correctly identified."""

        def sync_callback() -> None:
            pass

        assert not inspect.iscoroutinefunction(sync_callback)

    def test_async_callback_detected(self) -> None:
        """Async callbacks are correctly identified."""

        async def async_callback() -> None:
            pass

        assert inspect.iscoroutinefunction(async_callback)

    def test_async_callback_with_args(self) -> None:
        """Async callback with args is correctly identified."""

        async def async_with_args(event: ChangeEvent, *, option: bool = False) -> None:
            pass

        assert inspect.iscoroutinefunction(async_with_args)


class TestAsyncCallbackExecution:
    """Tests for async callback execution."""

    def test_async_callback_invocation(self) -> None:
        """Async callback can be invoked and returns awaitable."""
        import asyncio

        result_holder: list[str] = []

        async def async_handler() -> None:
            await asyncio.sleep(0)  # Simulate async work
            result_holder.append("done")

        @component
        def App() -> None:
            Button(text="Async", on_click=async_handler)

        ctx = RenderSession(App)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        callback = ctx.get_callback(cb_id)
        assert callback is not None
        assert inspect.iscoroutinefunction(callback)

        # Execute async callback
        asyncio.run(callback())
        assert result_holder == ["done"]


class TestCallbackErrorHandling:
    """Tests for callback error handling."""

    def test_sync_callback_exception_propagates(self) -> None:
        """Sync callback exceptions propagate normally."""

        def failing_callback() -> None:
            raise ValueError("Test error")

        @component
        def App() -> None:
            Button(text="Fail", on_click=failing_callback)

        ctx = RenderSession(App)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        callback = ctx.get_callback(cb_id)
        assert callback is not None

        try:
            callback()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e) == "Test error"

    def test_multiple_callbacks_independent(self) -> None:
        """Multiple callbacks don't affect each other."""
        results: list[str] = []

        def callback_a() -> None:
            results.append("a")

        def callback_b() -> None:
            results.append("b")

        @component
        def App() -> None:
            Button(text="A", on_click=callback_a)
            Button(text="B", on_click=callback_b)

        ctx = RenderSession(App)
        render(ctx)

        assert ctx.root_node is not None
        tree = serialize_node(ctx.root_node, ctx)
        btn_a = tree["children"][0]
        btn_b = tree["children"][1]
        cb_id_a = btn_a["props"]["on_click"]["__callback__"]
        cb_id_b = btn_b["props"]["on_click"]["__callback__"]

        ctx.get_callback(cb_id_a)()
        ctx.get_callback(cb_id_b)()
        ctx.get_callback(cb_id_a)()

        assert results == ["a", "b", "a"]
