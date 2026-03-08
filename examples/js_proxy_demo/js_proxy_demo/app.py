"""JS proxy demo application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from trellis import JsProxy, Stateful, component, js_object
from trellis import html as h
from trellis import widgets as w
from trellis.app import App, theme
from trellis.registry import ExportKind, registry

registry.register(
    "js-proxy-demo",
    base_path=Path(__file__).parent.resolve() / "client",
    exports=[("demo_api", ExportKind.OBJECT, "demo_api.ts")],
)


class DemoApi(JsProxy):
    async def greet(self, name: str) -> str: ...

    async def fail(self) -> str: ...


demo_api = js_object(DemoApi, "demo_api")


@dataclass
class DemoState(Stateful):
    status: Literal["success", "error", "warning", "pending", "info"] = "info"
    message: str = "Ready"


@component
def JsProxyDemo() -> None:
    """Demonstrate successful and failing JS proxy calls."""
    state = DemoState()

    async def handle_success(_event: object | None = None) -> None:
        state.status = "pending"
        state.message = "Calling greet()..."
        try:
            state.message = await demo_api.greet("Emma")
            state.status = "success"
        except RuntimeError as error:
            state.status = "error"
            state.message = str(error)

    async def handle_failure(_event: object | None = None) -> None:
        state.status = "pending"
        state.message = "Calling fail()..."
        try:
            await demo_api.fail()
        except RuntimeError as error:
            state.status = "error"
            state.message = str(error)
        else:
            state.status = "success"
            state.message = "Unexpected success"

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
                    text="Call a bundled TypeScript object from Python and surface the result.",
                    color=theme.text_secondary,
                )
                w.StatusIndicator(status=state.status, label=state.status.title())
                w.Label(text=state.message)
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


app = App(JsProxyDemo)
