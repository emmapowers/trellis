"""Unit tests for JS proxy transport helpers."""

from __future__ import annotations

import asyncio
import typing as tp

import pytest

import trellis.core.proxy as proxy_module
from trellis.core.proxy import JsProxy, js_object


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
