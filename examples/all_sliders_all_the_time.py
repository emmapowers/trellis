"""Slider performance demo.

Run with: pixi run -- python examples/all_sliders_all_the_time.py
Then open: http://127.0.0.1:8000
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis import Stateful, Trellis, async_main, component
from trellis import widgets as w

# =============================================================================
# Styles
# =============================================================================

STYLE_PAGE: dict[str, tp.Any] = {
    "backgroundColor": "#0f172a",
    "minHeight": "100vh",
    "fontFamily": "'Inter', system-ui, -apple-system, sans-serif",
    "padding": "24px",
}


# =============================================================================
# State
# =============================================================================


@dataclass
class SliderState(Stateful):
    """State for the slider demo."""

    num_sliders: int
    value: float

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

    def handle_num_change(value: float) -> None:
        state.set_num_sliders(int(value))

    def handle_value_change(value: float) -> None:
        state.set_value(value)

    with w.Card(padding=24, style={"width": "400px", "marginBottom": "24px"}):
        w.Label(
            text="Slider Performance Test",
            font_size=24,
            color="#f1f5f9",
            bold=True,
            style={"textAlign": "center", "display": "block", "marginBottom": "16px"},
        )

        with w.Row(gap=12, align="center", style={"marginBottom": "12px"}):
            w.Label(text="Num Sliders:", color="#94a3b8", style={"width": "100px"})
            w.NumberInput(
                value=float(state.num_sliders),
                min=1,
                on_change=handle_num_change,
                style={"width": "80px"},
            )

        with w.Row(gap=12, align="center", style={"marginBottom": "12px"}):
            w.Label(text="Value:", color="#94a3b8", style={"width": "100px"})
            w.NumberInput(
                value=state.value,
                on_change=handle_value_change,
                style={"width": "80px"},
            )

        with w.Row(justify="center", gap=12):
            w.Button(text="Reset", on_click=state.reset, variant="outline")


@component
def SliderColumn() -> None:
    """Column of sliders."""
    state = SliderState.from_context()

    with w.Card(
        padding=24,
        style={"width": "400px", "maxHeight": "60vh", "overflowY": "auto"},
    ):
        with w.Column(gap=4):
            for i in range(state.num_sliders):
                with w.Row(gap=12, align="center", key=f"slider-row-{i}"):
                    w.Label(
                        text=f"#{i + 1}",
                        font_size=12,
                        color="#64748b",
                        style={"width": "60px", "textAlign": "right"},
                    )
                    w.Slider(
                        value=state.value,
                        min=1,
                        max=100,
                        step=1,
                        on_change=state.set_value,
                        key=f"slider-{i}",
                    )
                    w.Label(
                        text=str(int(state.value)),
                        font_size=14,
                        color="#f1f5f9",
                        bold=True,
                        style={"fontVariantNumeric": "tabular-nums", "width": "40px"},
                    )


@component
def App() -> None:
    """Main application."""
    state = SliderState(num_sliders=3, value=50)

    with state:
        with w.Column(style=STYLE_PAGE, align="center"):
            ControlPanel()
            SliderColumn()


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
