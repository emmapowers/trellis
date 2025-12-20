"""Layout section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Row (horizontal)")
def RowLayout() -> None:
    """Horizontal flex container with justify options."""
    with w.Column(gap=8):
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


@example("Column (vertical)")
def ColumnLayout() -> None:
    """Vertical flex container with align options."""
    with w.Row(gap=16):
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


@example("Dividers")
def LayoutDividers() -> None:
    """Row and Column with dividers between items."""
    with w.Row(gap=16):
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


@example("Card")
def CardLayout() -> None:
    """Card container for grouped content."""
    with w.Row(gap=16):
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


@component
def LayoutSection() -> None:
    """Showcase layout widgets."""
    with w.Column(gap=16):
        ExampleCard(example=RowLayout)
        ExampleCard(example=ColumnLayout)
        ExampleCard(example=LayoutDividers)
        ExampleCard(example=CardLayout)
