"""Slider performance demo application."""

from __future__ import annotations

from dataclasses import dataclass

from trellis import Stateful, callback, component, mutable
from trellis import html as h
from trellis import widgets as w
from trellis.app import App, theme

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

    with w.Card(padding=16, width=400, style={"margin-bottom": "16px"}):
        w.Label(
            text="Slider Performance Test",
            font_size=16,
            bold=True,
            text_align="center",
            style={"display": "block", "margin-bottom": "12px"},
        )

        with w.Row(gap=8, align="center", style={"margin-bottom": "8px"}):
            w.Label(text="Num Sliders:", color=theme.text_secondary, width=100)
            # Uses callback() for custom processing (clamping via set_num_sliders)
            w.NumberInput(
                value=callback(state.num_sliders, handle_num_change),
                min=1,
                width=80,
            )

        with w.Row(gap=8, align="center", style={"margin-bottom": "8px"}):
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
        style=h.Style(max_height=h.vh(60), overflow_y="auto"),
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
                        style={"flex": 1},
                    ).key(f"slider-{i}")
                    w.Label(
                        text=str(int(state.value)),
                        font_size=13,
                        bold=True,
                        width=36,
                        style={"font-variant-numeric": "tabular-nums"},
                    )


@component
def SlidersDemo() -> None:
    """Main application."""
    state = SliderState(num_sliders=3, value=50)

    with state:
        with w.Column(padding=24, align="center"):
            ControlPanel()
            SliderColumn()


app = App(SlidersDemo)
