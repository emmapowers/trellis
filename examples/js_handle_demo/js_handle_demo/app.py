"""Returned JavaScript proxy handle demo application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from trellis import App, Stateful, component, js_global, js_property, js_proxy, js_release
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme
from trellis.registry import ExportKind, registry

registry.register(
    "js-handle-demo-helpers",
    base_path=Path(__file__).parent.resolve() / "client",
    exports=[
        ("createCounter", ExportKind.FUNCTION, "handle_helpers.ts"),
    ],
)


@js_proxy(dynamic=True)
class CounterHandle:
    value = js_property[int](writable=True)
    label = js_property[str](writable=True)

    async def increment(self) -> int:
        raise NotImplementedError


@js_proxy(dynamic=True)
class HtmlElement:
    tag_name = js_property[str](name="tagName")

    async def get_attribute(self, name: str) -> str | None:
        raise NotImplementedError

    async def set_attribute(self, name: str, value: str) -> None:
        raise NotImplementedError


@js_proxy
async def create_counter(label: str) -> CounterHandle:
    raise NotImplementedError


@js_global("document")
class Document:
    body = js_property[HtmlElement | None]()

    async def query_selector(self, selector: str) -> HtmlElement | None:
        raise NotImplementedError


document = Document()

Status = Literal["info", "pending", "success", "error"]


@dataclass
class DemoState(Stateful):
    counter_status: Status = "info"
    counter_message: str = "Create a returned counter handle."
    element_status: Status = "info"
    element_message: str = "Query document for a returned element handle."
    counter: CounterHandle | None = None
    element: HtmlElement | None = None


def _button_style(primary: bool) -> dict[str, str]:
    if primary:
        return {
            "backgroundColor": theme.accent_primary,
            "border": "none",
            "borderRadius": "8px",
            "color": "#fff",
            "cursor": "pointer",
            "fontSize": "14px",
            "fontWeight": "600",
            "padding": "10px 16px",
        }

    return {
        "backgroundColor": "transparent",
        "border": f"1px solid {theme.border_default}",
        "borderRadius": "8px",
        "color": theme.text_primary,
        "cursor": "pointer",
        "fontSize": "14px",
        "fontWeight": "600",
        "padding": "10px 16px",
    }


def _status_color(status: Status) -> str:
    if status == "success":
        return "#0f766e"
    if status == "error":
        return "#b91c1c"
    if status == "pending":
        return "#9a6700"
    return theme.text_secondary


@component
def JsHandleDemo() -> None:
    state = DemoState()

    async def handle_create_counter(_event: object | None = None) -> None:
        state.counter_status = "pending"
        state.counter_message = "Creating counter handle..."
        try:
            state.counter = await create_counter("demo-counter")
            value = await state.counter.value.get()
        except RuntimeError as error:
            state.counter_status = "error"
            state.counter_message = str(error)
        else:
            state.counter_status = "success"
            state.counter_message = f"Counter created with value {value}"

    async def handle_increment_counter(_event: object | None = None) -> None:
        if state.counter is None:
            state.counter_status = "error"
            state.counter_message = "Create the counter handle first."
            return

        state.counter_status = "pending"
        state.counter_message = "Incrementing counter..."
        try:
            value = await state.counter.increment()
            label = await state.counter.label.get()
        except RuntimeError as error:
            state.counter_status = "error"
            state.counter_message = str(error)
        else:
            state.counter_status = "success"
            state.counter_message = f"{label} incremented to {value}"

    async def handle_query_body(_event: object | None = None) -> None:
        state.element_status = "pending"
        state.element_message = "Querying document body..."
        try:
            state.element = await document.query_selector("body")
            if state.element is None:
                state.element_status = "success"
                state.element_message = "document.querySelector('body') returned null"
                return
            tag_name = await state.element.tag_name.get()
        except RuntimeError as error:
            state.element_status = "error"
            state.element_message = str(error)
        else:
            state.element_status = "success"
            state.element_message = f"Received element handle for <{tag_name}>"

    async def handle_read_body_id(_event: object | None = None) -> None:
        if state.element is None:
            state.element_status = "error"
            state.element_message = "Query the body handle first."
            return

        state.element_status = "pending"
        state.element_message = "Reading body id..."
        try:
            body_id = await state.element.get_attribute("id")
        except RuntimeError as error:
            state.element_status = "error"
            state.element_message = str(error)
        else:
            shown_id = body_id if body_id else "<empty>"
            state.element_status = "success"
            state.element_message = f"Body id: {shown_id}"

    async def handle_get_body_property(_event: object | None = None) -> None:
        state.element_status = "pending"
        state.element_message = "Reading document.body..."
        try:
            state.element = await document.body.get()
            if state.element is None:
                state.element_status = "success"
                state.element_message = "document.body returned null"
                return
            tag_name = await state.element.tag_name.get()
        except RuntimeError as error:
            state.element_status = "error"
            state.element_message = str(error)
        else:
            state.element_status = "success"
            state.element_message = f"document.body returned <{tag_name}>"

    async def handle_release_body(_event: object | None = None) -> None:
        if state.element is None:
            state.element_status = "error"
            state.element_message = "Acquire a body handle first."
            return

        state.element_status = "pending"
        state.element_message = "Releasing body handle..."
        try:
            await js_release(state.element)
        except (RuntimeError, TypeError) as error:
            state.element_status = "error"
            state.element_message = str(error)
        else:
            state.element_status = "success"
            state.element_message = "Released the current body handle."

    with h.Div(
        style={
            "background": "linear-gradient(180deg, #f3f8ff 0%, #ffffff 100%)",
            "color": theme.text_primary,
            "fontFamily": "'IBM Plex Sans', sans-serif",
            "minHeight": "100vh",
            "padding": "32px 20px 48px",
        }
    ):
        with h.Div(
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "24px",
                "margin": "0 auto",
                "maxWidth": "860px",
            }
        ):
            h.H1(
                "Returned Handle Demo",
                style={"fontSize": "34px", "fontWeight": "700", "letterSpacing": "-0.04em"},
            )
            h.P(
                "Exercise JS objects that come back across the proxy boundary as live handles.",
                style={"color": theme.text_secondary, "fontSize": "16px", "lineHeight": "1.6"},
            )

            with h.Div(
                style={
                    "backgroundColor": "#fff",
                    "border": f"1px solid {theme.border_default}",
                    "borderRadius": "18px",
                    "boxShadow": "0 18px 40px rgba(15, 23, 42, 0.08)",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "18px",
                    "padding": "22px",
                }
            ):
                h.H2("Bundled Counter Handle", style={"fontSize": "24px", "fontWeight": "650"})
                h.P(
                    "A bundled JS function returns a live object with methods and properties.",
                    style={
                        "color": theme.text_secondary,
                        "fontSize": "15px",
                        "lineHeight": "1.6",
                        "margin": "0",
                    },
                )
                with h.Div(style={"display": "flex", "flexWrap": "wrap", "gap": "12px"}):
                    w.Button(
                        text="Create counter",
                        on_click=handle_create_counter,
                        style=_button_style(True),
                    )
                    w.Button(text="Increment", on_click=handle_increment_counter, style=_button_style(False))
                h.P(
                    state.counter_message,
                    style={
                        "color": _status_color(state.counter_status),
                        "fontSize": "15px",
                        "fontWeight": "600",
                        "margin": "0",
                    },
                )

            with h.Div(
                style={
                    "backgroundColor": "#fff",
                    "border": f"1px solid {theme.border_default}",
                    "borderRadius": "18px",
                    "boxShadow": "0 18px 40px rgba(15, 23, 42, 0.08)",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "18px",
                    "padding": "22px",
                }
            ):
                h.H2("Document Body Handle", style={"fontSize": "24px", "fontWeight": "650"})
                h.P(
                    "Browser methods and properties both return DOM handles that can be released and reacquired.",
                    style={
                        "color": theme.text_secondary,
                        "fontSize": "15px",
                        "lineHeight": "1.6",
                        "margin": "0",
                    },
                )
                with h.Div(style={"display": "flex", "flexWrap": "wrap", "gap": "12px"}):
                    w.Button(text="Query body", on_click=handle_query_body, style=_button_style(True))
                    w.Button(text="Get body property", on_click=handle_get_body_property, style=_button_style(False))
                    w.Button(text="Read body id", on_click=handle_read_body_id, style=_button_style(False))
                    w.Button(text="Release body", on_click=handle_release_body, style=_button_style(False))
                h.P(
                    state.element_message,
                    style={
                        "color": _status_color(state.element_status),
                        "fontSize": "15px",
                        "fontWeight": "600",
                        "margin": "0",
                    },
                )


app = App(JsHandleDemo)
