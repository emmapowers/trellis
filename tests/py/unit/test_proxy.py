"""Unit tests for JS proxy transport helpers."""

from __future__ import annotations

import asyncio
import typing as tp

import pytest

import trellis.core.proxy as proxy_module
from trellis.core.components.composition import CompositionComponent
from trellis.core.proxy import js_method, js_proxy
from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import Message, ProxyCall


class RecordingTransport:
    """Simple transport stub for JS proxy tests."""

    def __init__(
        self,
        result: tp.Any = None,
        error: BaseException | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, str, list[tp.Any]]] = []

    async def call_proxy(
        self,
        proxy_id: str,
        method: str,
        args: list[tp.Any],
    ) -> tp.Any:
        self.calls.append((proxy_id, method, args))
        if self.error is not None:
            raise self.error
        return self.result


@js_proxy
class DemoApi:
    async def get_message(self, name: str) -> str:
        raise NotImplementedError

    @js_method(name="failNow")
    async def fail_now(self) -> str:
        raise NotImplementedError


@js_proxy(name="demo_api")
class NamedDemoApi:
    async def greet(self, name: str) -> str:
        raise NotImplementedError


def _identity_wrapper(
    component: CompositionComponent,
    _system_theme: str,
    _theme_mode: str | None,
) -> CompositionComponent:
    return component


class RecordingMessageHandler(MessageHandler):
    def __init__(self) -> None:
        super().__init__(
            CompositionComponent(name="Root", render_func=lambda: None),
            _identity_wrapper,
        )
        self.sent_messages: list[Message] = []
        self.raise_on_send: BaseException | None = None

    async def send_message(self, msg: Message) -> None:
        if self.raise_on_send is not None:
            raise self.raise_on_send
        self.sent_messages.append(msg)

    async def receive_message(self) -> Message:
        raise NotImplementedError


class TestJsProxyObjects:
    def test_decorated_object_proxy_uses_exact_class_name_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Object proxies default their target name to the exact class name."""
        transport = RecordingTransport(result="hello Emma")
        proxy = DemoApi()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(proxy.get_message("Emma"))

        assert result == "hello Emma"
        assert transport.calls == [("DemoApi", "getMessage", ["Emma"])]

    def test_decorated_object_proxy_name_override_is_used(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """name= overrides the object proxy target name."""
        transport = RecordingTransport(result="hello Emma")
        proxy = NamedDemoApi()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(proxy.greet("Emma"))

        assert result == "hello Emma"
        assert transport.calls == [("demo_api", "greet", ["Emma"])]

    def test_js_method_override_changes_the_js_method_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """@js_method(name=...) overrides the JS method name."""
        transport = RecordingTransport(error=RuntimeError("bad input"))
        proxy = DemoApi()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        with pytest.raises(RuntimeError, match="bad input"):
            asyncio.run(proxy.fail_now())

        assert transport.calls == [("DemoApi", "failNow", [])]

    def test_object_proxy_rejects_keyword_arguments(self) -> None:
        """Object proxy methods reject keyword arguments."""
        proxy = DemoApi()

        with pytest.raises(TypeError, match="do not accept keyword arguments"):
            asyncio.run(proxy.get_message(name="Emma"))

    def test_object_proxy_resolves_transport_from_callback_context(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Object proxies can resolve transport lazily from callback context."""
        transport = RecordingTransport(result="hello Emma")
        fake_session = type("FakeSession", (), {"proxy_transport": transport})()
        proxy = DemoApi()

        monkeypatch.setattr(proxy_module, "get_active_session", lambda: None)
        monkeypatch.setattr(proxy_module, "get_callback_node_id", lambda: "node-1")
        monkeypatch.setattr(proxy_module, "get_callback_session", lambda: fake_session)

        result = asyncio.run(proxy.get_message("Emma"))

        assert result == "hello Emma"
        assert transport.calls == [("DemoApi", "getMessage", ["Emma"])]

    def test_object_proxy_without_transport_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Object proxies raise when no transport can be resolved."""
        proxy = DemoApi()

        monkeypatch.setattr(proxy_module, "get_active_session", lambda: None)
        monkeypatch.setattr(proxy_module, "get_callback_node_id", lambda: None)

        with pytest.raises(RuntimeError, match="Cannot call JS proxy outside"):
            asyncio.run(proxy.get_message("Emma"))

    def test_non_async_public_methods_are_rejected(self) -> None:
        """Decorated object classes reject non-async public methods."""

        with pytest.raises(TypeError, match="must be async"):

            @js_proxy
            class InvalidApi:
                def greet(self, name: str) -> str:
                    return name

    def test_public_non_method_members_are_rejected(self) -> None:
        """Decorated object classes reject public non-method members."""

        with pytest.raises(TypeError, match="public members"):

            @js_proxy
            class InvalidApi:
                version = "1"

                async def greet(self, name: str) -> str:
                    raise NotImplementedError

    def test_duplicate_resolved_js_method_names_are_rejected(self) -> None:
        """Decorated object classes reject duplicate resolved JS method names."""

        with pytest.raises(ValueError, match="Duplicate JS proxy method name"):

            @js_proxy
            class InvalidApi:
                async def get_message(self, name: str) -> str:
                    raise NotImplementedError

                @js_method(name="getMessage")
                async def other_name(self, name: str) -> str:
                    raise NotImplementedError

    def test_js_method_outside_js_proxy_class_is_rejected(self) -> None:
        """@js_method is only valid inside @js_proxy classes."""

        with pytest.raises(TypeError, match="only be used on methods"):

            @js_method(name="test")
            async def invalid() -> None:
                raise NotImplementedError


class TestMessageHandlerProxyCalls:
    def test_call_proxy_cleans_up_pending_future_on_send_failure(self) -> None:
        """call_proxy removes pending requests when send_message fails."""
        handler = RecordingMessageHandler()
        handler.raise_on_send = RuntimeError("send failed")

        with pytest.raises(RuntimeError, match="send failed"):
            asyncio.run(handler.call_proxy("demo_api", "greet", ["Emma"]))

        assert handler._pending_proxy_calls == {}

    def test_call_proxy_cleans_up_pending_future_on_cancellation(self) -> None:
        """call_proxy removes pending requests when the caller cancels."""
        handler = RecordingMessageHandler()

        async def test() -> None:
            task = asyncio.create_task(handler.call_proxy("demo_api", "greet", ["Emma"]))
            await asyncio.sleep(0)

            assert len(handler.sent_messages) == 1
            message = handler.sent_messages[0]
            assert isinstance(message, ProxyCall)

            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

            assert handler._pending_proxy_calls == {}

        asyncio.run(test())
