"""Integration tests for render loop behavior and patch computation."""

import asyncio
import typing as tp
from dataclasses import dataclass, field

import pytest

from tests.conftest import get_button_element
from trellis.core.components.base import Component
from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.patches import RenderAddPatch, RenderRemovePatch, RenderUpdatePatch
from trellis.core.rendering.render import render
from trellis.core.state.stateful import Stateful
from trellis.platforms.browser.handler import BrowserMessageHandler
from trellis.platforms.common.handler import AppWrapper, MessageHandler
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


def _make_test_wrapper() -> AppWrapper:
    """Create a simple wrapper for tests that don't need full TrellisApp."""

    def wrapper(
        comp: Component,
        system_theme: str,
        theme_mode: str | None,
    ) -> CompositionComponent:
        def render_func() -> None:
            comp()

        return CompositionComponent(name="TestRoot", render_func=render_func)

    return wrapper


def _init_handler_for_test(handler: BrowserMessageHandler) -> None:
    """Initialize handler by posting HelloMessage and calling handle_hello.

    This simulates the production flow where handle_hello creates the session.
    """
    handler._inbox.put_nowait(HelloMessage(client_id="test", system_theme="light"))
    asyncio.run(handler.handle_hello())


def get_initial_tree(handler: MessageHandler) -> dict[str, tp.Any]:
    """Helper to get tree dict from initial render."""
    msg = handler.initial_render()
    assert isinstance(msg, PatchMessage)
    assert len(msg.patches) == 1
    patch = msg.patches[0]
    assert isinstance(patch, AddPatch)
    return patch.element


# Names of infrastructure wrapper components that we navigate through
_WRAPPER_COMPONENT_NAMES = frozenset(
    {
        "TrellisRoot",
        "TrellisApp",
        "TestRoot",
    }
)

# Types that are always wrappers (not CompositionComponent - that's too generic)
_WRAPPER_COMPONENT_TYPES = frozenset(
    {
        "ThemeProvider",
        "ClientState",
    }
)


def find_app_children(tree: dict[str, tp.Any]) -> list[dict[str, tp.Any]]:
    """Find the user's app children within the TrellisApp wrapper.

    The tree structure is:
    TrellisRoot -> TrellisApp -> ClientState -> ThemeProvider -> UserApp -> children

    This helper navigates through wrapper components to find user content.
    Infrastructure wrappers are identified by specific names or types.
    Returns the children of the user's root component.
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
        node_name = first.get("name", "")

        # If this is an infrastructure wrapper, continue navigating down
        if node_type in _WRAPPER_COMPONENT_TYPES or node_name in _WRAPPER_COMPONENT_NAMES:
            node = first
            continue

        # Found user's root component - return its children
        return first.get("children", [])

    # Hit safety limit - return empty to avoid infinite loops
    return []


class TestRenderLoop:
    """Tests for the render loop behavior."""

    def test_render_loop_sends_patches_when_dirty(self) -> None:
        """Render loop sends PatchMessage when dirty nodes exist."""

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

            def __init__(self, root: Component, app_wrapper: AppWrapper) -> None:
                # Use very short batch delay for testing
                super().__init__(root, app_wrapper, batch_delay=0.01)
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
            handler = TestableHandler(Counter, _make_test_wrapper())

            # Start run() in background
            run_task = asyncio.create_task(handler.run())

            # Wait for hello and initial render
            await asyncio.sleep(0.02)

            # Get the increment callback from initial PatchMessage
            initial = next(m for m in sent_messages if isinstance(m, PatchMessage))
            tree = initial.patches[0].element
            app_children = find_app_children(tree)
            button = get_button_element(app_children[1])
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
            state = FailState()
            if state.should_fail:
                raise ValueError("Intentional render failure")

            def trigger() -> None:
                state.should_fail = True

            Label(text="Hello")
            Button(text="Fail", on_click=trigger)

        sent_messages: list[Message] = []

        class TestableHandler(MessageHandler):
            def __init__(self, root: Component, app_wrapper: AppWrapper) -> None:
                super().__init__(root, app_wrapper, batch_delay=0.01)
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
            handler = TestableHandler(FailingApp, _make_test_wrapper())

            run_task = asyncio.create_task(handler.run())
            await asyncio.sleep(0.02)

            initial = next(m for m in sent_messages if isinstance(m, PatchMessage))
            tree = initial.patches[0].element
            app_children = find_app_children(tree)
            button = get_button_element(app_children[1])
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
            Label(text="Hello")

        class TestableHandler(MessageHandler):
            def __init__(self, root: Component, app_wrapper: AppWrapper) -> None:
                super().__init__(root, app_wrapper, batch_delay=0.01)
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
            handler = TestableHandler(App, _make_test_wrapper())
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

        handler = BrowserMessageHandler(Outer, _make_test_wrapper())
        _init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        # Get the button callback (deeply nested)
        # Structure: Wrapper > Outer > [Label, Middle > [Label, DeepLeaf > [Label, Button]]]
        app_children = find_app_children(tree)
        middle = app_children[1]
        deep_leaf = middle["children"][1]
        button = get_button_element(deep_leaf["children"][1])
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
            state = ListState()

            def reverse() -> None:
                state.items = list(reversed(state.items))

            for item in state.items:
                Label(text=item, key=item)
            Button(text="Reverse", on_click=reverse)

        handler = BrowserMessageHandler(ListApp, _make_test_wrapper())
        _init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        # Initial order: a, b, c (within wrapper)
        app_children = find_app_children(tree)
        labels = [c for c in app_children if c["name"] == "Label"]
        assert [label["props"]["text"] for label in labels] == ["a", "b", "c"]

        # Get reverse callback
        button_wrapper = next(c for c in app_children if c["name"] == "Button")
        button = get_button_element(button_wrapper)
        cb_id = button["props"]["on_click"]["__callback__"]

        # Reverse the list
        asyncio.run(handler.handle_message(EventMessage(callback_id=cb_id, args=[])))
        patches = render(handler.session)

        # Should have update patches for children reordering - render() returns RenderUpdatePatch
        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        # At least one update should exist
        assert len(update_patches) > 0

    def test_unchanged_elements_no_patches(self) -> None:
        """Unchanged elements should not generate any patches."""

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

        handler = BrowserMessageHandler(Counter, _make_test_wrapper())
        _init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        # Get the static label's key to track it (within wrapper)
        app_children = find_app_children(tree)
        static_label = app_children[0]
        static_label_id = static_label.get("key")

        # Trigger a state change
        button = get_button_element(app_children[2])
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

        handler = BrowserMessageHandler(TabApp, _make_test_wrapper())
        _init_handler_for_test(handler)
        tree = get_initial_tree(handler)

        # Verify initial state - Card contains Tab1Content (within wrapper)
        app_children = find_app_children(tree)
        card = app_children[1]
        assert card["type"] == "Card"
        tab1_content = card["children"][0]
        assert tab1_content["name"] == "Tab1Content"

        # Get the switch button callback
        button = get_button_element(app_children[0])
        cb_id = button["props"]["on_click"]["__callback__"]

        # Switch tabs
        asyncio.run(handler.handle_message(EventMessage(callback_id=cb_id, args=[])))
        patches = render(handler.session)

        # Should have RenderRemovePatch for Tab1Content and RenderAddPatch for Tab2Content
        remove_patches = [p for p in patches if isinstance(p, RenderRemovePatch)]
        add_patches = [p for p in patches if isinstance(p, RenderAddPatch)]

        assert len(remove_patches) >= 1, f"Expected RenderRemovePatch, got patches: {patches}"
        assert len(add_patches) >= 1, f"Expected RenderAddPatch, got patches: {patches}"

        # Verify the added element is Tab2Content
        added_names = [p.element.component.name for p in add_patches]
        assert "Tab2Content" in added_names, f"Expected Tab2Content in {added_names}"
