"""Unit tests for the core protocol registry."""

from __future__ import annotations

import asyncio
import typing as tp

import msgspec
import pytest

import trellis.core.protocol as protocol_module
from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.protocol import (
    MessageHandlerProtocol,
    MessageHandler,
    StatefulMessageHandlerMixin,
    dispatch,
    get_message_handler,
    listen,
    register_message_types,
    send,
    set_message_handler,
)
from trellis.core.state.stateful import Stateful


class Ping(msgspec.Struct, tag="ping", tag_field="type"):
    value: int


class Pong(msgspec.Struct, tag="pong", tag_field="type"):
    value: int


class Temp(msgspec.Struct, tag="temp", tag_field="type"):
    value: int


class MockMessageHandler:
    """Minimal handler implementing the protocol interface for tests."""

    message_send_queue: asyncio.Queue[object]

    def __init__(self) -> None:
        self.message_send_queue = asyncio.Queue()


class TestMessageTypeRegistration:
    def test_register_message_types_by_tag(self, reset_protocol) -> None:
        register_message_types(Ping, Pong)

        assert Ping in tp.cast("dict[type[object], str]", protocol_module._MESSAGE_TAGS)
        assert "ping" in tp.cast("dict[str, type[object]]", protocol_module._MESSAGE_TYPES)

    def test_reset_for_tests_clears_registered_message_types(self, reset_protocol) -> None:
        register_message_types(Temp)

        assert protocol_module.decode_registered_message({"type": "temp", "value": 1}) == Temp(1)

        protocol_module._reset_for_tests()

        assert protocol_module.decode_registered_message({"type": "temp", "value": 1}) is None


class TestMessageHandlerContext:
    def test_get_and_set_message_handler(
        self,
        reset_protocol,
    ) -> None:
        handler = MockMessageHandler()

        assert get_message_handler() is None

        set_message_handler(handler)
        assert get_message_handler() is handler

        set_message_handler(None)
        assert get_message_handler() is None


class TestListenerRegistration:
    @pytest.mark.anyio
    async def test_global_free_function_listener_receives_all_sessions(
        self,
        reset_protocol,
    ) -> None:
        received: list[tuple[MessageHandlerProtocol, int]] = []

        @listen(Ping)
        async def on_ping(
            message_handler: MessageHandlerProtocol,
            message: Ping,
        ) -> None:
            received.append((message_handler, message.value))

        first = MockMessageHandler()
        second = MockMessageHandler()

        await dispatch(first, Ping(1))
        await dispatch(second, Ping(2))

        assert received == [(first, 1), (second, 2)]

    @pytest.mark.anyio
    async def test_session_scoped_free_function_listener_receives_only_own_handler(
        self,
        reset_protocol,
    ) -> None:
        received: list[tuple[MessageHandlerProtocol, int]] = []
        first = MockMessageHandler()
        second = MockMessageHandler()

        set_message_handler(first)
        try:

            @listen(Ping)
            async def on_ping(
                message_handler: MessageHandlerProtocol,
                message: Ping,
            ) -> None:
                received.append((message_handler, message.value))
        finally:
            set_message_handler(None)

        await dispatch(first, Ping(1))
        await dispatch(second, Ping(2))

        assert received == [(first, 1)]

    @pytest.mark.anyio
    async def test_duplicate_registration_is_idempotent_within_scope(
        self,
        reset_protocol,
    ) -> None:
        received: list[int] = []

        async def on_ping(message_handler: MessageHandlerProtocol, message: Ping) -> None:
            del message_handler
            received.append(message.value)

        decorated = listen(Ping)(on_ping)
        listen(Ping)(decorated)

        await dispatch(MockMessageHandler(), Ping(3))

        assert received == [3]

    @pytest.mark.anyio
    async def test_dispatch_invokes_global_then_session_scoped_listeners_in_order(
        self,
        reset_protocol,
    ) -> None:
        calls: list[str] = []
        handler = MockMessageHandler()

        @listen(Ping)
        async def global_listener(
            message_handler: MessageHandlerProtocol,
            message: Ping,
        ) -> None:
            del message_handler
            calls.append(f"global:{message.value}")

        set_message_handler(handler)
        try:

            @listen(Ping)
            async def session_listener(
                message_handler: MessageHandlerProtocol,
                message: Ping,
            ) -> None:
                del message_handler
                calls.append(f"session:{message.value}")
        finally:
            set_message_handler(None)

        await dispatch(handler, Ping(4))

        assert calls == ["global:4", "session:4"]

    @pytest.mark.anyio
    async def test_dispatch_uses_listener_snapshots_when_listeners_unregister(
        self,
        reset_protocol,
    ) -> None:
        calls: list[str] = []

        async def first(message_handler: MessageHandlerProtocol, message: Ping) -> None:
            del message_handler, message
            calls.append("first")
            protocol_module._unregister_listener(Ping, first, None)

        async def second(message_handler: MessageHandlerProtocol, message: Ping) -> None:
            del message_handler, message
            calls.append("second")

        listen(Ping)(first)
        listen(Ping)(second)

        await dispatch(MockMessageHandler(), Ping(8))

        assert calls == ["first", "second"]


class TestMessageHandler:
    @pytest.mark.anyio
    async def test_message_handler_auto_registers_bound_methods_against_active_handler(
        self,
        reset_protocol,
    ) -> None:
        received: list[tuple[MessageHandlerProtocol, int]] = []
        handler = MockMessageHandler()

        class PingListener(MessageHandler):
            @listen(Ping)
            async def on_ping(
                self,
                message_handler: MessageHandlerProtocol,
                message: Ping,
            ) -> None:
                del self
                received.append((message_handler, message.value))

        set_message_handler(handler)
        try:
            PingListener()
        finally:
            set_message_handler(None)

        await dispatch(handler, Ping(5))

        assert received == [(handler, 5)]

    @pytest.mark.anyio
    async def test_message_handler_does_not_auto_register_without_active_handler(
        self,
        reset_protocol,
    ) -> None:
        received: list[int] = []
        handler = MockMessageHandler()

        class PingListener(MessageHandler):
            @listen(Ping)
            async def on_ping(
                self,
                message_handler: MessageHandlerProtocol,
                message: Ping,
            ) -> None:
                del self, message_handler
                received.append(message.value)

        listener = PingListener()

        await dispatch(handler, Ping(9))

        assert received == []

        listener.register_message_listeners(handler)
        await dispatch(handler, Ping(10))

        assert received == [10]

    @pytest.mark.anyio
    async def test_unregister_message_listeners_detaches_bound_methods(
        self,
        reset_protocol,
    ) -> None:
        received: list[int] = []
        handler = MockMessageHandler()

        class PingListener(MessageHandler):
            @listen(Ping)
            async def on_ping(
                self,
                message_handler: MessageHandlerProtocol,
                message: Ping,
            ) -> None:
                del self, message_handler
                received.append(message.value)

        set_message_handler(handler)
        try:
            listener = PingListener()
        finally:
            set_message_handler(None)

        await dispatch(handler, Ping(11))
        listener.unregister_message_listeners()
        await dispatch(handler, Ping(12))

        assert received == [11]


class TestStatefulMessageHandlerMixin:
    @pytest.mark.anyio
    async def test_stateful_mixin_registers_on_mount_and_unregisters_on_unmount(
        self,
        reset_protocol,
    ) -> None:
        received: list[int] = []
        show_state = True
        handler = MockMessageHandler()

        @component
        def App() -> None:
            nonlocal show_state
            if show_state:
                with PingState():
                    pass

        class PingState(StatefulMessageHandlerMixin, Stateful):
            @listen(Ping)
            async def on_ping(
                self,
                message_handler: MessageHandlerProtocol,
                message: Ping,
            ) -> None:
                del self, message_handler
                received.append(message.value)

        session = RenderSession(App)

        set_message_handler(handler)
        try:
            render(session)
            await dispatch(handler, Ping(13))

            show_state = False
            assert session.root_element_id is not None
            session.dirty.mark(session.root_element_id)
            render(session)
            await dispatch(handler, Ping(14))
        finally:
            set_message_handler(None)

        assert received == [13]


class TestSend:
    @pytest.mark.anyio
    async def test_send_enqueues_to_active_handler_queue(self, reset_protocol) -> None:
        handler = MockMessageHandler()
        set_message_handler(handler)

        try:
            await send(Ping(6))
        finally:
            set_message_handler(None)

        queued = await asyncio.wait_for(handler.message_send_queue.get(), timeout=1.0)
        assert queued == Ping(6)

    @pytest.mark.anyio
    async def test_send_raises_without_active_handler(self, reset_protocol) -> None:
        with pytest.raises(RuntimeError, match="No active message handler"):
            await send(Ping(7))
