"""CSS section of the widget showcase."""

from trellis import component
from trellis import html as h
from trellis import widgets as w
from trellis.app import theme

from ..components import ExampleCard
from ..example import example


@example("Typed HTML Style")
def TypedHtmlStyle() -> None:
    """Typed CSS values, pseudo states, and media queries on HTML elements."""
    with h.Div(
        style=h.Style(
            display="grid",
            gap=12,
            padding=16,
            background_color=h.color(theme.bg_surface),
            border=h.border(1, "solid", theme.border_default),
            border_radius=12,
            transition=h.raw("transform 150ms ease, box-shadow 150ms ease"),
            hover=h.Style(
                transform=h.scale(1.01),
                box_shadow=h.shadow("0 8px 24px rgba(15, 23, 42, 0.12)"),
            ),
            media=[
                h.media(
                    min_width=720,
                    style=h.Style(grid_template_columns=h.raw("repeat(2, minmax(0, 1fr))")),
                )
            ],
        )
    ):
        with h.Div(
            style=h.Style(
                background_color=h.color(theme.bg_surface_raised),
                border_radius=10,
                padding=16,
            )
        ):
            h.H3("Typed style")
            h.P("Structured values with helpers for border, hover, and media rules.")

        with h.Div(
            style=h.Style(
                background_color=h.color(theme.bg_page),
                border_radius=10,
                padding=16,
            )
        ):
            h.H3("Generated rules")
            h.P("Pseudo states and media queries compile into scoped CSS classes automatically.")


@example("Widget Style Sugar")
def WidgetStyleSugar() -> None:
    """Widget width/padding props share the same CSS pipeline as style=."""
    with w.Column(gap=12):
        with w.Card(
            width=320,
            padding=16,
            style=h.Style(
                border=h.border(1, "solid", theme.border_default),
                hover=h.Style(border_color=h.color(theme.accent_primary)),
            ),
        ):
            w.Heading(text="Widget sugar", level=4)
            w.Label(text="`width=` and `padding=` feed the same typed CSS compiler as `style=`.")

        with w.Card(
            padding=16,
            style={
                "border": f"1px solid {theme.border_default}",
                "border-radius": "12px",
                "@media (min-width: 720px)": {
                    "padding": "24px",
                },
            },
        ):
            w.Heading(text="Raw dict escape hatch", level=4)
            w.Label(text="DOM-style keys stay available when structured typing is too restrictive.")


@component
def CssSection() -> None:
    """Showcase the Trellis HTML CSS system."""
    with w.Column(gap=16):
        ExampleCard(example=TypedHtmlStyle)
        ExampleCard(example=WidgetStyleSugar)
