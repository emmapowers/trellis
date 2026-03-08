"""Unit tests for JS proxy transport helpers."""

from __future__ import annotations

import asyncio
import typing as tp

import pytest

import trellis.core.proxy as proxy_module
import trellis.core.proxy_values as proxy_values_module
from trellis.core.components.composition import CompositionComponent
from trellis.core.proxy import js_global, js_method, js_property, js_proxy, js_release
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import Message, ProxyRequest, ProxyResponse


class RecordingTransport:
    """Simple transport stub for JS proxy tests."""

    def __init__(
        self,
        result: tp.Any = None,
        error: BaseException | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.session = RenderSession(CompositionComponent(name="Root", render_func=lambda: None))
        self.calls: list[
            tuple[str, str, str | None, list[tp.Any], tp.Any, str, bool]
        ] = []

    async def request_proxy(
        self,
        proxy_id: str,
        operation: str,
        member: str | None,
        args: list[tp.Any] | None = None,
        value: tp.Any = None,
        *,
        return_mode: str = "value",
        allow_null: bool = True,
    ) -> tp.Any:
        self.calls.append((proxy_id, operation, member, args or [], value, return_mode, allow_null))
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


@js_proxy
async def invoke_callback(callback: tp.Callable[[int], tp.Any], value: int) -> int:
    raise NotImplementedError


@js_global("window.localStorage")
class LocalStorage:
    @js_method(name="getItem")
    async def get_item(self, key: str) -> str | None:
        raise NotImplementedError

    @js_method(name="setItem")
    async def set_item(self, key: str, value: str) -> None:
        raise NotImplementedError


@js_global("document")
class Document:
    title = js_property[str](writable=True)


@js_global("window")
class WindowGlobals:
    demo_flag = js_property[str](
        name="__trellisProxyDemoFlag",
        writable=True,
        deletable=True,
    )


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
        assert transport.calls == [("DemoApi", "call", "getMessage", ["Emma"], None, "value", True)]

    def test_decorated_object_proxy_name_override_is_used(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """name= overrides the object proxy target name."""
        transport = RecordingTransport(result="hello Emma")
        proxy = NamedDemoApi()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(proxy.greet("Emma"))

        assert result == "hello Emma"
        assert transport.calls == [("demo_api", "call", "greet", ["Emma"], None, "value", True)]

    def test_js_method_override_changes_the_js_method_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """@js_method(name=...) overrides the JS method name."""
        transport = RecordingTransport(error=RuntimeError("bad input"))
        proxy = DemoApi()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        with pytest.raises(RuntimeError, match="bad input"):
            asyncio.run(proxy.fail_now())

        assert transport.calls == [("DemoApi", "call", "failNow", [], None, "value", True)]

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
        assert transport.calls == [("DemoApi", "call", "getMessage", ["Emma"], None, "value", True)]

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

        with pytest.raises(TypeError, match="js_property descriptors"):

            @js_proxy
            class InvalidApi:
                version = "1"

                async def greet(self, name: str) -> str:
                    raise NotImplementedError

    def test_duplicate_resolved_js_method_names_are_rejected(self) -> None:
        """Decorated object classes reject duplicate resolved JS method names."""

        with pytest.raises(ValueError, match="Duplicate JS proxy member name"):

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
        assert transport.calls == [("formatNow", "call", None, [3], None, "value", True)]

    def test_decorated_function_proxy_name_override_is_used(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """name= overrides the function proxy target name exactly."""
        transport = RecordingTransport(result="value: 3")

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(format_exactly(3))

        assert result == "value: 3"
        assert transport.calls == [("formatExactly", "call", None, [3], None, "value", True)]

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

    def test_function_proxy_serializes_callback_arguments(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Function proxies serialize callback arguments as proxy callback sentinels."""
        transport = RecordingTransport(result=4)

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        fake_session = type(
            "FakeSession",
            (),
            {
                "is_executing": lambda self: True,
                "current_element_id": "node-1",
                "register_proxy_callback": lambda self, callback, node_id: "callback-1",
            },
        )()
        monkeypatch.setattr(proxy_module, "get_active_session", lambda: fake_session)
        monkeypatch.setattr(proxy_values_module, "get_active_session", lambda: fake_session)
        monkeypatch.setattr(proxy_values_module, "get_callback_node_id", lambda: None)

        result = asyncio.run(invoke_callback(lambda value: None, 3))

        assert result == 4
        assert transport.calls == [
            (
                "invokeCallback",
                "call",
                None,
                [{"__proxy_callback__": "callback-1"}, 3],
                None,
                "value",
                True,
            )
        ]


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
        assert transport.calls == [
            ("__global__:window.localStorage", "call", "getItem", ["theme"], None, "value", True)
        ]

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

        with pytest.raises(TypeError, match="js_property descriptors"):

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
            (
                "__global__:globalThis.encodeURIComponent",
                "call",
                None,
                ["hello world"],
                None,
                "value",
                True,
            )
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

        assert transport.calls == [
            (
                "__global__:navigator.clipboard",
                "call",
                "writeText",
                ["copied text"],
                None,
                "value",
                True,
            )
        ]

    def test_clipboard_wrapper_uses_read_text_method_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clipboard read wrappers call readText on the clipboard object."""
        transport = RecordingTransport(result="copied text")
        clipboard = Clipboard()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(clipboard.read_text())

        assert result == "copied text"
        assert transport.calls == [
            ("__global__:navigator.clipboard", "call", "readText", [], None, "value", True)
        ]

    def test_clipboard_errors_are_raised_as_runtime_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clipboard proxy failures surface as RuntimeError."""
        transport = RecordingTransport(error=RuntimeError("clipboard blocked"))
        clipboard = Clipboard()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        with pytest.raises(RuntimeError, match="clipboard blocked"):
            asyncio.run(clipboard.write_text("copied text"))

        assert transport.calls == [
            (
                "__global__:navigator.clipboard",
                "call",
                "writeText",
                ["copied text"],
                None,
                "value",
                True,
            )
        ]


class TestJsProperties:
    def test_property_get_uses_default_name_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Property get requests use snake_case to camelCase by default."""
        transport = RecordingTransport(result="Original title")
        document = Document()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(document.title.get())

        assert result == "Original title"
        assert transport.calls == [("__global__:document", "get", "title", [], None, "value", True)]

    def test_property_name_override_is_used(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Property name overrides apply to property requests."""
        transport = RecordingTransport(result="flag")
        window_globals = WindowGlobals()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(window_globals.demo_flag.get())

        assert result == "flag"
        assert transport.calls == [
            ("__global__:window", "get", "__trellisProxyDemoFlag", [], None, "value", True)
        ]

    def test_property_set_returns_bool(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Writable properties send a set request and return the JS boolean result."""
        transport = RecordingTransport(result=True)
        document = Document()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(document.title.set("New title"))

        assert result is True
        assert transport.calls == [
            ("__global__:document", "set", "title", [], "New title", "value", True)
        ]

    def test_property_delete_returns_bool(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deletable properties send a delete request and return the JS boolean result."""
        transport = RecordingTransport(result=True)
        window_globals = WindowGlobals()

        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)
        result = asyncio.run(window_globals.demo_flag.delete())

        assert result is True
        assert transport.calls == [
            ("__global__:window", "delete", "__trellisProxyDemoFlag", [], None, "value", True)
        ]

    def test_non_writable_properties_reject_set_locally(self) -> None:
        """Read-only properties fail before transport."""

        @js_global("document")
        class ReadOnlyDocument:
            title = js_property[str]()

        document = ReadOnlyDocument()

        with pytest.raises(TypeError, match="not writable"):
            asyncio.run(document.title.set("New title"))

    def test_non_deletable_properties_reject_delete_locally(self) -> None:
        """Non-deletable properties fail before transport."""

        @js_global("document")
        class NonDeletableDocument:
            title = js_property[str](writable=True)

        document = NonDeletableDocument()

        with pytest.raises(TypeError, match="not deletable"):
            asyncio.run(document.title.delete())

    def test_duplicate_property_and_method_names_are_rejected(self) -> None:
        """Classes reject duplicate resolved JS member names across methods and properties."""

        with pytest.raises(ValueError, match="Duplicate JS proxy member name"):

            @js_global("document")
            class InvalidDocument:
                title = js_property[str]()

                @js_method(name="title")
                async def fetch_title(self) -> str:
                    raise NotImplementedError

    def test_properties_are_rejected_on_callable_globals(self) -> None:
        """Callable globals cannot declare js_property descriptors."""

        with pytest.raises(TypeError, match="js_property"):

            @js_global("globalThis.encodeURIComponent", kind="function")
            class InvalidGlobal:
                value = js_property[str]()

                async def encode(self, text: str) -> str:
                    raise NotImplementedError


class TestMessageHandlerProxyRequests:
    def test_request_proxy_cleans_up_pending_future_on_send_failure(self) -> None:
        """request_proxy removes pending requests when send_message fails."""
        handler = RecordingMessageHandler()
        handler.raise_on_send = RuntimeError("send failed")

        with pytest.raises(RuntimeError, match="send failed"):
            asyncio.run(handler.request_proxy("demo_api", "call", "greet", ["Emma"]))

        assert handler._pending_proxy_requests == {}

    def test_request_proxy_cleans_up_pending_future_on_cancellation(self) -> None:
        """request_proxy removes pending requests when the caller cancels."""
        handler = RecordingMessageHandler()

        async def test() -> None:
            task = asyncio.create_task(handler.request_proxy("demo_api", "call", "greet", ["Emma"]))
            await asyncio.sleep(0)

            assert len(handler.sent_messages) == 1
            message = handler.sent_messages[0]
            assert isinstance(message, ProxyRequest)

            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

            assert handler._pending_proxy_requests == {}

        asyncio.run(test())


class TestReturnedProxyHandles:
    def test_dynamic_proxy_classes_reject_direct_instantiation(self) -> None:
        """dynamic=True proxy classes are return-only and cannot be constructed directly."""

        @js_proxy(dynamic=True)
        class CounterHandle:
            async def increment(self) -> int:
                raise NotImplementedError

        with pytest.raises(TypeError, match="cannot be instantiated directly"):
            CounterHandle()

    def test_dynamic_proxy_classes_reject_name_override(self) -> None:
        """dynamic=True proxies do not allow static target names."""

        with pytest.raises(TypeError, match="name=.*dynamic=True"):

            @js_proxy(name="CounterHandle", dynamic=True)
            class CounterHandle:
                async def increment(self) -> int:
                    raise NotImplementedError

    def test_function_returning_dynamic_proxy_requests_proxy_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Functions annotated with a dynamic proxy return request proxy mode."""

        @js_proxy(dynamic=True)
        class CounterHandle:
            async def increment(self) -> int:
                raise NotImplementedError

        @js_proxy
        async def create_counter(label: str) -> CounterHandle:
            raise NotImplementedError

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        result = asyncio.run(create_counter("demo"))

        assert isinstance(result, CounterHandle)
        assert transport.calls == [
            ("createCounter", "call", None, ["demo"], None, "proxy", False)
        ]

    def test_method_returning_optional_dynamic_proxy_allows_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Object methods returning optional proxies request proxy mode with allow_null."""

        @js_proxy(dynamic=True)
        class HtmlElement:
            async def focus(self) -> None:
                raise NotImplementedError

        @js_global("document")
        class DocumentProxy:
            async def query_selector(self, selector: str) -> HtmlElement | None:
                raise NotImplementedError

        transport = RecordingTransport(result=None)
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        result = asyncio.run(DocumentProxy().query_selector("body"))

        assert result is None
        assert transport.calls == [
            ("__global__:document", "call", "querySelector", ["body"], None, "proxy", True)
        ]

    def test_repeated_handle_id_reuses_same_python_object(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The same returned handle ID maps to stable Python identity within a session."""

        @js_proxy(dynamic=True)
        class CounterHandle:
            async def increment(self) -> int:
                raise NotImplementedError

        @js_proxy
        async def create_counter(label: str) -> CounterHandle:
            raise NotImplementedError

        handle_value = {proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"}
        transport = RecordingTransport(result=handle_value)
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        first = asyncio.run(create_counter("demo"))
        second = asyncio.run(create_counter("demo"))

        assert first is second

    def test_js_release_sends_release_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """js_release sends a release request for dynamic handles."""

        @js_proxy(dynamic=True)
        class CounterHandle:
            async def increment(self) -> int:
                raise NotImplementedError

        @js_proxy
        async def create_counter(label: str) -> CounterHandle:
            raise NotImplementedError

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        handle = asyncio.run(create_counter("demo"))
        asyncio.run(js_release(handle))

        assert transport.calls[-1] == (
            "__handle__:counter-1",
            "release",
            None,
            [],
            None,
            "value",
            True,
        )

    def test_js_release_is_idempotent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Releasing the same handle twice is a no-op after the first request."""

        @js_proxy(dynamic=True)
        class CounterHandle:
            async def increment(self) -> int:
                raise NotImplementedError

        @js_proxy
        async def create_counter(label: str) -> CounterHandle:
            raise NotImplementedError

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        handle = asyncio.run(create_counter("demo"))
        asyncio.run(js_release(handle))
        asyncio.run(js_release(handle))

        release_calls = [call for call in transport.calls if call[1] == "release"]
        assert len(release_calls) == 1

    def test_released_handles_raise_on_use(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Dynamic handles reject use after release."""

        @js_proxy(dynamic=True)
        class CounterHandle:
            async def increment(self) -> int:
                raise NotImplementedError

        @js_proxy
        async def create_counter(label: str) -> CounterHandle:
            raise NotImplementedError

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:counter-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        handle = asyncio.run(create_counter("demo"))
        asyncio.run(js_release(handle))

        with pytest.raises(RuntimeError, match="has been released"):
            asyncio.run(handle.increment())

    def test_js_release_rejects_static_root_proxies(self) -> None:
        """Only returned dynamic handles may be released explicitly."""
        with pytest.raises(TypeError, match="only supports returned proxy handles"):
            asyncio.run(js_release(DemoApi()))


class TestPropertyReturnedProxyHandles:
    def test_property_get_uses_proxy_mode_for_optional_dynamic_handles(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Proxy-valued properties request proxy mode and allow null for optional handles."""

        @js_proxy(dynamic=True)
        class HtmlElement:
            async def focus(self) -> None:
                raise NotImplementedError

        @js_global("document")
        class DocumentWithBody:
            body = js_property[HtmlElement | None]()

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:body-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        result = asyncio.run(DocumentWithBody().body.get())

        assert isinstance(result, HtmlElement)
        assert transport.calls == [
            ("__global__:document", "get", "body", [], None, "proxy", True)
        ]

    def test_non_optional_proxy_valued_properties_disallow_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-optional proxy-valued properties request proxy mode without nulls."""

        @js_proxy(dynamic=True)
        class HtmlElement:
            async def focus(self) -> None:
                raise NotImplementedError

        @js_global("document")
        class DocumentRoot:
            document_element = js_property[HtmlElement](name="documentElement")

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:root-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        result = asyncio.run(DocumentRoot().document_element.get())

        assert isinstance(result, HtmlElement)
        assert transport.calls == [
            ("__global__:document", "get", "documentElement", [], None, "proxy", False)
        ]

    def test_repeated_property_gets_reuse_python_identity(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Property-returned handles reuse the same cached Python object."""

        @js_proxy(dynamic=True)
        class HtmlElement:
            async def focus(self) -> None:
                raise NotImplementedError

        @js_global("document")
        class DocumentWithBody:
            body = js_property[HtmlElement | None]()

        transport = RecordingTransport(
            result={proxy_values_module.PROXY_HANDLE_SENTINEL: "__handle__:body-1"}
        )
        monkeypatch.setattr(proxy_module, "_resolve_transport", lambda: transport)

        first = asyncio.run(DocumentWithBody().body.get())
        second = asyncio.run(DocumentWithBody().body.get())

        assert first is second

    def test_request_proxy_supports_function_targets(self) -> None:
        """request_proxy sends function invocations with a null member."""
        handler = RecordingMessageHandler()

        async def test() -> None:
            task = asyncio.create_task(handler.request_proxy("formatNow", "call", None, [3]))
            await asyncio.sleep(0)

            assert len(handler.sent_messages) == 1
            message = handler.sent_messages[0]
            assert isinstance(message, ProxyRequest)
            assert message.proxy_id == "formatNow"
            assert message.operation == "call"
            assert message.member is None
            assert message.args == [3]

            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        asyncio.run(test())
