"""Layout section of the widget showcase."""

from trellis import component
from trellis import widgets as w


@component
def LayoutSection() -> None:
    """Showcase layout widgets."""
    with w.Column(gap=16):
        # Row layouts
        w.Label(text="Row (horizontal)", font_size=12, color="#64748b", bold=True)
        with w.Column(gap=8, style={"marginTop": "8px"}):
            w.Label(text="justify='start' (default)")
            with w.Row(gap=8, style={"backgroundColor": "#f1f5f9", "padding": "8px"}):
                w.Button(text="A", size="sm")
                w.Button(text="B", size="sm")
                w.Button(text="C", size="sm")

            w.Label(text="justify='center'")
            with w.Row(
                gap=8, justify="center", style={"backgroundColor": "#f1f5f9", "padding": "8px"}
            ):
                w.Button(text="A", size="sm")
                w.Button(text="B", size="sm")
                w.Button(text="C", size="sm")

            w.Label(text="justify='between'")
            with w.Row(
                gap=8,
                justify="between",
                style={"backgroundColor": "#f1f5f9", "padding": "8px"},
            ):
                w.Button(text="A", size="sm")
                w.Button(text="B", size="sm")
                w.Button(text="C", size="sm")

        # Column layouts
        w.Label(text="Column (vertical)", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, style={"marginTop": "8px"}):
            with w.Column(gap=4):
                w.Label(text="align='start'")
                with w.Column(
                    gap=4,
                    align="start",
                    style={
                        "backgroundColor": "#f1f5f9",
                        "padding": "8px",
                        "height": "100px",
                    },
                ):
                    w.Button(text="A", size="sm")
                    w.Button(text="B", size="sm")

            with w.Column(gap=4):
                w.Label(text="align='center'")
                with w.Column(
                    gap=4,
                    align="center",
                    style={
                        "backgroundColor": "#f1f5f9",
                        "padding": "8px",
                        "height": "100px",
                        "width": "120px",
                    },
                ):
                    w.Button(text="A", size="sm")
                    w.Button(text="B", size="sm")

            with w.Column(gap=4):
                w.Label(text="align='end'")
                with w.Column(
                    gap=4,
                    align="end",
                    style={
                        "backgroundColor": "#f1f5f9",
                        "padding": "8px",
                        "height": "100px",
                        "width": "120px",
                    },
                ):
                    w.Button(text="A", size="sm")
                    w.Button(text="B", size="sm")

        # Dividers
        w.Label(text="Dividers", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, style={"marginTop": "8px"}):
            with w.Column(gap=4):
                w.Label(text="Row with divider")
                with w.Row(
                    gap=12,
                    divider=True,
                    style={"backgroundColor": "#f1f5f9", "padding": "8px"},
                ):
                    w.Label(text="Item 1")
                    w.Label(text="Item 2")
                    w.Label(text="Item 3")

            with w.Column(gap=4):
                w.Label(text="Column with divider")
                with w.Column(
                    gap=8,
                    divider=True,
                    style={"backgroundColor": "#f1f5f9", "padding": "8px"},
                ):
                    w.Label(text="Item 1")
                    w.Label(text="Item 2")
                    w.Label(text="Item 3")

        # Card
        w.Label(text="Card", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, style={"marginTop": "8px"}):
            with w.Card():
                with w.Column(gap=8):
                    w.Label(text="Card Title", bold=True)
                    w.Label(text="Cards provide a contained surface for content.")
                    w.Button(text="Action", variant="primary", size="sm")

            with w.Card():
                with w.Column(gap=8):
                    w.Label(text="Another Card", bold=True)
                    w.Label(text="Multiple cards can be used side by side.")
                    w.Button(text="Learn More", variant="outline", size="sm")
