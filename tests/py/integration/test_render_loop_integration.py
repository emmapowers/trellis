"""Integration tests for render loop behavior and patch computation."""

import asyncio
import typing as tp
from dataclasses import dataclass, field

import pytest

from trellis.core.components.base import Component
from trellis.core.components.composition import component
from trellis.core.rendering.patches import RenderAddPatch, RenderRemovePatch, RenderUpdatePatch
from trellis.core.rendering.render import render
from trellis.core.state.stateful import Stateful
from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import (
    AddPatch,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    Message,
    PatchMessage,
    UpdatePatch,
)
from trellis.widgets import Button, Card, Label


def get_initial_tree(handler: MessageHandler) -> dict[str, tp.Any]:
    """
    Retrieve the UI tree node produced by the handler's initial render.
    
    Parameters:
        handler (MessageHandler): Handler whose initial_render() will be queried for the initial PatchMessage.
    
    Returns:
        dict[str, Any]: The node dictionary from the first AddPatch in the initial PatchMessage.
    
    Raises:
        AssertionError: If the initial message is not a PatchMessage, does not contain exactly one patch, or that patch is not an AddPatch.
    """
    msg = handler.initial_render()
    assert isinstance(msg, PatchMessage)
    assert len(msg.patches) == 1
    patch = msg.patches[0]
    assert isinstance(patch, AddPatch)
    return patch.node


class TestRenderLoop:
    """Tests for the render loop behavior."""

    def test_render_loop_sends_patches_when_dirty(self) -> None:
        """Render loop sends PatchMessage when dirty nodes exist."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @component
        def Counter() -> None:
            """
            Render a simple counter component with a label showing the current count and a button to increment it.
            
            Displays the current integer count and updates the displayed value each time the "+" button is pressed.
            """
            state = CounterState()

            def increment() -> None:
                """
                Increment the counter stored in the surrounding state.
                
                Increases `state.count` by 1.
                """
                state.count += 1

            Label(text=str(state.count))
            Button(text="+", on_click=increment)

        sent_messages: list[Message] = []

        class TestableHandler(MessageHandler):
            """Handler that captures sent messages."""

            def __init__(self, root: Component) -> None:
                # Use very short batch delay for testing
                """
                Create a test-oriented MessageHandler configured with a very short batching delay.
                
                Initializes the base handler with batch_delay=0.01 to accelerate render-loop batching in tests, sets an internal `_hello_sent` flag used to track the initial HelloMessage, and creates an asyncio.Queue `_inbox` for enqueuing incoming messages.
                
                Parameters:
                    root (Component): The root component that this handler will manage.
                """
                super().__init__(root, batch_delay=0.01)
                self._hello_sent = False
                self._inbox: asyncio.Queue[Message] = asyncio.Queue()

            async def send_message(self, msg: Message) -> None:
                """
                Capture an outgoing Message by appending it to the handler's local sent_messages list.
                
                Parameters:
                    msg (Message): The message to record.
                """
                sent_messages.append(msg)

            async def receive_message(self) -> Message:
                """
                Return the next incoming Message for the handler, providing an initial HelloMessage on the first invocation.
                
                Returns:
                    Message: The next message from the handler's inbox. On the first call this is a HelloMessage with `client_id="test"`, thereafter messages are taken from the internal inbox queue.
                """
                if not self._hello_sent:
                    self._hello_sent = True
                    return HelloMessage(client_id="test")
                return await self._inbox.get()

            def post(self, msg: Message) -> None:
                """
                Enqueue a message into the handler's local inbox for later processing.
                
                Parameters:
                    msg (Message): The message to enqueue.
                """
                self._inbox.put_nowait(msg)

        async def run_test() -> None:
            """
            Runs the TestableHandler for the Counter component, simulates a button click, and verifies that the render loop sends at least one PatchMessage.
            
            This starts the handler.run() task, waits for the initial render, extracts the button's callback id from the initial PatchMessage, posts an EventMessage to trigger a state change, waits for the render loop to process the event and asserts that at least one PatchMessage was sent afterward, then cancels the background task and ensures clean cancellation.
            """
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

        @dataclass(kw_only=True)
        class FailState(Stateful):
            should_fail: bool = False

        @component
        def FailingApp() -> None:
            """
            Component that renders a label and a button that triggers a deliberate render failure.
            
            When rendered, this component creates internal state with a `should_fail` flag. If that flag
            is True during rendering, the component raises a ValueError with the message "Intentional render failure".
            The button's callback sets `should_fail` to True so a subsequent render will raise the error.
            
            Raises:
                ValueError: If the internal `should_fail` flag is True at render time (message: "Intentional render failure").
            """
            state = FailState()
            if state.should_fail:
                raise ValueError("Intentional render failure")

            def trigger() -> None:
                """
                Mark the state to trigger an intentional render failure.
                
                Sets `state.should_fail` to `True`, causing subsequent renders to raise an intentional error.
                """
                state.should_fail = True

            Label(text="Hello")
            Button(text="Fail", on_click=trigger)

        sent_messages: list[Message] = []

        class TestableHandler(MessageHandler):
            def __init__(self, root: Component) -> None:
                """
                Initialize a testable MessageHandler configured for fast batching and an internal inbox.
                
                Parameters:
                    root (Component): The root component for the handler.
                
                Notes:
                    - Sets a small batch_delay (0.01) to speed up render batching in tests.
                    - Initializes `_hello_sent` to track if the initial HelloMessage was emitted.
                    - Creates `_inbox`, an asyncio.Queue[Message], for injected incoming messages.
                """
                super().__init__(root, batch_delay=0.01)
                self._hello_sent = False
                self._inbox: asyncio.Queue[Message] = asyncio.Queue()

            async def send_message(self, msg: Message) -> None:
                """
                Capture an outgoing Message by appending it to the handler's local sent_messages list.
                
                Parameters:
                    msg (Message): The message to record.
                """
                sent_messages.append(msg)

            async def receive_message(self) -> Message:
                """
                Return the next incoming Message for the handler, providing an initial HelloMessage on the first invocation.
                
                Returns:
                    Message: The next message from the handler's inbox. On the first call this is a HelloMessage with `client_id="test"`, thereafter messages are taken from the internal inbox queue.
                """
                if not self._hello_sent:
                    self._hello_sent = True
                    return HelloMessage(client_id="test")
                return await self._inbox.get()

            def post(self, msg: Message) -> None:
                """
                Enqueue a message into the handler's local inbox for later processing.
                
                Parameters:
                    msg (Message): The message to enqueue.
                """
                self._inbox.put_nowait(msg)

        async def run_test() -> None:
            """
            Exercise the handler run loop with a failing component, trigger the failure, and assert an error message is emitted and the run task cancels cleanly.
            
            Runs a TestableHandler for the FailingApp, locates the initial button callback from the first PatchMessage, posts an EventMessage to trigger a render failure, and asserts at least one ErrorMessage was sent containing "Intentional render failure" with context "render". Finally cancels the handler run task and awaits its cancellation.
            """
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

        @component
        def App() -> None:
            """
            Render a simple component that displays the text "Hello".
            
            Renders a single Label node with text "Hello".
            """
            Label(text="Hello")

        class TestableHandler(MessageHandler):
            def __init__(self, root: Component) -> None:
                """
                Create a test-oriented MessageHandler configured for fast batching and hello-message tracking.
                
                This initializer constructs the handler with a short batch delay (0.01) to accelerate render-loop tests and initializes an internal flag used to track whether the initial `HelloMessage` has been sent.
                
                Parameters:
                    root (Component): The root UI component to render and manage.
                """
                super().__init__(root, batch_delay=0.01)
                self._hello_sent = False

            async def send_message(self, msg: Message) -> None:
                """
                Send an outgoing Message to the connected client or transport.
                
                Implementations should deliver or enqueue `msg` for transmission to the remote client; subclasses may override to capture, transform, or batch messages before sending.
                
                Parameters:
                    msg (Message): The message to be sent to the client.
                """
                pass

            async def receive_message(self) -> Message:
                """
                Simulate receiving messages from a test client for handler tests.
                
                On the first invocation returns a HelloMessage with client_id "test". On subsequent invocations it sleeps for a very long time to simulate a hung inbox and (after that delay) would return a HelloMessage with client_id "never".
                
                Returns:
                    Message: A HelloMessage — client_id is "test" on the first call, "never" after the long sleep on later calls.
                """
                if not self._hello_sent:
                    self._hello_sent = True
                    return HelloMessage(client_id="test")
                await asyncio.sleep(999999)
                return HelloMessage(client_id="never")

        async def run_test() -> None:
            """
            Verifies that the handler's run loop cancels cleanly and that its internal render task is cancelled.
            
            Starts the TestableHandler, waits briefly to allow tasks to start, cancels the main run task, asserts that awaiting it raises CancelledError, and checks that the handler's internal render task exists and is cancelled.
            """
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
            """
            Renders a label displaying a DeepState value and a button that increments that value.
            
            The label shows state.value as text. The "+" button increments state.value by 1 when clicked.
            """
            state = DeepState()
            Label(text=str(state.value))
            Button(text="+", on_click=lambda: setattr(state, "value", state.value + 1))

        @component
        def Middle() -> None:
            """
            Renders the middle layer containing a "Middle" label and the DeepLeaf component.
            
            This component composes a static Label with text "Middle" and a DeepLeaf child.
            """
            Label(text="Middle")
            DeepLeaf()

        @component
        def Outer() -> None:
            """
            Render an outer container with a "Outer" label and the Middle component as its child.
            
            Used to construct a nested component hierarchy for testing patch propagation.
            """
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

        # Should have patches - render() returns RenderUpdatePatch
        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]

        # At least one update should have props with the new text value
        props_patches = [p for p in update_patches if p.props and p.props.get("text") == "1"]
        assert len(props_patches) >= 1

    def test_compute_patches_reordered_children(self) -> None:
        """Reordering children generates correct update patches."""

        @dataclass(kw_only=True)
        class ListState(Stateful):
            items: list[str] = field(default_factory=lambda: ["a", "b", "c"])

        @component
        def ListApp() -> None:
            """
            Render a list of Label components—one per item in the list state—and a Button that reverses the item order.
            
            Each item is rendered as a Label with text set to the item value and key set to the same value. The Button labeled "Reverse" invokes a callback that replaces the state's items with their reversed order.
            """
            state = ListState()

            def reverse() -> None:
                """
                Reverse the order of items in the component state.
                
                Updates state.items to a new list containing the elements in reverse order.
                """
                state.items = list(reversed(state.items))

            for item in state.items:
                Label(text=item, key=item)
            Button(text="Reverse", on_click=reverse)

        handler = MessageHandler(ListApp)
        tree = get_initial_tree(handler)

        # Initial order: a, b, c
        labels = [c for c in tree["children"] if c["name"] == "Label"]
        assert [label["props"]["text"] for label in labels] == ["a", "b", "c"]

        # Get reverse callback
        button = next(c for c in tree["children"] if c["name"] == "Button")
        cb_id = button["props"]["on_click"]["__callback__"]

        # Reverse the list
        asyncio.run(handler.handle_message(EventMessage(callback_id=cb_id, args=[])))
        patches = render(handler.session)

        # Should have update patches for children reordering - render() returns RenderUpdatePatch
        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        # At least one update should exist
        assert len(update_patches) > 0

    def test_unchanged_nodes_no_patches(self) -> None:
        """Unchanged nodes should not generate any patches."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @component
        def Counter() -> None:
            """
            Render a counter component with a static label, a dynamic label showing the current count, and a button that increments the count.
            
            The static label's text is constant and should not produce patches during updates. The second label displays the current value of the component's internal state. The button calls an increment function that mutates the state's `count`.
            """
            state = CounterState()

            def increment() -> None:
                """
                Increment the counter stored in the surrounding state.
                
                Increases `state.count` by 1.
                """
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
        update_patches = [p for p in patches if isinstance(p, UpdatePatch)]
        for patch in update_patches:
            if patch.id == static_label_id:
                # If it is in the patches, it shouldn't have any actual changes
                # (or it shouldn't be there at all)
                if patch.props:
                    assert (
                        "text" not in patch.props
                        or patch.props["text"] != "Static label that never changes"
                    )

    def test_container_child_replacement_emits_add_remove_patches(self) -> None:
        """Replacing container children emits RemovePatch and AddPatch.

        This tests the tab-switching scenario: a container (like Card) has
        entirely new children after state change. The old children should
        be removed and new children added.

        Regression test for: container not detecting child changes when
        the container's props are unchanged but children are different.
        """

        @dataclass(kw_only=True)
        class TabState(Stateful):
            selected: str = "tab1"

        @component
        def Tab1Content() -> None:
            """
            Render the content for the first tab.
            
            Renders a Label with the text "Content for tab 1".
            """
            Label(text="Content for tab 1")

        @component
        def Tab2Content() -> None:
            """
            Render the content for the second tab.
            
            Renders a Label with the text "Content for tab 2".
            """
            Label(text="Content for tab 2")

        @component
        def TabApp() -> None:
            """
            Render a switchable tabbed Card showing either Tab1Content or Tab2Content.
            
            Creates a TabState and a "Switch" button that toggles state.selected between "tab1" and "tab2"; the Card's contents show Tab1Content when selected is "tab1" and Tab2Content otherwise.
            """
            state = TabState()

            def switch_tab() -> None:
                """
                Toggle the tab selection between "tab1" and "tab2".
                
                Updates the component state by setting `state.selected` to "tab2" when it is currently "tab1", otherwise sets it to "tab1".
                """
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

        # Should have RenderRemovePatch for Tab1Content and RenderAddPatch for Tab2Content
        remove_patches = [p for p in patches if isinstance(p, RenderRemovePatch)]
        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]

        assert len(remove_patches) >= 1, f"Expected RenderRemovePatch, got patches: {patches}"
        assert len(add_patches) >= 1, f"Expected RenderAddPatch, got patches: {patches}"

        # Verify the added node is Tab2Content
        added_names = [p.node.component.name for p in add_patches]
        assert "Tab2Content" in added_names, f"Expected Tab2Content in {added_names}"