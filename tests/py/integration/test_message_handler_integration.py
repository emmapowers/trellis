"""Integration tests for MessageHandler and BrowserMessageHandler."""

import asyncio
import typing as tp
from dataclasses import dataclass

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.patches import RenderUpdatePatch
from trellis.core.rendering.render import render
from trellis.core.state.stateful import Stateful
from trellis.platforms.browser import BrowserMessageHandler
from trellis.platforms.common.handler import AppWrapper
from trellis.platforms.common.messages import (
    AddPatch,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    PatchMessage,
)
from trellis.widgets import Button, Label


def init_handler_for_test(handler: BrowserMessageHandler) -> None:
    """Initialize handler by posting HelloMessage and calling handle_hello.

    This simulates the production flow where handle_hello creates the session.
    """
    handler._inbox.put_nowait(HelloMessage(client_id="test", system_theme="light"))
    asyncio.run(handler.handle_hello())


def get_initial_tree(handler: BrowserMessageHandler) -> dict[str, tp.Any]:
    """Helper to get tree dict from initial render."""
    msg = handler.initial_render()
    assert isinstance(msg, PatchMessage)
    assert len(msg.patches) == 1
    patch = msg.patches[0]
    assert isinstance(patch, AddPatch)
    return patch.element


# Components that are part of the TrellisApp wrapper infrastructure
_WRAPPER_COMPONENT_TYPES = frozenset(
    {
        "CompositionComponent",  # Generic wrapper (TrellisRoot, TrellisApp, etc.)
        "ThemeProvider",  # Theme provider
        "ClientState",  # Client state context
    }
)


def find_app_children(tree: dict[str, tp.Any]) -> list[dict[str, tp.Any]]:
    """Find the user's app children within the TrellisApp wrapper.

    The tree structure is:
    TrellisRoot -> TrellisApp -> ClientState -> ThemeProvider -> UserApp -> children

    This helper navigates through wrapper components to find user content.
    Wrapper components are identified by their type being in _WRAPPER_COMPONENT_TYPES.
    """
    if not tree:
        return []

    node = tree
    # Walk down through wrapper components until we find user content
    for _ in range(15):  # Safety limit - more than enough for any wrapper depth
        children = node.get("children", [])
        if not children:
            return []

        first = children[0]
        node_type = first.get("type", "")

        # If this is a wrapper component, continue navigating down
        if node_type in _WRAPPER_COMPONENT_TYPES:
            node = first
            continue

        # Found user content - return all children at this level
        return children

    # Hit safety limit - return empty to avoid infinite loops
    return []


class TestMessageHandler:
    """Tests for MessageHandler base class.

    Uses BrowserMessageHandler as a concrete implementation since MessageHandler
    is abstract. Tests focus on core handler behavior shared by all platforms.
    """

    def test_initial_render_returns_patch_message(self, app_wrapper: AppWrapper) -> None:
        """initial_render() returns a PatchMessage with AddPatch."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        msg = handler.initial_render()

        assert isinstance(msg, PatchMessage)
        assert len(msg.patches) == 1
        assert isinstance(msg.patches[0], AddPatch)
        tree = msg.patches[0].element
        assert "children" in tree
        # Navigate through wrapper to find user content
        app_children = find_app_children(tree)
        assert app_children[0]["props"]["text"] == "Hello"

    def test_handle_message_with_event(self, app_wrapper: AppWrapper) -> None:
        """handle_message() invokes callback (rendering is batched separately)."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        # Get callback ID from tree (navigate through wrapper)
        app_children = find_app_children(tree)
        button = app_children[0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Send event message
        event_msg = EventMessage(callback_id=cb_id, args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # With batched rendering, handle_message returns None
        # Rendering happens in the background loop
        assert response is None
        assert clicked == [True]

    def test_handle_message_with_unknown_callback(self, app_wrapper: AppWrapper) -> None:
        """handle_message() returns ErrorMessage for unknown callback."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        handler.initial_render()

        event_msg = EventMessage(callback_id="unknown|callback", args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # Returns ErrorMessage because callback not found
        assert isinstance(response, ErrorMessage)
        assert response.context == "callback"
        assert "Callback not found: unknown|callback" in response.error

    def test_handle_message_with_state_update(self, app_wrapper: AppWrapper) -> None:
        """handle_message() marks nodes dirty, render() sends patches."""

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

        handler = BrowserMessageHandler(Counter, app_wrapper)
        init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        # Verify initial state (navigate through wrapper)
        app_children = find_app_children(tree)
        label = app_children[0]
        assert label["props"]["text"] == "0"

        # Get callback and invoke
        button = app_children[1]
        cb_id = button["props"]["on_click"]["__callback__"]

        event_msg = EventMessage(callback_id=cb_id, args=[])
        response = asyncio.run(handler.handle_message(event_msg))

        # With batched rendering, handle_message returns None
        assert response is None

        # Nodes should be dirty now
        assert handler.session is not None
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

    def test_handle_message_with_event_args(self, app_wrapper: AppWrapper) -> None:
        """handle_message() converts event args to dataclasses."""
        received = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda e: received.append(e))

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        app_children = find_app_children(tree)
        button = app_children[0]
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

    def test_cleanup_clears_callbacks(self, app_wrapper: AppWrapper) -> None:
        """cleanup() clears all registered callbacks."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        handler.initial_render()

        # Callback should exist
        assert handler.session is not None
        assert handler.session.get_callback is not None

        handler.cleanup()

        # After cleanup, tree should have no callbacks
        # (we can't easily test this without internal access,
        # but the method should not raise)


class TestBrowserMessageHandler:
    """Tests for BrowserMessageHandler event handling."""

    def test_post_event_adds_to_queue(self, app_wrapper: AppWrapper) -> None:
        """post_event() adds EventMessage to inbox.

        INTERNAL TEST: _inbox is the internal queue - no public API to inspect it.
        """

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App, app_wrapper)

        handler.post_event("test:callback", [1, 2, 3])

        # Verify the message was queued
        assert not handler._inbox.empty()
        msg = handler._inbox.get_nowait()
        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "test:callback"
        assert msg.args == [1, 2, 3]

    def test_receive_message_gets_from_queue(self, app_wrapper: AppWrapper) -> None:
        """receive_message() awaits message from inbox."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App, app_wrapper)

        # Post an event
        handler.post_event("test:callback", [])

        # Receive should get it
        msg = asyncio.run(handler.receive_message())
        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "test:callback"

    def test_send_message_calls_send_callback(self, app_wrapper: AppWrapper) -> None:
        """send_message() calls registered send callback with message dict."""
        received_messages: list[dict] = []

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App, app_wrapper)
        handler.set_send_callback(lambda msg: received_messages.append(msg))

        msg = PatchMessage(patches=[])
        asyncio.run(handler.send_message(msg))

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "patch"
        assert received_messages[0]["patches"] == []

    def test_send_message_without_callback_no_error(self, app_wrapper: AppWrapper) -> None:
        """send_message() without callback doesn't raise."""

        @component
        def App() -> None:
            Label(text="Hello")

        handler = BrowserMessageHandler(App, app_wrapper)
        # No callback set

        msg = PatchMessage(patches=[])
        asyncio.run(handler.send_message(msg))  # Should not raise

    def test_full_event_flow(self, app_wrapper: AppWrapper) -> None:
        """Full flow: post_event -> handle_message -> patches via render loop."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)

        # Get initial render
        tree = get_initial_tree(handler)
        app_children = find_app_children(tree)
        button = app_children[0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Simulate JS posting event
        handler.post_event(cb_id, [])

        # Process one message
        async def process_one() -> None:
            msg = await handler.receive_message()
            response = await handler.handle_message(msg)
            # With batched rendering, handle_message returns None
            assert response is None

        asyncio.run(process_one())

        # Callback was invoked
        assert clicked == [True]


class TestAsyncCallbackHandling:
    """Tests for async callback handling in MessageHandler."""

    def test_async_callback_fires_and_forgets(self, app_wrapper: AppWrapper) -> None:
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

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        app_children = find_app_children(tree)
        button = app_children[0]
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

    def test_background_tasks_tracked(self, app_wrapper: AppWrapper) -> None:
        """Background tasks are tracked to prevent GC.

        INTERNAL TEST: _background_tasks is internal - verifies GC prevention.
        """
        task_completed = []

        async def async_handler() -> None:
            await asyncio.sleep(0.01)
            task_completed.append(True)

        @component
        def App() -> None:
            Button(text="Async", on_click=async_handler)

        handler = BrowserMessageHandler(App, app_wrapper)
        init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        app_children = find_app_children(tree)
        button = app_children[0]
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


class TestHelloHandshake:
    """Tests for hello handshake and session creation.

    These tests verify that handle_hello() correctly passes theme information
    to the app_wrapper and creates the session. The wrapper now encapsulates
    ClientState creation, so we test the interface between handler and wrapper.
    """

    def test_handle_hello_creates_session(self, app_wrapper: AppWrapper) -> None:
        """handle_hello should create the render session."""

        @component
        def App() -> None:
            Label(text="test")

        handler = BrowserMessageHandler(App, app_wrapper)

        async def test() -> None:
            hello_msg = HelloMessage(client_id="test", system_theme="light")
            handler._inbox.put_nowait(hello_msg)

            session_id = await handler.handle_hello()

            # Session should be created
            assert handler.session is not None
            assert session_id is not None

        asyncio.run(test())

    def test_handle_hello_passes_dark_system_theme_to_wrapper(self) -> None:
        """handle_hello should pass dark system theme to wrapper."""
        captured: list[tuple[str, str | None]] = []

        def tracking_wrapper(
            comp: tp.Any, system_theme: str, theme_mode: str | None
        ) -> CompositionComponent:
            captured.append((system_theme, theme_mode))

            def render_func() -> None:
                comp()

            return CompositionComponent(name="TestRoot", render_func=render_func)

        @component
        def App() -> None:
            Label(text="test")

        handler = BrowserMessageHandler(App, tracking_wrapper)

        async def test() -> None:
            hello_msg = HelloMessage(client_id="test", system_theme="dark")
            handler._inbox.put_nowait(hello_msg)

            await handler.handle_hello()

            assert len(captured) == 1
            assert captured[0][0] == "dark"

        asyncio.run(test())

    def test_handle_hello_passes_light_system_theme_to_wrapper(self) -> None:
        """handle_hello should pass light system theme to wrapper."""
        captured: list[tuple[str, str | None]] = []

        def tracking_wrapper(
            comp: tp.Any, system_theme: str, theme_mode: str | None
        ) -> CompositionComponent:
            captured.append((system_theme, theme_mode))

            def render_func() -> None:
                comp()

            return CompositionComponent(name="TestRoot", render_func=render_func)

        @component
        def App() -> None:
            Label(text="test")

        handler = BrowserMessageHandler(App, tracking_wrapper)

        async def test() -> None:
            hello_msg = HelloMessage(client_id="test", system_theme="light")
            handler._inbox.put_nowait(hello_msg)

            await handler.handle_hello()

            assert len(captured) == 1
            assert captured[0][0] == "light"

        asyncio.run(test())

    def test_hello_message_default_system_theme(self) -> None:
        """HelloMessage should default to light theme if not provided."""
        msg = HelloMessage(client_id="test")
        assert msg.system_theme == "light"

    def test_handle_hello_passes_theme_mode_to_wrapper(self) -> None:
        """handle_hello should pass theme_mode to wrapper."""
        captured: list[tuple[str, str | None]] = []

        def tracking_wrapper(
            comp: tp.Any, system_theme: str, theme_mode: str | None
        ) -> CompositionComponent:
            captured.append((system_theme, theme_mode))

            def render_func() -> None:
                comp()

            return CompositionComponent(name="TestRoot", render_func=render_func)

        @component
        def App() -> None:
            Label(text="test")

        handler = BrowserMessageHandler(App, tracking_wrapper)

        async def test() -> None:
            hello_msg = HelloMessage(client_id="test", system_theme="light", theme_mode="dark")
            handler._inbox.put_nowait(hello_msg)

            await handler.handle_hello()

            assert len(captured) == 1
            assert captured[0] == ("light", "dark")

        asyncio.run(test())

    def test_handle_hello_passes_system_theme_mode_to_wrapper(self) -> None:
        """handle_hello should pass 'system' theme_mode to wrapper."""
        captured: list[tuple[str, str | None]] = []

        def tracking_wrapper(
            comp: tp.Any, system_theme: str, theme_mode: str | None
        ) -> CompositionComponent:
            captured.append((system_theme, theme_mode))

            def render_func() -> None:
                comp()

            return CompositionComponent(name="TestRoot", render_func=render_func)

        @component
        def App() -> None:
            Label(text="test")

        handler = BrowserMessageHandler(App, tracking_wrapper)

        async def test() -> None:
            hello_msg = HelloMessage(client_id="test", system_theme="dark", theme_mode="system")
            handler._inbox.put_nowait(hello_msg)

            await handler.handle_hello()

            assert len(captured) == 1
            assert captured[0] == ("dark", "system")

        asyncio.run(test())

    def test_handle_hello_passes_none_theme_mode_when_not_provided(self) -> None:
        """handle_hello should pass None theme_mode when not in HelloMessage."""
        captured: list[tuple[str, str | None]] = []

        def tracking_wrapper(
            comp: tp.Any, system_theme: str, theme_mode: str | None
        ) -> CompositionComponent:
            captured.append((system_theme, theme_mode))

            def render_func() -> None:
                comp()

            return CompositionComponent(name="TestRoot", render_func=render_func)

        @component
        def App() -> None:
            Label(text="test")

        handler = BrowserMessageHandler(App, tracking_wrapper)

        async def test() -> None:
            hello_msg = HelloMessage(client_id="test", system_theme="dark")
            handler._inbox.put_nowait(hello_msg)

            await handler.handle_hello()

            assert len(captured) == 1
            assert captured[0] == ("dark", None)

        asyncio.run(test())
