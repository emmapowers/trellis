"""Demo app to test end-to-end render loop.

Run with: pixi run -- python examples/demo.py
Then open: http://127.0.0.1:8000
"""

from collections.abc import Callable
from dataclasses import dataclass

from trellis import Margin, Padding, Stateful, Trellis, async_main, component
from trellis import widgets as w
from trellis.widgets import theme

# =============================================================================
# Styles
# =============================================================================

STYLE_COUNT_DISPLAY = {
    "backgroundColor": theme.bg_surface,
    "borderRadius": "6px",
    "textAlign": "center",
    "border": f"1px solid {theme.border_default}",
}


# =============================================================================
# State
# =============================================================================


@dataclass
class CounterState(Stateful):
    """Counter state with value constrained between min and max."""

    count: int
    min_val: int
    max_val: int

    def increment(self) -> None:
        self.count = min(self.max_val, self.count + 1)

    def decrement(self) -> None:
        self.count = max(self.min_val, self.count - 1)

    def reset(self) -> None:
        self.count = (self.min_val + self.max_val) // 2


# =============================================================================
# Components
# =============================================================================


@component
def Header(title: str, subtitle: str) -> None:
    """Page header with title and subtitle."""
    with w.Column(align="center", gap=4, margin=Margin(bottom=24)):
        w.Label(text=title, font_size=20, bold=True)
        w.Label(text=subtitle, font_size=13, color=theme.text_secondary)


@component
def CounterControls(
    count: int,
    on_increment: Callable[[], None],
    on_decrement: Callable[[], None],
    min_val: int = 1,
    max_val: int = 10,
) -> None:
    """Counter display with increment/decrement buttons."""
    with w.Row(gap=16, align="center", justify="center", margin=Margin(bottom=24)):
        w.Button(
            text="-",
            on_click=on_decrement,
            disabled=count <= min_val,
            variant="secondary",
            size="lg",
        )

        with w.Column(
            width=120, padding=Padding(x=32, y=16), style=STYLE_COUNT_DISPLAY
        ):
            w.Label(
                text=str(count),
                font_size=36,
                bold=True,
                style={"fontVariantNumeric": "tabular-nums"},
            )

        w.Button(
            text="+",
            on_click=on_increment,
            disabled=count >= max_val,
            variant="secondary",
            size="lg",
        )


@component
def RangeLabels(min_val: int, max_val: int) -> None:
    """Min/max range labels."""
    with w.Row(justify="between", margin=Margin(bottom=24)):
        w.Label(text=f"Min: {min_val}", font_size=12, color=theme.text_secondary)
        w.Label(text=f"Max: {max_val}", font_size=12, color=theme.text_secondary)


@component
def App() -> None:
    """Main application component with interactive counter."""
    state = CounterState(count=5, min_val=1, max_val=10)

    with w.Column(padding=24, align="center", justify="center"):
        with w.Card(padding=32, width=320):
            Header(title="Counter", subtitle="A simple interactive counter demo")
            CounterControls(
                count=state.count,
                on_increment=state.increment,
                on_decrement=state.decrement,
                min_val=state.min_val,
                max_val=state.max_val,
            )
            w.ProgressBar(
                value=state.count,
                min=state.min_val,
                max=state.max_val,
                margin=Margin(bottom=16),
            )
            RangeLabels(min_val=state.min_val, max_val=state.max_val)

            with w.Row(justify="center", gap=8):
                w.Button(text="Reset", on_click=state.reset, variant="outline")


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
