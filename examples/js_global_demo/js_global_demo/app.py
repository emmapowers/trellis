"""JS global proxy demo application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from trellis import App, Stateful, component, js_global, js_method
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme


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


local_storage = LocalStorage()
encode_uri_component = EncodeURIComponent()


Status = Literal["success", "error", "warning", "pending", "info"]
_STORAGE_KEY = "js-global-demo.theme"
_STORAGE_VALUE = "dark"
_ENCODE_INPUT = "hello world"


@dataclass
class DemoState(Stateful):
    storage_status: Status = "info"
    storage_message: str = "No localStorage action yet."
    encode_status: Status = "info"
    encode_message: str = "Ready to encode a value."


def _button_style(primary: bool) -> dict[str, str]:
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
                    w.Label(text="localStorage", font_weight=600)
                    w.StatusIndicator(
                        status=state.storage_status,
                        label=state.storage_status.title(),
                    )
                    w.Label(text=state.storage_message)
                    with w.Row(gap=12):
                        h.HtmlButton("Write theme", on_click=handle_write, style=_button_style(True))
                        h.HtmlButton("Read theme", on_click=handle_read, style=_button_style(False))
                        h.HtmlButton("Clear theme", on_click=handle_clear, style=_button_style(False))

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


app = App(JsGlobalDemo)
