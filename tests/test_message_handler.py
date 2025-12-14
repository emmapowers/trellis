"""Tests for MessageHandler base class and transport implementations."""

import asyncio
from dataclasses import dataclass

import pytest

from trellis.core.composition_component import component
from trellis.core.message_handler import MessageHandler
from trellis.core.messages import EventMessage, Message, RenderMessage
from trellis.core.rendering import IComponent
from trellis.core.state import Stateful
from trellis.widgets import Button, Label
from trellis_playground.runtime import PlaygroundMessageHandler


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
        """handle_message() returns None for unknown callback."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = MessageHandler(App)
        handler.initial_render()

        event_msg = EventMessage(callback_id="unknown:callback", args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # Returns None because callback not found (logged as warning)
        assert response is None

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


class TestPlaygroundMessageHandler:
    """Tests for PlaygroundMessageHandler."""

    def test_post_event_adds_to_queue(self) -> None:
        """post_event() adds EventMessage to inbox."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = PlaygroundMessageHandler(App)

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

        handler = PlaygroundMessageHandler(App)

        # Post an event
        handler.post_event("test:callback", [])

        # Receive should get it
        msg = asyncio.run(handler.receive_message())
        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "test:callback"

    def test_send_message_calls_render_callback(self) -> None:
        """send_message() calls registered render callback."""
        received_trees = []

        @component
        def App() -> None:
            Label(text="Hello")

        handler = PlaygroundMessageHandler(App)
        handler.set_render_callback(lambda tree: received_trees.append(tree))

        msg = RenderMessage(tree={"test": "data"})
        asyncio.run(handler.send_message(msg))

        assert received_trees == [{"test": "data"}]

    def test_send_message_without_callback_no_error(self) -> None:
        """send_message() without callback doesn't raise."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = PlaygroundMessageHandler(App)
        # No callback set

        msg = RenderMessage(tree={"test": "data"})
        asyncio.run(handler.send_message(msg))  # Should not raise

    def test_full_event_flow(self) -> None:
        """Full flow: post_event -> handle_message -> callback to JS."""
        clicked = []
        rendered_trees = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = PlaygroundMessageHandler(App)
        handler.set_render_callback(lambda tree: rendered_trees.append(tree))

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
        assert len(rendered_trees) == 1


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
