"""Hello World counter application."""

from collections.abc import Callable

from trellis import Margin, Padding, component, state_var
from trellis import widgets as w
from trellis.app import App, theme

# =============================================================================
# Styles
# =============================================================================

STYLE_COUNT_DISPLAY = {
    "backgroundColor": theme.bg_surface,
    "borderRadius": "6px",
    "textAlign": "center",
    "border": f"1px solid {theme.border_default}",
}


MIN_COUNT = 1
MAX_COUNT = 10
INITIAL_COUNT = 5


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

        with w.Column(width=120, padding=Padding(x=32, y=16), style=STYLE_COUNT_DISPLAY):
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
def HelloWorld() -> None:
    """Main application component with interactive counter."""
    count = state_var(INITIAL_COUNT)

    def increment() -> None:
        count.set(min(MAX_COUNT, count.value + 1))

    def decrement() -> None:
        count.set(max(MIN_COUNT, count.value - 1))

    def reset() -> None:
        count.set((MIN_COUNT + MAX_COUNT) // 2)

    with w.Column(padding=24, align="center", justify="center"):
        with w.Card(padding=32, width=320):
            Header(title="Counter", subtitle="A simple interactive counter demo")
            CounterControls(
                count=count.value,
                on_increment=increment,
                on_decrement=decrement,
                min_val=MIN_COUNT,
                max_val=MAX_COUNT,
            )
            w.ProgressBar(
                value=count.value,
                min=MIN_COUNT,
                max=MAX_COUNT,
                margin=Margin(bottom=16),
            )
            RangeLabels(min_val=MIN_COUNT, max_val=MAX_COUNT)

            with w.Row(justify="center", gap=8):
                w.Button(text="Reset", on_click=reset, variant="outline")


app = App(HelloWorld)
