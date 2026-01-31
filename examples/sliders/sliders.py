"""Slider performance demo.

Run with: pixi run -- python examples/all_sliders_all_the_time.py
Then open: http://127.0.0.1:8000
"""

from __future__ import annotations

from dataclasses import dataclass

from trellis import Height, Margin, Stateful, Trellis, async_main, callback, component, mutable
from trellis import widgets as w
from trellis.app import theme

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


# =============================================================================
# Components
# =============================================================================


@component
def ControlPanel() -> None:
    """Top control panel with inputs and reset button."""
    state = SliderState.from_context()

    def handle_num_change(value: float) -> None:
        state.set_num_sliders(int(value))

    with w.Card(padding=16, width=400, margin=Margin(bottom=16)):
        w.Label(
            text="Slider Performance Test",
            font_size=16,
            bold=True,
            margin=Margin(bottom=12),
            text_align="center",
            style={"display": "block"},
        )

        with w.Row(gap=8, align="center", margin=Margin(bottom=8)):
            w.Label(text="Num Sliders:", color=theme.text_secondary, width=100)
            # Uses callback() for custom processing (clamping via set_num_sliders)
            w.NumberInput(
                value=callback(state.num_sliders, handle_num_change),
                min=1,
                width=80,
            )

        with w.Row(gap=8, align="center", margin=Margin(bottom=8)):
            w.Label(text="Value:", color=theme.text_secondary, width=100)
            w.NumberInput(
                value=mutable(state.value),
                width=80,
            )

        with w.Row(justify="center", gap=8):
            w.Button(text="Reset", on_click=state.reset, variant="outline")


@component
def SliderColumn() -> None:
    """Column of sliders."""
    state = SliderState.from_context()

    with w.Card(
        padding=16,
        width=400,
        height=Height(max="60vh"),
        style={"overflowY": "auto"},
    ):
        with w.Column(gap=4):
            for i in range(state.num_sliders):
                with w.Row(gap=8, align="center").key(f"slider-row-{i}"):
                    w.Label(
                        text=f"#{i + 1}",
                        font_size=12,
                        color=theme.text_secondary,
                        width=50,
                        text_align="right",
                    )
                    w.Slider(
                        value=mutable(state.value),
                        min=1,
                        max=100,
                        step=1,
                        style={"flex": "1"},
                    ).key(f"slider-{i}")
                    w.Label(
                        text=str(int(state.value)),
                        font_size=13,
                        bold=True,
                        width=36,
                        style={"fontVariantNumeric": "tabular-nums"},
                    )


@component
def App() -> None:
    """Main application."""
    state = SliderState(num_sliders=3, value=50)

    with state:
        with w.Column(padding=24, align="center"):
            ControlPanel()
            SliderColumn()


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
