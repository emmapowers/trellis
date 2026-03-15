"""Hello World counter application."""

from collections.abc import Callable

from trellis import App, component, state_var
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme

# =============================================================================
# Styles
# =============================================================================

STYLE_COUNT_DISPLAY = h.Style(
    background_color=theme.bg_surface,
    border_radius=6,
    text_align="center",
    border=f"1px solid {theme.border_default}",
)


MIN_COUNT = 1
MAX_COUNT = 10
INITIAL_COUNT = 5


# =============================================================================
# Components
# =============================================================================


@component
def Header(title: str, subtitle: str) -> None:
    """Page header with title and subtitle."""
    with w.Column(align="center", gap=4, style=h.Style(margin_bottom=24)):
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
    with w.Row(gap=16, align="center", justify="center", style=h.Style(margin_bottom=24)):
        w.Button(
            text="-",
            on_click=on_decrement,
            disabled=count <= min_val,
            variant="secondary",
            size="lg",
        )

        with w.Column(width=120, padding=h.padding(16, 32), style=STYLE_COUNT_DISPLAY):
            w.Label(
                text=str(count),
                font_size=36,
                bold=True,
                style=h.Style(font_variant_numeric=h.raw("tabular-nums")),
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
    with w.Row(justify="between", style=h.Style(margin_bottom=24)):
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
        count.set(INITIAL_COUNT)

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
                style=h.Style(margin_bottom=16),
            )
            RangeLabels(min_val=MIN_COUNT, max_val=MAX_COUNT)

            with w.Row(justify="center", gap=8):
                w.Button(text="Reset", on_click=reset, variant="outline")


app = App(HelloWorld)
