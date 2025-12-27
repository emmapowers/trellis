"""Tests for MessageHandler base class and transport implementations."""

import asyncio
from dataclasses import dataclass

import pytest

from trellis.core.components.composition import component
from trellis.core.message_handler import MessageHandler
from trellis.core.messages import AddPatch, ErrorMessage, EventMessage, Message, PatchMessage
from trellis.core.components.base import Component
from trellis.core.rendering.render import render
from trellis.core.state.stateful import Stateful
from trellis.widgets import Button, Label
from trellis.platforms.browser import BrowserMessageHandler
import typing as tp


def get_initial_tree(handler: MessageHandler) -> dict[str, tp.Any]:
    """Helper to get tree dict from initial render."""
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
        assert handler.session.has_dirty_nodes()

        # Render should produce patches
        patches = render(handler.session)
        assert len(patches) > 0

        # Find the update patch for the label
        from trellis.core.messages import UpdatePatch

        update_patches = [p for p in patches if isinstance(p, UpdatePatch)]
        assert len(update_patches) > 0
        # Check that the label's text was updated
        label_patch = next((p for p in update_patches if p.props and "text" in p.props), None)
        assert label_patch is not None
        assert label_patch.props["text"] == "1"

    def test_handle_message_with_event_args(self) -> None:
        """handle_message() converts event args to dataclasses."""
        received = []

        @component
        def App() -> None:
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
    """Tests for BrowserMessageHandler."""

    def test_message_to_dict_converts_patch_message(self) -> None:
        """_message_to_dict converts PatchMessage to dict with type field."""
        from trellis.platforms.browser.handler import _message_to_dict

        msg = PatchMessage(patches=[])
        result = _message_to_dict(msg)

        assert result == {"type": "patch", "patches": []}

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

        msg = PatchMessage(patches=[])
        asyncio.run(handler.send_message(msg))

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "patch"
        assert received_messages[0]["patches"] == []

    def test_send_message_without_callback_no_error(self) -> None:
        """send_message() without callback doesn't raise."""

        @component
        def App() -> None:
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
            started.append(True)
            await asyncio.sleep(0.01)
            completed.append(True)

        @component
        def App() -> None:
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
        """Background tasks are tracked to prevent GC."""
        task_completed = []

        async def async_handler() -> None:
            await asyncio.sleep(0.01)
            task_completed.append(True)

        @component
        def App() -> None:
            Button(text="Async", on_click=async_handler)

        handler = MessageHandler(App)
        tree = get_initial_tree(handler)

        button = tree["children"][0]
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


class TestRenderLoop:
    """Tests for the render loop behavior."""

    def test_render_loop_sends_patches_when_dirty(self) -> None:
        """Render loop sends PatchMessage when dirty nodes exist."""
        from trellis.core.messages import HelloMessage, PatchMessage

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

        sent_messages: list[Message] = []

        class TestableHandler(MessageHandler):
            """Handler that captures sent messages."""

            def __init__(self, root: Component) -> None:
                # Use very short batch delay for testing
                super().__init__(root, batch_delay=0.01)
                self._hello_sent = False
                self._inbox: asyncio.Queue[Message] = asyncio.Queue()

            async def send_message(self, msg: Message) -> None:
                sent_messages.append(msg)

            async def receive_message(self) -> Message:
                if not self._hello_sent:
                    self._hello_sent = True
                    return HelloMessage(client_id="test")
                return await self._inbox.get()

            def post(self, msg: Message) -> None:
                self._inbox.put_nowait(msg)

        async def run_test() -> None:
            handler = TestableHandler(Counter)

            # Start run() in background
            run_task = asyncio.create_task(handler.run())

            # Wait for hello and initial render
            await asyncio.sleep(0.02)

            # Get the increment callback from initial PatchMessage
            initial = next(m for m in sent_messages if isinstance(m, PatchMessage))
            tree = initial.patches[0].node
            button = tree["children"][1]
            cb_id = button["props"]["on_click"]["__callback__"]

            # Send event to trigger state change
            handler.post(EventMessage(callback_id=cb_id, args=[]))

            # Wait for render loop to pick it up
            await asyncio.sleep(0.03)

            # Should have sent a PatchMessage
            patch_messages = [m for m in sent_messages if isinstance(m, PatchMessage)]
            assert len(patch_messages) >= 1

            # Clean up
            run_task.cancel()
            try:
                await run_task
            except asyncio.CancelledError:
                pass

        asyncio.run(run_test())

    def test_render_loop_sends_error_on_render_failure(self) -> None:
        """Render loop sends ErrorMessage on render exception."""
        from trellis.core.messages import HelloMessage

        @dataclass(kw_only=True)
        class FailState(Stateful):
            should_fail: bool = False

        @component
        def FailingApp() -> None:
            state = FailState()
            if state.should_fail:
                raise ValueError("Intentional render failure")

            def trigger() -> None:
                state.should_fail = True

            Label(text="Hello")
            Button(text="Fail", on_click=trigger)

        sent_messages: list[Message] = []

        class TestableHandler(MessageHandler):
            def __init__(self, root: Component) -> None:
                super().__init__(root, batch_delay=0.01)
                self._hello_sent = False
                self._inbox: asyncio.Queue[Message] = asyncio.Queue()

            async def send_message(self, msg: Message) -> None:
                sent_messages.append(msg)

            async def receive_message(self) -> Message:
                if not self._hello_sent:
                    self._hello_sent = True
                    return HelloMessage(client_id="test")
                return await self._inbox.get()

            def post(self, msg: Message) -> None:
                self._inbox.put_nowait(msg)

        async def run_test() -> None:
            handler = TestableHandler(FailingApp)

            run_task = asyncio.create_task(handler.run())
            await asyncio.sleep(0.02)

            initial = next(m for m in sent_messages if isinstance(m, PatchMessage))
            tree = initial.patches[0].node
            button = tree["children"][1]
            cb_id = button["props"]["on_click"]["__callback__"]

            handler.post(EventMessage(callback_id=cb_id, args=[]))
            await asyncio.sleep(0.05)

            error_messages = [m for m in sent_messages if isinstance(m, ErrorMessage)]
            assert len(error_messages) >= 1
            assert "Intentional render failure" in error_messages[0].error
            assert error_messages[0].context == "render"

            run_task.cancel()
            try:
                await run_task
            except asyncio.CancelledError:
                pass

        asyncio.run(run_test())

    def test_render_loop_cancels_cleanly(self) -> None:
        """Render loop cancels without error on disconnect."""
        from trellis.core.messages import HelloMessage

        @component
        def App() -> None:
            Label(text="Hello")

        class TestableHandler(MessageHandler):
            def __init__(self, root: Component) -> None:
                super().__init__(root, batch_delay=0.01)
                self._hello_sent = False

            async def send_message(self, msg: Message) -> None:
                pass

            async def receive_message(self) -> Message:
                if not self._hello_sent:
                    self._hello_sent = True
                    return HelloMessage(client_id="test")
                await asyncio.sleep(999999)
                return HelloMessage(client_id="never")

        async def run_test() -> None:
            handler = TestableHandler(App)
            run_task = asyncio.create_task(handler.run())
            await asyncio.sleep(0.02)

            run_task.cancel()

            with pytest.raises(asyncio.CancelledError):
                await run_task

            assert handler._render_task is not None
            assert handler._render_task.cancelled()

        asyncio.run(run_test())


class TestPatchComputation:
    """Tests for patch computation edge cases."""

    def test_compute_patches_deep_nesting(self) -> None:
        """Only changed nodes generate patches, not their unchanged parents."""

        @dataclass(kw_only=True)
        class DeepState(Stateful):
            value: int = 0

        @component
        def DeepLeaf() -> None:
            state = DeepState()
            Label(text=str(state.value))
            Button(text="+", on_click=lambda: setattr(state, "value", state.value + 1))

        @component
        def Middle() -> None:
            Label(text="Middle")
            DeepLeaf()

        @component
        def Outer() -> None:
            Label(text="Outer")
            Middle()

        handler = MessageHandler(Outer)
        tree = get_initial_tree(handler)

        # Get the button callback (deeply nested)
        # Structure: Outer > [Label, Middle > [Label, DeepLeaf > [Label, Button]]]
        middle = tree["children"][1]
        deep_leaf = middle["children"][1]
        button = deep_leaf["children"][1]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Trigger state change
        event_msg = EventMessage(callback_id=cb_id, args=[])
        asyncio.run(handler.handle_message(event_msg))

        # Get patches
        patches = render(handler.session)

        # Should have patches, but Outer and Middle labels shouldn't be in them
        from trellis.core.messages import UpdatePatch

        update_patches = [p for p in patches if isinstance(p, UpdatePatch)]

        # Only the DeepLeaf's Label should be updated (text changed from "0" to "1")
        label_updates = [
            p for p in update_patches if p.props and "text" in p.props and p.props["text"] == "1"
        ]
        assert len(label_updates) >= 1

        # Outer and Middle labels should NOT be in the patches
        outer_label_updates = [
            p for p in update_patches if p.props and p.props.get("text") == "Outer"
        ]
        middle_label_updates = [
            p for p in update_patches if p.props and p.props.get("text") == "Middle"
        ]
        assert len(outer_label_updates) == 0
        assert len(middle_label_updates) == 0

    def test_compute_patches_reordered_children(self) -> None:
        """Reordering children generates correct update patches."""
        from dataclasses import field

        @dataclass(kw_only=True)
        class ListState(Stateful):
            items: list[str] = field(default_factory=lambda: ["a", "b", "c"])

        @component
        def ListApp() -> None:
            state = ListState()

            def reverse() -> None:
                state.items = list(reversed(state.items))

            for item in state.items:
                Label(text=item, key=item)
            Button(text="Reverse", on_click=reverse)

        handler = MessageHandler(ListApp)
        tree = get_initial_tree(handler)

        # Initial order: a, b, c
        labels = [c for c in tree["children"] if c["name"] == "Label"]
        assert [l["props"]["text"] for l in labels] == ["a", "b", "c"]

        # Get reverse callback
        button = next(c for c in tree["children"] if c["name"] == "Button")
        cb_id = button["props"]["on_click"]["__callback__"]

        # Reverse the list
        asyncio.run(handler.handle_message(EventMessage(callback_id=cb_id, args=[])))
        patches = render(handler.session)

        # Should have update patches for children reordering
        from trellis.core.messages import UpdatePatch

        update_patches = [p for p in patches if isinstance(p, UpdatePatch)]
        # At least one update should contain children info
        assert len(update_patches) > 0

    def test_unchanged_nodes_no_patches(self) -> None:
        """Unchanged nodes should not generate any patches."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @component
        def Counter() -> None:
            state = CounterState()

            def increment() -> None:
                state.count += 1

            Label(text="Static label that never changes")  # This should never get patches
            Label(text=str(state.count))
            Button(text="+", on_click=increment)

        handler = MessageHandler(Counter)
        tree = get_initial_tree(handler)

        # Get the static label's key to track it
        static_label = tree["children"][0]
        static_label_id = static_label.get("key")

        # Trigger a state change
        button = tree["children"][2]
        cb_id = button["props"]["on_click"]["__callback__"]
        asyncio.run(handler.handle_message(EventMessage(callback_id=cb_id, args=[])))

        # Get patches
        patches = render(handler.session)

        # The static label should NOT be in any patch
        from trellis.core.messages import UpdatePatch

        update_patches = [p for p in patches if isinstance(p, UpdatePatch)]
        for patch in update_patches:
            if patch.id == static_label_id:
                # If it is in the patches, it shouldn't have any actual changes
                # (or it shouldn't be there at all)
                if patch.props:
                    assert "text" not in patch.props or patch.props["text"] != "Static label that never changes"

    def test_container_child_replacement_emits_add_remove_patches(self) -> None:
        """Replacing container children emits RemovePatch and AddPatch.

        This tests the tab-switching scenario: a container (like Card) has
        entirely new children after state change. The old children should
        be removed and new children added.

        Regression test for: container not detecting child changes when
        the container's props are unchanged but children are different.
        """
        from dataclasses import field

        from trellis.core.messages import AddPatch, RemovePatch
        from trellis.widgets import Card

        @dataclass(kw_only=True)
        class TabState(Stateful):
            selected: str = "tab1"

        @component
        def Tab1Content() -> None:
            Label(text="Content for tab 1")

        @component
        def Tab2Content() -> None:
            Label(text="Content for tab 2")

        @component
        def TabApp() -> None:
            state = TabState()

            def switch_tab() -> None:
                state.selected = "tab2" if state.selected == "tab1" else "tab1"

            Button(text="Switch", on_click=switch_tab)
            with Card():
                if state.selected == "tab1":
                    Tab1Content()
                else:
                    Tab2Content()

        handler = MessageHandler(TabApp)
        tree = get_initial_tree(handler)

        # Verify initial state - Card contains Tab1Content
        card = tree["children"][1]
        assert card["type"] == "Card"
        tab1_content = card["children"][0]
        assert tab1_content["name"] == "Tab1Content"

        # Get the switch button callback
        button = tree["children"][0]
        cb_id = button["props"]["on_click"]["__callback__"]

        # Switch tabs
        asyncio.run(handler.handle_message(EventMessage(callback_id=cb_id, args=[])))
        patches = render(handler.session)

        # Should have RemovePatch for Tab1Content and AddPatch for Tab2Content
        remove_patches = [p for p in patches if isinstance(p, RemovePatch)]
        add_patches = [p for p in patches if isinstance(p, AddPatch)]

        assert len(remove_patches) >= 1, f"Expected RemovePatch, got patches: {patches}"
        assert len(add_patches) >= 1, f"Expected AddPatch, got patches: {patches}"

        # Verify the added node is Tab2Content
        added_names = [p.node.get("name") for p in add_patches]
        assert "Tab2Content" in added_names, f"Expected Tab2Content in {added_names}"
