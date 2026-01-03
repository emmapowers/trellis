"""Integration tests for router-handler integration (Phase 6).

Tests that MessageHandler properly integrates with RouterState:
- Initial path from HelloMessage is accessible to components
- UrlChanged messages update RouterState
- RouterState navigation methods trigger history messages to client
"""

import asyncio
import typing as tp

from trellis.core.components.composition import CompositionComponent, component
from trellis.platforms.common.handler import AppWrapper, MessageHandler
from trellis.platforms.common.messages import (
    AddPatch,
    HelloMessage,
    HistoryBack,
    HistoryForward,
    HistoryPush,
    Message,
    PatchMessage,
    UrlChanged,
)
from trellis.routing import Link, Route, RouterState, Routes, router
from trellis.widgets import Button, Label


def simple_app_wrapper(
    comp: tp.Any, system_theme: str, theme_mode: str | None
) -> CompositionComponent:
    """Simple app wrapper for testing without full TrellisApp."""

    def render_func() -> None:
        comp()

    return CompositionComponent(name="TestRoot", render_func=render_func)


class MockMessageHandler(MessageHandler):
    """MessageHandler with mocked transport for testing."""

    def __init__(
        self, root_component: tp.Any, app_wrapper: AppWrapper = simple_app_wrapper
    ) -> None:
        super().__init__(root_component, app_wrapper)
        self.sent_messages: list[Message] = []
        self.incoming_messages: list[Message] = []
        self._message_index = 0

    async def send_message(self, msg: Message) -> None:
        self.sent_messages.append(msg)

    async def receive_message(self) -> Message:
        if self._message_index < len(self.incoming_messages):
            msg = self.incoming_messages[self._message_index]
            self._message_index += 1
            return msg
        # Block forever if no messages (tests should add messages before calling)
        await asyncio.sleep(float("inf"))
        raise RuntimeError("No more messages")

    def queue_incoming(self, msg: Message) -> None:
        """Queue a message to be received."""
        self.incoming_messages.append(msg)


def get_initial_tree(handler: MessageHandler) -> dict[str, tp.Any]:
    """Helper to get tree dict from initial render."""
    msg = handler.initial_render()
    assert isinstance(msg, PatchMessage)
    assert len(msg.patches) == 1
    patch = msg.patches[0]
    assert isinstance(patch, AddPatch)
    return patch.node


class TestInitialPathFromHelloMessage:
    """Tests for reading initial path from HelloMessage."""

    def test_hello_message_path_accessible_to_router_state(self) -> None:
        """RouterState can access initial path from HelloMessage."""
        received_path: list[str] = []

        @component
        def App() -> None:
            # RouterState should be able to access initial path
            with RouterState() as rs:
                received_path.append(rs.path)
                Label(text=rs.path)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/users/123"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()

        asyncio.run(test())

        # RouterState should have received the initial path from HelloMessage
        assert received_path == ["/users/123"]

    def test_hello_message_default_path_is_root(self) -> None:
        """Default path is '/' when not specified in HelloMessage."""
        received_path: list[str] = []

        @component
        def App() -> None:
            with RouterState() as rs:
                received_path.append(rs.path)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()

        asyncio.run(test())

        assert received_path == ["/"]

    def test_route_component_matches_initial_path(self) -> None:
        """Route component correctly matches against initial path from HelloMessage."""
        matched_routes: list[str] = []

        @component
        def HomePage() -> None:
            matched_routes.append("home")

        @component
        def UsersPage() -> None:
            matched_routes.append("users")

        @component
        def App() -> None:
            with RouterState():
                with Routes():
                    with Route(pattern="/"):
                        HomePage()
                    with Route(pattern="/users"):
                        UsersPage()

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/users"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()

        asyncio.run(test())

        # Only /users route should match
        assert matched_routes == ["users"]


class TestUrlChangedMessage:
    """Tests for handling UrlChanged messages from client."""

    def test_url_changed_updates_router_state(self) -> None:
        """UrlChanged message updates RouterState path."""
        router_state = RouterState(path="/")
        observed_paths: list[str] = []

        @component
        def App() -> None:
            with router_state:
                observed_paths.append(router_state.path)
                Label(text=router_state.path)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()

            # Simulate browser back button causing URL change
            response = await handler.handle_message(UrlChanged(path="/about"))
            assert response is None  # No error

        asyncio.run(test())

        # RouterState should be updated
        assert router_state.path == "/about"

    def test_url_changed_triggers_rerender(self) -> None:
        """UrlChanged message marks dependent nodes dirty for re-render."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:
                Label(text=f"Path: {router_state.path}")

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()

            await handler.handle_message(UrlChanged(path="/new-path"))

            # Session should have dirty nodes
            assert handler.session.dirty.has_dirty()

        asyncio.run(test())

    def test_url_changed_updates_route_matching(self) -> None:
        """UrlChanged causes Route components to re-match."""
        router_state = RouterState(path="/")
        rendered_routes: list[str] = []

        @component
        def HomePage() -> None:
            rendered_routes.append("home")

        @component
        def AboutPage() -> None:
            rendered_routes.append("about")

        @component
        def App() -> None:
            with router_state:
                with Routes():
                    with Route(pattern="/"):
                        HomePage()
                    with Route(pattern="/about"):
                        AboutPage()

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            rendered_routes.clear()

            await handler.handle_message(UrlChanged(path="/about"))

            # Force re-render to see route changes
            from trellis.core.rendering.render import render

            render(handler.session)

        asyncio.run(test())

        # About page should have rendered
        assert "about" in rendered_routes


class TestHistoryMessagesFromRouterState:
    """Tests for sending history messages when RouterState navigation methods are called."""

    def test_navigate_sends_history_push(self) -> None:
        """RouterState.navigate() sends HistoryPush message to client."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:

                def handle_click() -> None:
                    router().navigate("/new-page")

                Button(text="Navigate", on_click=handle_click)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            handler.sent_messages.clear()

            # Get the button callback
            from trellis.platforms.common.messages import EventMessage
            from trellis.platforms.common.serialization import serialize_element

            tree = serialize_element(handler.session.root_element, handler.session)
            # Navigate: TestRoot -> App -> Button
            app = tree["children"][0]
            button = app["children"][0]
            cb_id = button["props"]["on_click"]["__callback__"]

            # Invoke callback
            await handler.handle_message(EventMessage(callback_id=cb_id, args=[]))

        asyncio.run(test())

        # Handler should have sent HistoryPush
        history_pushes = [m for m in handler.sent_messages if isinstance(m, HistoryPush)]
        assert len(history_pushes) == 1
        assert history_pushes[0].path == "/new-page"

    def test_go_back_sends_history_back(self) -> None:
        """RouterState.go_back() sends HistoryBack message to client."""
        router_state = RouterState(path="/")
        router_state.navigate("/page1")
        router_state.navigate("/page2")

        @component
        def App() -> None:
            with router_state:

                def handle_click() -> None:
                    router().go_back()

                Button(text="Back", on_click=handle_click)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/page2"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            handler.sent_messages.clear()

            from trellis.platforms.common.messages import EventMessage
            from trellis.platforms.common.serialization import serialize_element

            tree = serialize_element(handler.session.root_element, handler.session)
            # Navigate: TestRoot -> App -> Button
            app = tree["children"][0]
            button = app["children"][0]
            cb_id = button["props"]["on_click"]["__callback__"]

            await handler.handle_message(EventMessage(callback_id=cb_id, args=[]))

        asyncio.run(test())

        # Handler should have sent HistoryBack
        history_backs = [m for m in handler.sent_messages if isinstance(m, HistoryBack)]
        assert len(history_backs) == 1

    def test_go_forward_sends_history_forward(self) -> None:
        """RouterState.go_forward() sends HistoryForward message to client."""
        router_state = RouterState(path="/")
        router_state.navigate("/page1")
        router_state.go_back()  # Now can go forward

        @component
        def App() -> None:
            with router_state:

                def handle_click() -> None:
                    router().go_forward()

                Button(text="Forward", on_click=handle_click)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            handler.sent_messages.clear()

            from trellis.platforms.common.messages import EventMessage
            from trellis.platforms.common.serialization import serialize_element

            tree = serialize_element(handler.session.root_element, handler.session)
            # Navigate: TestRoot -> App -> Button
            app = tree["children"][0]
            button = app["children"][0]
            cb_id = button["props"]["on_click"]["__callback__"]

            await handler.handle_message(EventMessage(callback_id=cb_id, args=[]))

        asyncio.run(test())

        # Handler should have sent HistoryForward
        history_forwards = [m for m in handler.sent_messages if isinstance(m, HistoryForward)]
        assert len(history_forwards) == 1

    def test_link_click_sends_history_push(self) -> None:
        """Clicking a Link component sends HistoryPush message."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:
                Link(to="/target-page", text="Go")

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            handler.sent_messages.clear()

            from trellis.platforms.common.messages import EventMessage
            from trellis.platforms.common.serialization import serialize_element

            tree = serialize_element(handler.session.root_element, handler.session)
            # Navigate: TestRoot -> App -> Link -> Anchor
            app = tree["children"][0]
            link_comp = app["children"][0]
            anchor = link_comp["children"][0]
            cb_id = anchor["props"]["onClick"]["__callback__"]

            # Pass click event - handler converts dict with "type" to MouseEvent
            await handler.handle_message(EventMessage(callback_id=cb_id, args=[{"type": "click"}]))

        asyncio.run(test())

        # Handler should have sent HistoryPush
        history_pushes = [m for m in handler.sent_messages if isinstance(m, HistoryPush)]
        assert len(history_pushes) == 1
        assert history_pushes[0].path == "/target-page"


class TestNoHistoryMessageWhenNoNavigation:
    """Tests that history messages are NOT sent when navigation doesn't happen."""

    def test_no_history_push_when_go_back_fails(self) -> None:
        """go_back() at start of history doesn't send any message."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:

                def handle_click() -> None:
                    router().go_back()  # Should do nothing - at start

                Button(text="Back", on_click=handle_click)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            handler.sent_messages.clear()

            from trellis.platforms.common.messages import EventMessage
            from trellis.platforms.common.serialization import serialize_element

            tree = serialize_element(handler.session.root_element, handler.session)
            # Navigate: TestRoot -> App -> Button
            app = tree["children"][0]
            button = app["children"][0]
            cb_id = button["props"]["on_click"]["__callback__"]

            await handler.handle_message(EventMessage(callback_id=cb_id, args=[]))

        asyncio.run(test())

        # No history messages should be sent
        history_msgs = [
            m
            for m in handler.sent_messages
            if isinstance(m, (HistoryPush, HistoryBack, HistoryForward))
        ]
        assert len(history_msgs) == 0

    def test_no_history_forward_when_go_forward_fails(self) -> None:
        """go_forward() at end of history doesn't send any message."""
        router_state = RouterState(path="/")

        @component
        def App() -> None:
            with router_state:

                def handle_click() -> None:
                    router().go_forward()  # Should do nothing - at end

                Button(text="Forward", on_click=handle_click)

        handler = MockMessageHandler(App)
        handler.queue_incoming(HelloMessage(client_id="test", path="/"))

        async def test() -> None:
            await handler.handle_hello()
            handler.initial_render()
            handler.sent_messages.clear()

            from trellis.platforms.common.messages import EventMessage
            from trellis.platforms.common.serialization import serialize_element

            tree = serialize_element(handler.session.root_element, handler.session)
            # Navigate: TestRoot -> App -> Button
            app = tree["children"][0]
            button = app["children"][0]
            cb_id = button["props"]["on_click"]["__callback__"]

            await handler.handle_message(EventMessage(callback_id=cb_id, args=[]))

        asyncio.run(test())

        # No history messages should be sent
        history_msgs = [
            m
            for m in handler.sent_messages
            if isinstance(m, (HistoryPush, HistoryBack, HistoryForward))
        ]
        assert len(history_msgs) == 0
