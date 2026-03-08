"""JS proxy demo application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from trellis import Stateful, component, js_proxy
from trellis import html as h
from trellis import widgets as w
from trellis.app import App, theme
from trellis.registry import ExportKind, registry

registry.register(
    "js-proxy-demo",
    base_path=Path(__file__).parent.resolve() / "client",
    exports=[
        ("DemoApi", ExportKind.OBJECT, "demo_api.ts"),
        ("formatNow", ExportKind.FUNCTION, "demo_api.ts"),
        ("renameMe", ExportKind.FUNCTION, "demo_api.ts"),
    ],
)


@js_proxy
class DemoApi:
    async def greet(self, name: str) -> str:
        raise NotImplementedError

    async def fail(self) -> str:
        raise NotImplementedError


demo_api = DemoApi()


@js_proxy
async def format_now(value: int) -> str:
    raise NotImplementedError


@js_proxy(name="renameMe")
async def explode_now() -> str:
    raise NotImplementedError


@dataclass
class DemoState(Stateful):
    object_status: Literal["success", "error", "warning", "pending", "info"] = "info"
    object_message: str = "Object ready"
    function_status: Literal["success", "error", "warning", "pending", "info"] = "info"
    function_message: str = "Function ready"


@component
def JsProxyDemo() -> None:
    """Demonstrate successful and failing JS proxy calls."""
    state = DemoState()

    async def handle_success(_event: object | None = None) -> None:
        state.object_status = "pending"
        state.object_message = "Calling greet()..."
        try:
            state.object_message = await demo_api.greet("Emma")
            state.object_status = "success"
        except RuntimeError as error:
            state.object_status = "error"
            state.object_message = str(error)

    async def handle_failure(_event: object | None = None) -> None:
        state.object_status = "pending"
        state.object_message = "Calling fail()..."
        try:
            await demo_api.fail()
        except RuntimeError as error:
            state.object_status = "error"
            state.object_message = str(error)
        else:
            state.object_status = "success"
            state.object_message = "Unexpected success"

    async def handle_function_success(_event: object | None = None) -> None:
        state.function_status = "pending"
        state.function_message = "Calling format_now()..."
        try:
            state.function_message = await format_now(3)
            state.function_status = "success"
        except RuntimeError as error:
            state.function_status = "error"
            state.function_message = str(error)

    async def handle_function_failure(_event: object | None = None) -> None:
        state.function_status = "pending"
        state.function_message = "Calling explode_now()..."
        try:
            await explode_now()
        except RuntimeError as error:
            state.function_status = "error"
            state.function_message = str(error)
        else:
            state.function_status = "success"
            state.function_message = "Unexpected success"

    with w.Column(
        padding=24,
        gap=16,
        align="center",
        justify="center",
        style={"minHeight": "100vh", "backgroundColor": theme.bg_page},
    ):
        with w.Card(
            width=420,
            padding=24,
            style={"backgroundColor": theme.bg_surface},
        ):
            with w.Column(gap=12):
                w.Heading(text="JS Proxy Demo", level=2)
                w.Label(
                    text="Call bundled TypeScript objects and functions from Python.",
                    color=theme.text_secondary,
                )
                with w.Column(gap=8):
                    w.Label(text="Object proxy", font_weight=600)
                    w.StatusIndicator(
                        status=state.object_status,
                        label=state.object_status.title(),
                    )
                    w.Label(text=state.object_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Call greet",
                            on_click=handle_success,
                            style={
                                "backgroundColor": theme.accent_primary,
                                "color": "#fff",
                                "border": "none",
                                "borderRadius": "8px",
                                "padding": "10px 16px",
                                "cursor": "pointer",
                                "fontSize": "14px",
                                "fontWeight": 600,
                            },
                        )
                        h.HtmlButton(
                            "Call fail",
                            on_click=handle_failure,
                            style={
                                "backgroundColor": "transparent",
                                "color": theme.text_primary,
                                "border": f"1px solid {theme.border_default}",
                                "borderRadius": "8px",
                                "padding": "10px 16px",
                                "cursor": "pointer",
                                "fontSize": "14px",
                                "fontWeight": 600,
                            },
                        )
                with w.Column(gap=8):
                    w.Label(text="Function proxy", font_weight=600)
                    w.StatusIndicator(
                        status=state.function_status,
                        label=state.function_status.title(),
                    )
                    w.Label(text=state.function_message)
                    with w.Row(gap=12):
                        h.HtmlButton(
                            "Call format_now",
                            on_click=handle_function_success,
                            style={
                                "backgroundColor": theme.accent_primary,
                                "color": "#fff",
                                "border": "none",
                                "borderRadius": "8px",
                                "padding": "10px 16px",
                                "cursor": "pointer",
                                "fontSize": "14px",
                                "fontWeight": 600,
                            },
                        )
                        h.HtmlButton(
                            "Call explode_now",
                            on_click=handle_function_failure,
                            style={
                                "backgroundColor": "transparent",
                                "color": theme.text_primary,
                                "border": f"1px solid {theme.border_default}",
                                "borderRadius": "8px",
                                "padding": "10px 16px",
                                "cursor": "pointer",
                                "fontSize": "14px",
                                "fontWeight": 600,
                            },
                        )


app = App(JsProxyDemo)
