"""Unit tests for JS proxy transport helpers."""

from __future__ import annotations

import asyncio
import typing as tp

import pytest

import trellis.core.proxy as proxy_module
from trellis.core.components.composition import CompositionComponent
from trellis.core.proxy import js_global, js_method, js_proxy
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
        self.calls: list[tuple[str, str | None, list[tp.Any]]] = []

    async def call_proxy(
        self,
        proxy_id: str,
        method: str | None,
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


@js_proxy
async def format_now(value: int) -> str:
    raise NotImplementedError


@js_proxy(name="formatExactly")
async def format_exactly(value: int) -> str:
    raise NotImplementedError


@js_global("window.localStorage")
class LocalStorage:
    @js_method(name="getItem")
    async def get_item(self, key: str) -> str | None:
        raise NotImplementedError

    @js_method(name="setItem")
    async def set_item(self, key: str, value: str) -> None:
        raise NotImplementedError


@js_global("globalThis.encodeURIComponent", kind="function")
class EncodeURIComponent:
    async def encode(self, value: str) -> str:
        raise NotImplementedError


@js_global("navigator.clipboard")
class Clipboard:
    @js_method(name="writeText")
    async def write_text(self, text: str) -> None:
        raise NotImplementedError

    @js_method(name="readText")
    async def read_text(self) -> str:
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


class TestJsProxyFunctions:
    def test_decorated_function_proxy_uses_camel_case_target_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Function proxies default their target name to camelCase."""
        transport = RecordingTransport(result="value: 3")

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(format_now(3))

        assert result == "value: 3"
        assert transport.calls == [("formatNow", None, [3])]

    def test_decorated_function_proxy_name_override_is_used(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """name= overrides the function proxy target name exactly."""
        transport = RecordingTransport(result="value: 3")

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(format_exactly(3))

        assert result == "value: 3"
        assert transport.calls == [("formatExactly", None, [3])]

    def test_function_proxy_rejects_keyword_arguments(self) -> None:
        """Function proxies reject keyword arguments."""
        with pytest.raises(TypeError, match="do not accept keyword arguments"):
            asyncio.run(format_now(value=3))

    def test_non_async_functions_are_rejected(self) -> None:
        """Decorated function proxies must be async."""
        with pytest.raises(TypeError, match="async functions"):

            @js_proxy
            def invalid(value: int) -> int:
                return value


class TestJsGlobalObjects:
    def test_object_global_proxy_uses_reserved_global_proxy_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Global object proxies send calls through the reserved global ID prefix."""
        transport = RecordingTransport(result="dark")
        storage = LocalStorage()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(storage.get_item("theme"))

        assert result == "dark"
        assert transport.calls == [("__global__:window.localStorage", "getItem", ["theme"])]

    def test_object_global_proxy_rejects_keyword_arguments(self) -> None:
        """Global object proxies reject keyword arguments."""
        storage = LocalStorage()

        with pytest.raises(TypeError, match="do not accept keyword arguments"):
            asyncio.run(storage.get_item(key="theme"))

    @pytest.mark.parametrize(
        "path",
        [
            "window.localStorage",
            "navigator.clipboard",
            "globalThis.encodeURIComponent",
        ],
    )
    def test_global_paths_allow_dotted_identifier_segments(self, path: str) -> None:
        """Dotted global paths are accepted at decoration time."""

        @js_global(path)
        class ValidGlobal:
            async def ping(self) -> None:
                raise NotImplementedError

        assert ValidGlobal.__name__ == "ValidGlobal"

    @pytest.mark.parametrize(
        "path",
        [
            "",
            'window["localStorage"]',
            "window.localStorage.getItem()",
            ".window",
            "window..localStorage",
        ],
    )
    def test_invalid_global_paths_are_rejected(self, path: str) -> None:
        """Malformed global paths fail at decoration time."""

        with pytest.raises(TypeError, match="global path"):

            @js_global(path)
            class InvalidGlobal:
                async def ping(self) -> None:
                    raise NotImplementedError

    def test_non_async_object_global_methods_are_rejected(self) -> None:
        """Global object classes require async public methods."""

        with pytest.raises(TypeError, match="must be async"):

            @js_global("window.localStorage")
            class InvalidGlobal:
                def get_item(self, key: str) -> str | None:
                    return key

    def test_public_non_method_members_on_object_global_are_rejected(self) -> None:
        """Global object classes reject public data members."""

        with pytest.raises(TypeError, match="public members"):

            @js_global("window.localStorage")
            class InvalidGlobal:
                version = "1"

                async def get_item(self, key: str) -> str | None:
                    raise NotImplementedError


class TestJsGlobalFunctions:
    def test_callable_global_proxy_uses_null_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Callable globals invoke the resolved function target directly."""
        transport = RecordingTransport(result="hello%20world")
        encoder = EncodeURIComponent()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(encoder.encode("hello world"))

        assert result == "hello%20world"
        assert transport.calls == [
            ("__global__:globalThis.encodeURIComponent", None, ["hello world"])
        ]

    def test_callable_global_classes_require_exactly_one_public_async_method(self) -> None:
        """Callable globals reject classes with multiple public methods."""

        with pytest.raises(TypeError, match="exactly one public async method"):

            @js_global("globalThis.encodeURIComponent", kind="function")
            class InvalidGlobal:
                async def encode(self, value: str) -> str:
                    raise NotImplementedError

                async def decode(self, value: str) -> str:
                    raise NotImplementedError

    def test_callable_global_classes_reject_js_method_overrides(self) -> None:
        """Callable globals do not allow per-method JS name overrides."""

        with pytest.raises(TypeError, match="@js_method"):

            @js_global("globalThis.encodeURIComponent", kind="function")
            class InvalidGlobal:
                @js_method(name="encodeURIComponent")
                async def encode(self, value: str) -> str:
                    raise NotImplementedError

    def test_callable_global_classes_reject_non_async_public_methods(self) -> None:
        """Callable globals require their single public method to be async."""

        with pytest.raises(TypeError, match="must be async"):

            @js_global("globalThis.encodeURIComponent", kind="function")
            class InvalidGlobal:
                def encode(self, value: str) -> str:
                    return value


class TestJsGlobalClipboard:
    def test_clipboard_wrapper_uses_write_text_method_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clipboard wrappers map Python method names to browser clipboard methods."""
        transport = RecordingTransport(result=None)
        clipboard = Clipboard()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        asyncio.run(clipboard.write_text("copied text"))

        assert transport.calls == [("__global__:navigator.clipboard", "writeText", ["copied text"])]

    def test_clipboard_wrapper_uses_read_text_method_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clipboard read wrappers call readText on the clipboard object."""
        transport = RecordingTransport(result="copied text")
        clipboard = Clipboard()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(clipboard.read_text())

        assert result == "copied text"
        assert transport.calls == [("__global__:navigator.clipboard", "readText", [])]

    def test_clipboard_errors_are_raised_as_runtime_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clipboard proxy failures surface as RuntimeError."""
        transport = RecordingTransport(error=RuntimeError("clipboard blocked"))
        clipboard = Clipboard()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        with pytest.raises(RuntimeError, match="clipboard blocked"):
            asyncio.run(clipboard.write_text("copied text"))

        assert transport.calls == [("__global__:navigator.clipboard", "writeText", ["copied text"])]


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

    def test_call_proxy_supports_function_targets(self) -> None:
        """call_proxy sends function invocations with a null method."""
        handler = RecordingMessageHandler()

        async def test() -> None:
            task = asyncio.create_task(handler.call_proxy("formatNow", None, [3]))
            await asyncio.sleep(0)

            assert len(handler.sent_messages) == 1
            message = handler.sent_messages[0]
            assert isinstance(message, ProxyCall)
            assert message.proxy_id == "formatNow"
            assert message.method is None
            assert message.args == [3]

            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        asyncio.run(test())
