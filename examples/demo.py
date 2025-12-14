"""Demo app to test end-to-end render loop.

Run with: pixi run -- python examples/demo.py
Then open: http://127.0.0.1:8000
"""

from collections.abc import Callable
from dataclasses import dataclass

from trellis import Stateful, Trellis, async_main, component
from trellis import html as h
from trellis import widgets as w

# =============================================================================
# Styles
# =============================================================================

STYLE_PAGE = {
    "backgroundColor": "#0f172a",
    "minHeight": "100vh",
    "fontFamily": "'Inter', system-ui, -apple-system, sans-serif",
    "padding": "24px",
}

STYLE_COUNT_DISPLAY = {
    "backgroundColor": "#0f172a",
    "borderRadius": "12px",
    "padding": "16px 32px",
    "width": "120px",
    "textAlign": "center",
}

STYLE_PROGRESS_BG = {
    "backgroundColor": "#0f172a",
    "borderRadius": "9999px",
    "height": "8px",
    "overflow": "hidden",
}


def progress_bar_style(percent: float) -> dict:
    """Generate style for progress bar fill."""
    return {
        "backgroundColor": "#6366f1",
        "height": "100%",
        "width": f"{percent}%",
        "borderRadius": "9999px",
        "transition": "width 200ms ease",
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
    with w.Column(align="center", gap=8, style={"marginBottom": "32px"}):
        w.Label(text=title, font_size=28, color="#f1f5f9", bold=True)
        w.Label(text=subtitle, font_size=14, color="#94a3b8")


@component
def CounterControls(
    count: int,
    on_increment: Callable[[], None],
    on_decrement: Callable[[], None],
    min_val: int = 1,
    max_val: int = 10,
) -> None:
    """Counter display with increment/decrement buttons."""
    with w.Row(gap=24, align="center", justify="center", style={"marginBottom": "32px"}):
        w.Button(
            text="-",
            on_click=on_decrement,
            disabled=count <= min_val,
            variant="secondary",
            size="lg",
        )

        with w.Column(style=STYLE_COUNT_DISPLAY):
            w.Label(
                text=str(count),
                font_size=48,
                color="#f1f5f9",
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
def ProgressBar(value: int, min_val: int = 1, max_val: int = 10) -> None:
    """Visual progress indicator."""
    percent = (value - min_val) / (max_val - min_val) * 100
    with w.Column(style={"marginBottom": "24px"}):
        with h.Div(style=STYLE_PROGRESS_BG):
            with h.Div(style=progress_bar_style(percent)):
                pass


@component
def RangeLabels(min_val: int, max_val: int) -> None:
    """Min/max range labels."""
    with w.Row(justify="between", style={"marginBottom": "32px"}):
        w.Label(text=f"Min: {min_val}", font_size=12, color="#64748b")
        w.Label(text=f"Max: {max_val}", font_size=12, color="#64748b")


@component
def App() -> None:
    """Main application component with interactive counter."""
    state = CounterState(count=5, min_val=1, max_val=10)

    with w.Column(style=STYLE_PAGE, align="center", justify="center"):
        with w.Card(padding=40, style={"width": "320px"}):
            Header(title="Counter", subtitle="A simple interactive counter demo")
            CounterControls(
                count=state.count,
                on_increment=state.increment,
                on_decrement=state.decrement,
                min_val=state.min_val,
                max_val=state.max_val,
            )
            ProgressBar(value=state.count, min_val=state.min_val, max_val=state.max_val)
            RangeLabels(min_val=state.min_val, max_val=state.max_val)

            with w.Row(justify="center", gap=12):
                w.Button(text="Reset", on_click=state.reset, variant="outline")


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
