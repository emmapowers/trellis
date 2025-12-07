"""Demo app to test end-to-end render loop.

Run with: pixi run -- python examples/demo.py
Then open: http://127.0.0.1:8000
"""

from collections.abc import Callable
from dataclasses import dataclass

from trellis import Trellis, html as h
from trellis.core.functional_component import component
from trellis.core.state import Stateful
from trellis.utils.async_main import async_main
from trellis.widgets import Button

# =============================================================================
# Styles
# =============================================================================

STYLE_PAGE = {
    "backgroundColor": "#0f172a",
    "minHeight": "100vh",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "fontFamily": "'Inter', system-ui, -apple-system, sans-serif",
    "padding": "24px",
}

STYLE_CARD = {
    "backgroundColor": "#1e293b",
    "borderRadius": "16px",
    "padding": "40px",
    "boxShadow": "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
    "border": "1px solid #334155",
    "width": "320px",
}

STYLE_HEADER = {
    "textAlign": "center",
    "marginBottom": "32px",
}

STYLE_TITLE = {
    "color": "#f1f5f9",
    "fontSize": "28px",
    "fontWeight": "700",
    "margin": "0 0 8px 0",
    "letterSpacing": "-0.025em",
}

STYLE_SUBTITLE = {
    "color": "#94a3b8",
    "fontSize": "14px",
    "margin": "0",
}

STYLE_COUNTER_ROW = {
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "gap": "24px",
    "marginBottom": "32px",
}

STYLE_COUNT_DISPLAY = {
    "backgroundColor": "#0f172a",
    "borderRadius": "12px",
    "padding": "16px 32px",
    "width": "120px",
    "textAlign": "center",
}

STYLE_COUNT_TEXT = {
    "color": "#f1f5f9",
    "fontSize": "48px",
    "fontWeight": "700",
    "fontVariantNumeric": "tabular-nums",
}

STYLE_PROGRESS_CONTAINER = {
    "marginBottom": "24px",
}

STYLE_PROGRESS_BG = {
    "backgroundColor": "#0f172a",
    "borderRadius": "9999px",
    "height": "8px",
    "overflow": "hidden",
}

STYLE_RANGE_LABELS = {
    "display": "flex",
    "justifyContent": "space-between",
    "marginBottom": "32px",
}

STYLE_RANGE_LABEL = {
    "color": "#64748b",
    "fontSize": "12px",
}

STYLE_ACTIONS = {
    "display": "flex",
    "gap": "12px",
    "justifyContent": "center",
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


@dataclass(kw_only=True)
class CounterState(Stateful):
    """Counter state with value constrained between min and max."""

    count: int = 5
    min_val: int = 1
    max_val: int = 10

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
    with h.Div(style=STYLE_HEADER):
        h.H1(title, style=STYLE_TITLE)
        h.P(subtitle, style=STYLE_SUBTITLE)


@component
def CounterControls(
    count: int,
    on_increment: Callable[[], None],
    on_decrement: Callable[[], None],
    min_val: int = 1,
    max_val: int = 10,
) -> None:
    """Counter display with increment/decrement buttons."""
    with h.Div(style=STYLE_COUNTER_ROW):
        Button(
            text="-",
            on_click=on_decrement,
            disabled=count <= min_val,
            variant="secondary",
            size="lg",
        )

        with h.Div(style=STYLE_COUNT_DISPLAY):
            h.Span(str(count), style=STYLE_COUNT_TEXT)

        Button(
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
    with h.Div(style=STYLE_PROGRESS_CONTAINER):
        with h.Div(style=STYLE_PROGRESS_BG):
            with h.Div(style=progress_bar_style(percent)):
                pass


@component
def RangeLabels(min_val: int, max_val: int) -> None:
    """Min/max range labels."""
    with h.Div(style=STYLE_RANGE_LABELS):
        h.Span(f"Min: {min_val}", style=STYLE_RANGE_LABEL)
        h.Span(f"Max: {max_val}", style=STYLE_RANGE_LABEL)


@component
def App() -> None:
    """Main application component with interactive counter."""
    state = CounterState()

    with h.Div(style=STYLE_PAGE):
        with h.Div(style=STYLE_CARD):
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

            with h.Div(style=STYLE_ACTIONS):
                Button(text="Reset", on_click=state.reset, variant="outline")


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
