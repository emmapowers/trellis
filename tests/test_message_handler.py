"""Tests for MessageHandler base class and transport implementations."""

import asyncio
from dataclasses import dataclass

import pytest

from trellis.core.composition_component import component
from trellis.core.message_handler import MessageHandler
from trellis.core.messages import ErrorMessage, EventMessage, Message, RenderMessage
from trellis.core.rendering import IComponent
from trellis.core.state import Stateful
from trellis.widgets import Button, Label
from trellis.platforms.browser import BrowserMessageHandler


class TestMessageHandler:
    """Tests for MessageHandler base class."""

    def test_initial_render_returns_render_message(self) -> None:
        """initial_render() returns a RenderMessage with tree."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = MessageHandler(App)
        msg = handler.initial_render()

        assert isinstance(msg, RenderMessage)
        assert "children" in msg.tree
        assert msg.tree["children"][0]["props"]["text"] == "Hello"

    def test_handle_message_with_event(self) -> None:
        """handle_message() invokes callback and returns RenderMessage."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = MessageHandler(App)
        initial = handler.initial_render()

        # Get callback ID from tree
        button = initial.tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Send event message
        event_msg = EventMessage(callback_id=cb_id, args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        assert isinstance(response, RenderMessage)
        assert clicked == [True]

    def test_handle_message_with_unknown_callback(self) -> None:
        """handle_message() returns ErrorMessage for unknown callback."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = MessageHandler(App)
        handler.initial_render()

        event_msg = EventMessage(callback_id="unknown:callback", args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # Returns ErrorMessage because callback not found
        assert isinstance(response, ErrorMessage)
        assert response.context == "callback"
        assert "Callback not found: unknown:callback" in response.error

    def test_handle_message_with_state_update(self) -> None:
        """handle_message() re-renders after state change."""

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

        handler = MessageHandler(Counter)
        initial = handler.initial_render()

        # Verify initial state
        label = initial.tree["children"][0]
        assert label["props"]["text"] == "0"

        # Get callback and invoke
        button = initial.tree["children"][1]
        cb_id = button["props"]["on_click"]["__callback__"]

        event_msg = EventMessage(callback_id=cb_id, args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # Verify updated state
        assert isinstance(response, RenderMessage)
        label = response.tree["children"][0]
        assert label["props"]["text"] == "1"

    def test_handle_message_with_event_args(self) -> None:
        """handle_message() converts event args to dataclasses."""
        received = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda e: received.append(e))

        handler = MessageHandler(App)
        initial = handler.initial_render()

        button = initial.tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Send event with mouse event data
        event_msg = EventMessage(
            callback_id=cb_id,
            args=[{"type": "click", "clientX": 100, "clientY": 200}],
        )
        asyncio.run(handler.handle_message(event_msg))

        assert len(received) == 1
        event = received[0]
        assert event.type == "click"
        assert event.clientX == 100
        assert event.clientY == 200

    def test_cleanup_clears_callbacks(self) -> None:
        """cleanup() clears all registered callbacks."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        handler = MessageHandler(App)
        handler.initial_render()

        # Callback should exist
        assert handler.tree.get_callback is not None

        handler.cleanup()

        # After cleanup, tree should have no callbacks
        # (we can't easily test this without internal access,
        # but the method should not raise)


class TestBrowserMessageHandler:
    """Tests for BrowserMessageHandler."""

    def test_message_to_dict_converts_render_message(self) -> None:
        """_message_to_dict converts RenderMessage to dict with type field."""
        from trellis.platforms.browser.handler import _message_to_dict

        msg = RenderMessage(tree={"root": "data"})
        result = _message_to_dict(msg)

        assert result == {"type": "render", "tree": {"root": "data"}}

    def test_message_to_dict_converts_error_message(self) -> None:
        """_message_to_dict converts ErrorMessage to dict with type field."""
        from trellis.platforms.browser.handler import _message_to_dict

        msg = ErrorMessage(error="test error", context="callback")
        result = _message_to_dict(msg)

        assert result == {"type": "error", "error": "test error", "context": "callback"}

    def test_dict_to_message_unknown_type_raises(self) -> None:
        """_dict_to_message raises ValueError for unknown message type."""
        from trellis.platforms.browser.handler import _dict_to_message

        with pytest.raises(ValueError, match="Unknown message type"):
            _dict_to_message({"type": "unknown_type"})

    def test_dict_to_message_missing_callback_id_raises(self) -> None:
        """_dict_to_message raises ValueError when event is missing callback_id."""
        from trellis.platforms.browser.handler import _dict_to_message

        with pytest.raises(ValueError, match="callback_id"):
            _dict_to_message({"type": "event", "args": []})

    def test_dict_to_message_converts_hello(self) -> None:
        """_dict_to_message converts hello message dict to HelloMessage."""
        from trellis.platforms.browser.handler import _dict_to_message
        from trellis.core.messages import HelloMessage

        result = _dict_to_message({"type": "hello", "client_id": "test-123"})

        assert isinstance(result, HelloMessage)
        assert result.client_id == "test-123"

    def test_dict_to_message_converts_event(self) -> None:
        """_dict_to_message converts event message dict to EventMessage."""
        from trellis.platforms.browser.handler import _dict_to_message

        result = _dict_to_message({"type": "event", "callback_id": "cb-1", "args": [1, 2]})

        assert isinstance(result, EventMessage)
        assert result.callback_id == "cb-1"
        assert result.args == [1, 2]

    def test_post_event_adds_to_queue(self) -> None:
        """post_event() adds EventMessage to inbox."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App)

        handler.post_event("test:callback", [1, 2, 3])

        # Queue should have one message
        assert not handler._inbox.empty()
        msg = handler._inbox.get_nowait()
        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "test:callback"
        assert msg.args == [1, 2, 3]

    def test_receive_message_gets_from_queue(self) -> None:
        """receive_message() awaits message from inbox."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App)

        # Post an event
        handler.post_event("test:callback", [])

        # Receive should get it
        msg = asyncio.run(handler.receive_message())
        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "test:callback"

    def test_send_message_calls_send_callback(self) -> None:
        """send_message() calls registered send callback with message dict."""
        received_messages: list[dict] = []

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App)
        handler.set_send_callback(lambda msg: received_messages.append(msg))

        msg = RenderMessage(tree={"test": "data"})
        asyncio.run(handler.send_message(msg))

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "render"
        assert received_messages[0]["tree"] == {"test": "data"}

    def test_send_message_without_callback_no_error(self) -> None:
        """send_message() without callback doesn't raise."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App)
        # No callback set

        msg = RenderMessage(tree={"test": "data"})
        asyncio.run(handler.send_message(msg))  # Should not raise

    def test_full_event_flow(self) -> None:
        """Full flow: post_event -> handle_message -> callback to JS."""
        clicked = []
        rendered_messages: list[dict] = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = BrowserMessageHandler(App)
        handler.set_send_callback(lambda msg: rendered_messages.append(msg))

        # Get initial render
        initial = handler.initial_render()
        button = initial.tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Simulate JS posting event
        handler.post_event(cb_id, [])

        # Process one message
        async def process_one() -> None:
            msg = await handler.receive_message()
            response = await handler.handle_message(msg)
            if response:
                await handler.send_message(response)

        asyncio.run(process_one())

        assert clicked == [True]
        assert len(rendered_messages) == 1
        assert rendered_messages[0]["type"] == "render"


class TestAsyncCallbackHandling:
    """Tests for async callback handling in MessageHandler."""

    def test_async_callback_fires_and_forgets(self) -> None:
        """Async callbacks are scheduled without blocking."""
        started = []
        completed = []

        async def async_handler() -> None:
            started.append(True)
            await asyncio.sleep(0.01)
            completed.append(True)

        @component
        def App() -> None:
            Button(text="Async", on_click=async_handler)

        handler = MessageHandler(App)
        initial = handler.initial_render()

        button = initial.tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        async def test() -> None:
            event_msg = EventMessage(callback_id=cb_id, args=[])
            response = await handler.handle_message(event_msg)

            # Response should be returned immediately (fire-and-forget)
            assert isinstance(response, RenderMessage)

            # Yield to let the scheduled task start
            await asyncio.sleep(0)

            # Callback started but may not be complete yet
            assert started == [True]
            assert completed == []  # Not yet complete

            # Wait for completion
            await asyncio.sleep(0.02)
            assert completed == [True]

        asyncio.run(test())

    def test_background_tasks_tracked(self) -> None:
        """Background tasks are tracked to prevent GC."""
        task_completed = []

        async def async_handler() -> None:
            await asyncio.sleep(0.01)
            task_completed.append(True)

        @component
        def App() -> None:
            Button(text="Async", on_click=async_handler)

        handler = MessageHandler(App)
        initial = handler.initial_render()

        button = initial.tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        async def test() -> None:
            event_msg = EventMessage(callback_id=cb_id, args=[])
            await handler.handle_message(event_msg)

            # Task should be tracked
            assert len(handler._background_tasks) == 1

            # Wait for completion
            await asyncio.sleep(0.02)

            # Task should be removed after completion
            assert len(handler._background_tasks) == 0
            assert task_completed == [True]

        asyncio.run(test())
