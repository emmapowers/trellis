"""Slider performance demo.

Run with: pixi run -- python examples/all_sliders_all_the_time.py
Then open: http://127.0.0.1:8000
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis import Trellis
from trellis import html as h
from trellis.core.composition_component import component
from trellis.core.state import Stateful
from trellis.html.events import ChangeEvent
from trellis.utils.async_main import async_main
from trellis.widgets import Button, Column, Row, Slider

# =============================================================================
# Styles
# =============================================================================

STYLE_PAGE: dict[str, tp.Any] = {
    "backgroundColor": "#0f172a",
    "minHeight": "100vh",
    "display": "flex",
    "flexDirection": "column",
    "alignItems": "center",
    "fontFamily": "'Inter', system-ui, -apple-system, sans-serif",
    "padding": "24px",
}

STYLE_CARD: dict[str, tp.Any] = {
    "backgroundColor": "#1e293b",
    "borderRadius": "16px",
    "padding": "24px",
    "boxShadow": "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
    "border": "1px solid #334155",
    "width": "400px",
    "marginBottom": "24px",
}

STYLE_TITLE: dict[str, tp.Any] = {
    "color": "#f1f5f9",
    "fontSize": "24px",
    "fontWeight": "700",
    "margin": "0 0 16px 0",
    "textAlign": "center",
}

STYLE_CONTROL_ROW: dict[str, tp.Any] = {
    "display": "flex",
    "alignItems": "center",
    "gap": "12px",
    "marginBottom": "12px",
}

STYLE_LABEL: dict[str, tp.Any] = {
    "color": "#94a3b8",
    "fontSize": "14px",
    "width": "100px",
}

STYLE_INPUT: dict[str, tp.Any] = {
    "backgroundColor": "#0f172a",
    "border": "1px solid #334155",
    "borderRadius": "8px",
    "padding": "8px 12px",
    "color": "#f1f5f9",
    "fontSize": "14px",
    "width": "80px",
    "outline": "none",
}

STYLE_SLIDERS_CONTAINER: dict[str, tp.Any] = {
    "backgroundColor": "#1e293b",
    "borderRadius": "16px",
    "padding": "24px",
    "boxShadow": "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
    "border": "1px solid #334155",
    "width": "400px",
    "maxHeight": "60vh",
    "overflowY": "auto",
}

STYLE_SLIDER_ROW: dict[str, tp.Any] = {
    "display": "flex",
    "alignItems": "center",
    "gap": "12px",
    "marginBottom": "8px",
}

STYLE_SLIDER_LABEL: dict[str, tp.Any] = {
    "color": "#64748b",
    "fontSize": "12px",
    "width": "60px",
    "textAlign": "right",
}

STYLE_SLIDER_VALUE: dict[str, tp.Any] = {
    "color": "#f1f5f9",
    "fontSize": "14px",
    "fontWeight": "600",
    "fontVariantNumeric": "tabular-nums",
    "width": "40px",
}


# =============================================================================
# State
# =============================================================================


@dataclass(kw_only=True)
class SliderState(Stateful):
    """State for the slider demo."""

    num_sliders: int = 3
    value: float = 50

    def reset(self) -> None:
        """Reset to default values."""
        self.num_sliders = 3
        self.value = 50

    def set_num_sliders(self, num: int) -> None:
        """Update number of sliders."""
        self.num_sliders = max(1, num)

    def set_value(self, val: float) -> None:
        """Update slider value."""
        self.value = val


# =============================================================================
# Components
# =============================================================================


@component
def ControlPanel() -> None:
    """Top control panel with inputs and reset button."""
    state = SliderState.from_context()

    def handle_num_change(event: ChangeEvent) -> None:
        try:
            state.set_num_sliders(int(event.value))
        except ValueError:
            pass

    def handle_value_change(event: ChangeEvent) -> None:
        try:
            state.set_value(float(event.value))
        except ValueError:
            pass

    with h.Div(style=STYLE_CARD):
        h.H2("Slider Performance Test", style=STYLE_TITLE)

        with h.Div(style=STYLE_CONTROL_ROW):
            h.Span("Num Sliders:", style=STYLE_LABEL)
            h.Input(
                type="number",
                value=str(state.num_sliders),
                onChange=handle_num_change,
                style=STYLE_INPUT,
            )

        with h.Div(style=STYLE_CONTROL_ROW):
            h.Span("Value:", style=STYLE_LABEL)
            h.Input(
                type="number",
                value=str(int(state.value)),
                onChange=handle_value_change,
                style=STYLE_INPUT,
            )

        with Row(justify="center", gap=12):
            Button(text="Reset", on_click=state.reset, variant="outline")


@component
def SliderColumn() -> None:
    """Column of sliders."""
    state = SliderState.from_context()

    with h.Div(style=STYLE_SLIDERS_CONTAINER):
        with Column(gap=4):
            for i in range(state.num_sliders):
                with h.Div(style=STYLE_SLIDER_ROW, key=f"slider-row-{i}"):
                    h.Span(f"#{i + 1}", style=STYLE_SLIDER_LABEL)
                    Slider(
                        value=state.value,
                        min=1,
                        max=100,
                        step=1,
                        on_change=state.set_value,
                        key=f"slider-{i}",
                    )
                    h.Span(str(int(state.value)), style=STYLE_SLIDER_VALUE)


@component
def App() -> None:
    """Main application."""
    state = SliderState()

    with state:
        with h.Div(style=STYLE_PAGE):
            ControlPanel()
            SliderColumn()


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
