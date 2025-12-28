"""Integration tests for MessageHandler and BrowserMessageHandler."""

import asyncio
import typing as tp
from dataclasses import dataclass

from trellis.core.components.composition import component
from trellis.core.rendering.patches import RenderUpdatePatch
from trellis.core.rendering.render import render
from trellis.core.state.stateful import Stateful
from trellis.platforms.browser import BrowserMessageHandler
from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import (
    AddPatch,
    ErrorMessage,
    EventMessage,
    PatchMessage,
)
from trellis.widgets import Button, Label


def get_initial_tree(handler: MessageHandler) -> dict[str, tp.Any]:
    """
    Extract the root node dictionary produced by a handler's initial render.
    
    Returns:
        The `node` dictionary from the single `AddPatch` contained in the `PatchMessage` returned by `handler.initial_render()`.
    
    Raises:
        AssertionError: If the initial render does not return a `PatchMessage` with exactly one patch, or if that patch is not an `AddPatch`.
    """
    msg = handler.initial_render()
    assert isinstance(msg, PatchMessage)
    assert len(msg.patches) == 1
    patch = msg.patches[0]
    assert isinstance(patch, AddPatch)
    return patch.node


class TestMessageHandler:
    """Tests for MessageHandler base class."""

    def test_initial_render_returns_patch_message(self) -> None:
        """initial_render() returns a PatchMessage with AddPatch."""

        @component
        def App() -> None:
            """
            Simple example component that renders a Label with the text "Hello".
            
            Used by tests to produce an initial render tree containing a single Label node whose props.text is "Hello".
            """
            Label(text="Hello")

        handler = MessageHandler(App)
        msg = handler.initial_render()

        assert isinstance(msg, PatchMessage)
        assert len(msg.patches) == 1
        assert isinstance(msg.patches[0], AddPatch)
        tree = msg.patches[0].node
        assert "children" in tree
        assert tree["children"][0]["props"]["text"] == "Hello"

    def test_handle_message_with_event(self) -> None:
        """handle_message() invokes callback (rendering is batched separately)."""
        clicked = []

        @component
        def App() -> None:
            """
            Create a simple UI component containing a single Button labeled "Click" whose on_click handler appends True to the outer `clicked` list.
            """
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = MessageHandler(App)
        tree = get_initial_tree(handler)

        # Get callback ID from tree
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Send event message
        event_msg = EventMessage(callback_id=cb_id, args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # With batched rendering, handle_message returns None
        # Rendering happens in the background loop
        assert response is None
        assert clicked == [True]

    def test_handle_message_with_unknown_callback(self) -> None:
        """
        Verify that handling an EventMessage with an unknown callback ID produces an ErrorMessage.
        
        Asserts the response is an ErrorMessage with context "callback" and an error message containing the missing callback ID.
        """

        @component
        def App() -> None:
            """
            Simple example component that renders a Label with the text "Hello".
            
            Used by tests to produce an initial render tree containing a single Label node whose props.text is "Hello".
            """
            Label(text="Hello")

        handler = MessageHandler(App)
        handler.initial_render()

        event_msg = EventMessage(callback_id="unknown|callback", args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # Returns ErrorMessage because callback not found
        assert isinstance(response, ErrorMessage)
        assert response.context == "callback"
        assert "Callback not found: unknown|callback" in response.error

    def test_handle_message_with_state_update(self) -> None:
        """handle_message() marks nodes dirty, render() sends patches."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @component
        def Counter() -> None:
            """
            A stateful counter component that displays the current count and provides a button to increment it.
            
            Renders a Label showing the counter's current value and a Button labeled "+" that, when clicked, increments the component's internal `count` state.
            """
            state = CounterState()

            def increment() -> None:
                """
                Increment the current state's count by one.
                """
                state.count += 1

            Label(text=str(state.count))
            Button(text="+", on_click=increment)

        handler = MessageHandler(Counter)
        tree = get_initial_tree(handler)

        # Verify initial state
        label = tree["children"][0]
        assert label["props"]["text"] == "0"

        # Get callback and invoke
        button = tree["children"][1]
        cb_id = button["props"]["on_click"]["__callback__"]

        event_msg = EventMessage(callback_id=cb_id, args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # With batched rendering, handle_message returns None
        assert response is None

        # Nodes should be dirty now
        assert handler.session.dirty.has_dirty()

        # Render should produce patches
        patches = render(handler.session)
        assert len(patches) > 0

        # Find the update patch for the label - render() returns RenderUpdatePatch
        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        assert len(update_patches) > 0
        # Check that a props update was emitted with the new text value
        props_patches = [p for p in update_patches if p.props and p.props.get("text") == "1"]
        assert len(props_patches) > 0

    def test_handle_message_with_event_args(self) -> None:
        """handle_message() converts event args to dataclasses."""
        received = []

        @component
        def App() -> None:
            """
            Define a minimal application with a Button that records click events.
            
            The Button's on_click handler appends the received event object to the surrounding `received` list.
            """
            Button(text="Click", on_click=lambda e: received.append(e))

        handler = MessageHandler(App)
        tree = get_initial_tree(handler)

        button = tree["children"][0]
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
            """
            Declare a minimal application that renders a single Button labeled "Click" with a no-op click handler.
            
            The component has no parameters and does not return a value; it defines UI structure by creating a Button with its `text` set to "Click" and `on_click` set to a function that does nothing.
            """
            Button(text="Click", on_click=lambda: None)

        handler = MessageHandler(App)
        handler.initial_render()

        # Callback should exist
        assert handler.session.get_callback is not None

        handler.cleanup()

        # After cleanup, tree should have no callbacks
        # (we can't easily test this without internal access,
        # but the method should not raise)


class TestBrowserMessageHandler:
    """Tests for BrowserMessageHandler event handling."""

    def test_post_event_adds_to_queue(self) -> None:
        """post_event() adds EventMessage to inbox.

        INTERNAL TEST: _inbox is the internal queue - no public API to inspect it.
        """

        @component
        def App() -> None:
            """
            Simple example component that renders a Label with the text "Hello".
            
            Used by tests to produce an initial render tree containing a single Label node whose props.text is "Hello".
            """
            Label(text="Hello")

        handler = BrowserMessageHandler(App)

        handler.post_event("test:callback", [1, 2, 3])

        # Verify the message was queued
        assert not handler._inbox.empty()
        msg = handler._inbox.get_nowait()
        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "test:callback"
        assert msg.args == [1, 2, 3]

    def test_receive_message_gets_from_queue(self) -> None:
        """receive_message() awaits message from inbox."""

        @component
        def App() -> None:
            """
            Simple example component that renders a Label with the text "Hello".
            
            Used by tests to produce an initial render tree containing a single Label node whose props.text is "Hello".
            """
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
            """
            Simple example component that renders a Label with the text "Hello".
            
            Used by tests to produce an initial render tree containing a single Label node whose props.text is "Hello".
            """
            Label(text="Hello")

        handler = BrowserMessageHandler(App)
        handler.set_send_callback(lambda msg: received_messages.append(msg))

        msg = PatchMessage(patches=[])
        asyncio.run(handler.send_message(msg))

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "patch"
        assert received_messages[0]["patches"] == []

    def test_send_message_without_callback_no_error(self) -> None:
        """send_message() without callback doesn't raise."""

        @component
        def App() -> None:
            """
            Simple example component that renders a Label with the text "Hello".
            
            Used by tests to produce an initial render tree containing a single Label node whose props.text is "Hello".
            """
            Label(text="Hello")

        handler = BrowserMessageHandler(App)
        # No callback set

        msg = PatchMessage(patches=[])
        asyncio.run(handler.send_message(msg))  # Should not raise

    def test_full_event_flow(self) -> None:
        """Full flow: post_event -> handle_message -> patches via render loop."""
        clicked = []

        @component
        def App() -> None:
            """
            Create a simple UI component containing a single Button labeled "Click" whose on_click handler appends True to the outer `clicked` list.
            """
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = BrowserMessageHandler(App)

        # Get initial render
        tree = get_initial_tree(handler)
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Simulate JS posting event
        handler.post_event(cb_id, [])

        # Process one message
        async def process_one() -> None:
            """
            Process a single incoming message by receiving it from the handler and forwarding it for handling.
            
            Awaits a message from handler.receive_message(), passes it to handler.handle_message(), and asserts that the handler returns None (expected when rendering is batched). Raises AssertionError if the handler returns a non-None response.
            """
            msg = await handler.receive_message()
            response = await handler.handle_message(msg)
            # With batched rendering, handle_message returns None
            assert response is None

        asyncio.run(process_one())

        # Callback was invoked
        assert clicked == [True]


class TestAsyncCallbackHandling:
    """Tests for async callback handling in MessageHandler."""

    def test_async_callback_fires_and_forgets(self) -> None:
        """Async callbacks are scheduled without blocking."""
        started = []
        completed = []

        async def async_handler() -> None:
            """
            Asynchronous test callback that records its start and completion in surrounding lists.
            
            Appends True to the outer `started` list, awaits a short delay (~0.01s), then appends True to the outer `completed` list.
            """
            started.append(True)
            await asyncio.sleep(0.01)
            completed.append(True)

        @component
        def App() -> None:
            """
            Render a simple app containing a single Button labeled "Async" that invokes `async_handler` when clicked.
            
            Used in tests to verify asynchronous callback scheduling and background task tracking.
            """
            Button(text="Async", on_click=async_handler)

        handler = MessageHandler(App)
        tree = get_initial_tree(handler)

        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        async def test() -> None:
            event_msg = EventMessage(callback_id=cb_id, args=[])
            response = await handler.handle_message(event_msg)

            # With batched rendering, handle_message returns None immediately
            assert response is None

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
        """Background tasks are tracked to prevent GC.

        INTERNAL TEST: _background_tasks is internal - verifies GC prevention.
        """
        task_completed = []

        async def async_handler() -> None:
            """
            Waits briefly then records completion by appending True to the enclosing `task_completed` list.
            
            This coroutine sleeps for approximately 0.01 seconds and then appends `True` to the `task_completed` list captured from the surrounding scope.
            """
            await asyncio.sleep(0.01)
            task_completed.append(True)

        @component
        def App() -> None:
            """
            Render a simple app containing a single Button labeled "Async" that invokes `async_handler` when clicked.
            
            Used in tests to verify asynchronous callback scheduling and background task tracking.
            """
            Button(text="Async", on_click=async_handler)

        handler = MessageHandler(App)
        tree = get_initial_tree(handler)

        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        async def test() -> None:
            event_msg = EventMessage(callback_id=cb_id, args=[])
            await handler.handle_message(event_msg)

            # Verify task tracking
            assert len(handler._background_tasks) == 1

            # Wait for completion
            await asyncio.sleep(0.02)

            # Task should be removed after completion
            assert len(handler._background_tasks) == 0
            assert task_completed == [True]

        asyncio.run(test())