"""JS global proxy demo application."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from trellis import App, Stateful, component, js_global, js_method, js_property, js_proxy
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme
from trellis.registry import ExportKind, registry

registry.register(
    "js-global-demo-callbacks",
    base_path=Path(__file__).parent.resolve() / "client",
    exports=[
        ("invokeCallback", ExportKind.FUNCTION, "callback_helpers.ts"),
    ],
)


@js_global("window.localStorage")
class LocalStorage:
    @js_method(name="getItem")
    async def get_item(self, key: str) -> str | None:
        raise NotImplementedError

    @js_method(name="setItem")
    async def set_item(self, key: str, value: str) -> None:
        raise NotImplementedError

    @js_method(name="removeItem")
    async def remove_item(self, key: str) -> None:
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


@js_global("document")
class Document:
    title = js_property[str](writable=True)


@js_global("window")
class Window:
    demo_flag = js_property[str](name="__trellisProxyDemoFlag", writable=True, deletable=True)

    async def set_timeout(
        self,
        callback: Callable[[], None | Awaitable[None]],
        delay_ms: int,
    ) -> int:
        raise NotImplementedError


local_storage = LocalStorage()
encode_uri_component = EncodeURIComponent()
clipboard = Clipboard()
document = Document()
window = Window()


@js_proxy
async def invoke_callback(
    callback: Callable[[int], int | Awaitable[int]],
    value: int,
) -> int:
    raise NotImplementedError


Status = Literal["success", "error", "warning", "pending", "info"]
_STORAGE_KEY = "js-global-demo.theme"
_STORAGE_VALUE = "dark"
_ENCODE_INPUT = "hello world"
_CLIPBOARD_TEXT = "copied from js_global demo"
_TITLE_VALUE = "JS Global Demo Title"
_FLAG_VALUE = "demo-flag"
_TIMEOUT_DELAY_MS = 50
_CALLBACK_INPUT = 3


@dataclass
class DemoState(Stateful):
    storage_status: Status = "info"
    storage_message: str = "No localStorage action yet."
    encode_status: Status = "info"
    encode_message: str = "Ready to encode a value."
    clipboard_status: Status = "info"
    clipboard_message: str = "Ready to use navigator.clipboard."
    title_status: Status = "info"
    title_message: str = "Ready to read and set document.title."
    flag_status: Status = "info"
    flag_message: str = "Ready to manage window.__trellisProxyDemoFlag."
    timeout_status: Status = "info"
    timeout_message: str = "Ready to call window.setTimeout with a Python callback."
    callback_status: Status = "info"
    callback_message: str = "Ready to pass Python callbacks into a bundled JS helper."

    def complete_timeout(self) -> None:
        self.timeout_status = "success"
        self.timeout_message = "Timeout callback fired."

    def return_sync_value(self, value: int) -> int:
        return value + 1

    async def add_async_value(self, value: int) -> int:
        return value + 10

    async def fail_async_value(self, value: int) -> int:
        raise RuntimeError(f"async callback failed for {value}")


def _button_style(primary: bool) -> dict[str, str | int | float]:
    if primary:
        return {
            "backgroundColor": theme.accent_primary,
            "color": "#fff",
            "border": "none",
            "borderRadius": "8px",
            "padding": "10px 16px",
            "cursor": "pointer",
            "fontSize": "14px",
            "fontWeight": "600",
        }

    return {
        "backgroundColor": "transparent",
        "color": theme.text_primary,
        "border": f"1px solid {theme.border_default}",
        "borderRadius": "8px",
        "padding": "10px 16px",
        "cursor": "pointer",
        "fontSize": "14px",
        "fontWeight": "600",
    }


@component
def JsGlobalDemo() -> None:
    """Demonstrate browser global object and function proxies."""
    state = DemoState()

    async def handle_write(_event: object | None = None) -> None:
        state.storage_status = "pending"
        state.storage_message = "Writing localStorage value..."
        try:
            await local_storage.set_item(_STORAGE_KEY, _STORAGE_VALUE)
        except RuntimeError as error:
            state.storage_status = "error"
            state.storage_message = str(error)
        else:
            state.storage_status = "success"
            state.storage_message = f"Stored {_STORAGE_KEY}={_STORAGE_VALUE}"

    async def handle_read(_event: object | None = None) -> None:
        state.storage_status = "pending"
        state.storage_message = "Reading localStorage value..."
        try:
            value = await local_storage.get_item(_STORAGE_KEY)
        except RuntimeError as error:
            state.storage_status = "error"
            state.storage_message = str(error)
        else:
            state.storage_status = "success"
            state.storage_message = (
                f"Current value: {value}" if value is not None else "Current value: <missing>"
            )

    async def handle_clear(_event: object | None = None) -> None:
        state.storage_status = "pending"
        state.storage_message = "Clearing localStorage value..."
        try:
            await local_storage.remove_item(_STORAGE_KEY)
        except RuntimeError as error:
            state.storage_status = "error"
            state.storage_message = str(error)
        else:
            state.storage_status = "success"
            state.storage_message = "Storage cleared."

    async def handle_encode(_event: object | None = None) -> None:
        state.encode_status = "pending"
        state.encode_message = "Encoding value..."
        try:
            encoded = await encode_uri_component.encode(_ENCODE_INPUT)
        except RuntimeError as error:
            state.encode_status = "error"
            state.encode_message = str(error)
        else:
            state.encode_status = "success"
            state.encode_message = f"{_ENCODE_INPUT} -> {encoded}"

    async def handle_clipboard_write(_event: object | None = None) -> None:
        state.clipboard_status = "pending"
        state.clipboard_message = "Writing clipboard text..."
        try:
            await clipboard.write_text(_CLIPBOARD_TEXT)
        except RuntimeError as error:
            state.clipboard_status = "error"
            state.clipboard_message = str(error)
        else:
            state.clipboard_status = "success"
            state.clipboard_message = f"Copied: {_CLIPBOARD_TEXT}"

    async def handle_clipboard_read(_event: object | None = None) -> None:
        state.clipboard_status = "pending"
        state.clipboard_message = "Reading clipboard text..."
        try:
            text = await clipboard.read_text()
        except RuntimeError as error:
            state.clipboard_status = "error"
            state.clipboard_message = str(error)
        else:
            state.clipboard_status = "success"
            state.clipboard_message = f"Clipboard: {text}"

    async def handle_title_read(_event: object | None = None) -> None:
        state.title_status = "pending"
        state.title_message = "Reading document.title..."
        try:
            value = await document.title.get()
        except RuntimeError as error:
            state.title_status = "error"
            state.title_message = str(error)
        else:
            state.title_status = "success"
            state.title_message = f"Current title: {value}"

    async def handle_title_set(_event: object | None = None) -> None:
        state.title_status = "pending"
        state.title_message = "Setting document.title..."
        try:
            await document.title.set(_TITLE_VALUE)
        except RuntimeError as error:
            state.title_status = "error"
            state.title_message = str(error)
        else:
            state.title_status = "success"
            state.title_message = f"Updated title: {_TITLE_VALUE}"

    async def handle_flag_read(_event: object | None = None) -> None:
        state.flag_status = "pending"
        state.flag_message = "Reading window.__trellisProxyDemoFlag..."
        try:
            value = await window.demo_flag.get()
        except RuntimeError as error:
            state.flag_status = "error"
            state.flag_message = str(error)
        else:
            state.flag_status = "success"
            state.flag_message = (
                f"Current flag: {value}" if value is not None else "Current flag: <missing>"
            )

    async def handle_flag_set(_event: object | None = None) -> None:
        state.flag_status = "pending"
        state.flag_message = "Setting window.__trellisProxyDemoFlag..."
        try:
            await window.demo_flag.set(_FLAG_VALUE)
        except RuntimeError as error:
            state.flag_status = "error"
            state.flag_message = str(error)
        else:
            state.flag_status = "success"
            state.flag_message = f"Stored flag: {_FLAG_VALUE}"

    async def handle_flag_delete(_event: object | None = None) -> None:
        state.flag_status = "pending"
        state.flag_message = "Deleting window.__trellisProxyDemoFlag..."
        try:
            await window.demo_flag.delete()
        except RuntimeError as error:
            state.flag_status = "error"
            state.flag_message = str(error)
        else:
            state.flag_status = "success"
            state.flag_message = "Flag deleted."

    async def handle_timeout_callback(_event: object | None = None) -> None:
        state.timeout_status = "pending"
        state.timeout_message = f"Waiting {_TIMEOUT_DELAY_MS}ms for timeout callback..."
        try:
            await window.set_timeout(state.complete_timeout, _TIMEOUT_DELAY_MS)
        except RuntimeError as error:
            state.timeout_status = "error"
            state.timeout_message = str(error)

    async def handle_callback_success(_event: object | None = None) -> None:
        state.callback_status = "pending"
        state.callback_message = "Calling invoke_callback() with an async Python callback..."
        try:
            result = await invoke_callback(state.add_async_value, _CALLBACK_INPUT)
        except RuntimeError as error:
            state.callback_status = "error"
            state.callback_message = str(error)
        else:
            state.callback_status = "success"
            state.callback_message = f"Callback result: {result}"

    async def handle_callback_sync_failure(_event: object | None = None) -> None:
        state.callback_status = "pending"
        state.callback_message = "Calling invoke_callback() with a sync return value..."
        try:
            await invoke_callback(state.return_sync_value, _CALLBACK_INPUT)
        except RuntimeError as error:
            state.callback_status = "error"
            state.callback_message = str(error)
        else:
            state.callback_status = "success"
            state.callback_message = "Unexpected success"

    async def handle_callback_async_failure(_event: object | None = None) -> None:
        state.callback_status = "pending"
        state.callback_message = "Calling invoke_callback() with a failing async callback..."
        try:
            await invoke_callback(state.fail_async_value, _CALLBACK_INPUT)
        except RuntimeError as error:
            state.callback_status = "error"
            state.callback_message = str(error)
        else:
            state.callback_status = "success"
            state.callback_message = "Unexpected success"

    with w.Column(
        padding=24,
        gap=16,
        align="center",
        justify="center",
        style={"minHeight": "100vh", "backgroundColor": theme.bg_page},
    ):
        with w.Card(
            width=520,
            padding=24,
            style={"backgroundColor": theme.bg_surface},
        ):
            with w.Column(gap=16):
                w.Heading(text="JS Global Demo", level=2)
                w.Label(
                    text="Call browser globals from Python through the JS proxy transport.",
                    color=theme.text_secondary,
                )

                with w.Column(gap=8):
                    w.Label(text="document.title", font_weight=600)
                    w.StatusIndicator(
                        status=state.title_status,
                        label=state.title_status.title(),
                    )
                    w.Label(text=state.title_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Read title", on_click=handle_title_read, style=_button_style(True)
                        )
                        h.HtmlButton(
                            "Set demo title",
                            on_click=handle_title_set,
                            style=_button_style(False),
                        )

                with w.Column(gap=8):
                    w.Label(text="window.__trellisProxyDemoFlag", font_weight=600)
                    w.StatusIndicator(
                        status=state.flag_status,
                        label=state.flag_status.title(),
                    )
                    w.Label(text=state.flag_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Read flag", on_click=handle_flag_read, style=_button_style(True)
                        )
                        h.HtmlButton(
                            "Set flag", on_click=handle_flag_set, style=_button_style(False)
                        )
                        h.HtmlButton(
                            "Delete flag", on_click=handle_flag_delete, style=_button_style(False)
                        )

                with w.Column(gap=8):
                    w.Label(text="localStorage", font_weight=600)
                    w.StatusIndicator(
                        status=state.storage_status,
                        label=state.storage_status.title(),
                    )
                    w.Label(text=state.storage_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Write theme", on_click=handle_write, style=_button_style(True)
                        )
                        h.HtmlButton("Read theme", on_click=handle_read, style=_button_style(False))
                        h.HtmlButton(
                            "Clear theme", on_click=handle_clear, style=_button_style(False)
                        )

                with w.Column(gap=8):
                    w.Label(text="encodeURIComponent", font_weight=600)
                    w.StatusIndicator(
                        status=state.encode_status,
                        label=state.encode_status.title(),
                    )
                    w.Label(text=state.encode_message)
                    h.HtmlButton(
                        "Encode hello world",
                        on_click=handle_encode,
                        style=_button_style(True),
                    )

                with w.Column(gap=8):
                    w.Label(text="navigator.clipboard", font_weight=600)
                    w.StatusIndicator(
                        status=state.clipboard_status,
                        label=state.clipboard_status.title(),
                    )
                    w.Label(text=state.clipboard_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Copy demo text",
                            on_click=handle_clipboard_write,
                            style=_button_style(True),
                        )
                        h.HtmlButton(
                            "Read clipboard",
                            on_click=handle_clipboard_read,
                            style=_button_style(False),
                        )

                with w.Column(gap=8):
                    w.Label(text="window.setTimeout", font_weight=600)
                    w.StatusIndicator(
                        status=state.timeout_status,
                        label=state.timeout_status.title(),
                    )
                    w.Label(text=state.timeout_message)
                    h.HtmlButton(
                        "Trigger timeout callback",
                        on_click=handle_timeout_callback,
                        style=_button_style(True),
                    )

                with w.Column(gap=8):
                    w.Label(text="Bundled callback helper", font_weight=600)
                    w.StatusIndicator(
                        status=state.callback_status,
                        label=state.callback_status.title(),
                    )
                    w.Label(text=state.callback_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Run async callback",
                            on_click=handle_callback_success,
                            style=_button_style(True),
                        )
                        h.HtmlButton(
                            "Sync callback error",
                            on_click=handle_callback_sync_failure,
                            style=_button_style(False),
                        )
                        h.HtmlButton(
                            "Async callback error",
                            on_click=handle_callback_async_failure,
                            style=_button_style(False),
                        )


app = App(JsGlobalDemo)
