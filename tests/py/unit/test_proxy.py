"""Unit tests for JS proxy transport helpers."""

from __future__ import annotations

import asyncio
import typing as tp

import pytest

import trellis.core.proxy as proxy_module
from trellis.core.components.composition import CompositionComponent
from trellis.core.proxy import JsProxy, js_object
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


class DemoApi(JsProxy):
    async def get_message(self, name: str) -> str: ...

    async def fail(self) -> str: ...


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


class TestJsProxy:
    def test_js_proxy_calls_transport(self) -> None:
        """Proxy methods delegate to the configured transport."""
        transport = RecordingTransport(result="hello Emma")
        proxy = js_object(DemoApi, "demo_api", transport=transport)

        result = asyncio.run(proxy.get_message("Emma"))

        assert result == "hello Emma"
        assert transport.calls == [("demo_api", "getMessage", ["Emma"])]

    def test_js_proxy_raises_transport_errors(self) -> None:
        """Transport errors propagate to the caller."""
        transport = RecordingTransport(error=RuntimeError("bad input"))
        proxy = js_object(DemoApi, "demo_api", transport=transport)

        with pytest.raises(RuntimeError, match="bad input"):
            asyncio.run(proxy.fail())

    def test_js_proxy_resolves_transport_from_callback_context(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Proxy methods can resolve transport lazily from callback context."""
        transport = RecordingTransport(result="hello Emma")
        fake_session = type("FakeSession", (), {"proxy_transport": transport})()
        proxy = js_object(DemoApi, "demo_api")

        monkeypatch.setattr(proxy_module, "get_active_session", lambda: None)
        monkeypatch.setattr(proxy_module, "get_callback_node_id", lambda: "node-1")
        monkeypatch.setattr(proxy_module, "get_callback_session", lambda: fake_session)

        result = asyncio.run(proxy.get_message("Emma"))

        assert result == "hello Emma"
        assert transport.calls == [("demo_api", "getMessage", ["Emma"])]

    def test_js_proxy_without_transport_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Proxy methods raise when no transport can be resolved."""
        proxy = js_object(DemoApi, "demo_api")

        monkeypatch.setattr(proxy_module, "get_active_session", lambda: None)
        monkeypatch.setattr(proxy_module, "get_callback_node_id", lambda: None)

        with pytest.raises(RuntimeError, match="Cannot call JS proxy outside"):
            asyncio.run(proxy.get_message("Emma"))


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
