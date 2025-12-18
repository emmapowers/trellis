"""Widget showcase - demonstrates all available Trellis widgets.

Run with: pixi run -- python examples/widget_showcase.py
Then open: http://127.0.0.1:8000
"""

from __future__ import annotations

from dataclasses import dataclass, field

from trellis import Stateful, Trellis, async_main, component
from trellis import widgets as w


# =============================================================================
# State
# =============================================================================


@dataclass
class ShowcaseState(Stateful):
    """State for interactive widgets."""

    text_value: str = ""
    number_value: float = 50
    slider_value: float = 50
    checkbox_value: bool = False
    select_value: str = "option1"


# =============================================================================
# Section Components
# =============================================================================


@component
def SectionHeader(title: str, description: str) -> None:
    """Section header with title and description."""
    with w.Column(gap=4, style={"marginBottom": "16px"}):
        w.Heading(text=title, level=3)
        w.Label(text=description, color="#64748b", font_size=13)


@component
def ButtonsSection() -> None:
    """Showcase all button variants and sizes."""
    with w.Card(padding=20):
        SectionHeader(
            title="Buttons",
            description="Available variants: primary, secondary, outline, ghost, danger",
        )

        # Variants
        w.Label(text="Variants", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=8, style={"marginBottom": "16px", "marginTop": "8px"}):
            w.Button(text="Primary", variant="primary")
            w.Button(text="Secondary", variant="secondary")
            w.Button(text="Outline", variant="outline")
            w.Button(text="Ghost", variant="ghost")
            w.Button(text="Danger", variant="danger")

        # Sizes
        w.Label(text="Sizes", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=8, align="center", style={"marginTop": "8px"}):
            w.Button(text="Small", size="sm")
            w.Button(text="Medium", size="md")
            w.Button(text="Large", size="lg")


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    state = ShowcaseState.from_context()

    with w.Card(padding=20):
        SectionHeader(
            title="Form Inputs",
            description="Text, number, select, checkbox, and slider inputs",
        )

        with w.Column(gap=12):
            # Text input
            with w.Row(gap=8, align="center"):
                w.Label(text="Text:", style={"width": "80px"})
                w.TextInput(
                    value=state.text_value,
                    placeholder="Enter text...",
                    on_change=lambda v: setattr(state, "text_value", v),
                    style={"width": "200px"},
                )

            # Number input
            with w.Row(gap=8, align="center"):
                w.Label(text="Number:", style={"width": "80px"})
                w.NumberInput(
                    value=state.number_value,
                    min=0,
                    max=100,
                    on_change=lambda v: setattr(state, "number_value", v),
                    style={"width": "200px"},
                )

            # Select
            with w.Row(gap=8, align="center"):
                w.Label(text="Select:", style={"width": "80px"})
                w.Select(
                    value=state.select_value,
                    options=[
                        {"value": "option1", "label": "Option 1"},
                        {"value": "option2", "label": "Option 2"},
                        {"value": "option3", "label": "Option 3"},
                    ],
                    on_change=lambda v: setattr(state, "select_value", v),
                    style={"width": "200px"},
                )

            # Checkbox
            with w.Row(gap=8, align="center"):
                w.Label(text="Toggle:", style={"width": "80px"})
                w.Checkbox(
                    checked=state.checkbox_value,
                    label="Enable feature",
                    on_change=lambda v: setattr(state, "checkbox_value", v),
                )

            # Slider
            with w.Row(gap=8, align="center"):
                w.Label(text="Slider:", style={"width": "80px"})
                w.Slider(
                    value=state.slider_value,
                    min=0,
                    max=100,
                    on_change=lambda v: setattr(state, "slider_value", v),
                    style={"width": "200px"},
                )
                w.Label(text=f"{int(state.slider_value)}", style={"width": "40px"})


@component
def StatusSection() -> None:
    """Showcase status indicators and badges."""
    with w.Card(padding=20):
        SectionHeader(
            title="Status Indicators & Badges",
            description="Semantic status display with icons and colored badges",
        )

        # Status indicators
        w.Label(text="Status Indicators", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, style={"marginBottom": "16px", "marginTop": "8px"}):
            w.StatusIndicator(status="success", label="Success")
            w.StatusIndicator(status="error", label="Error")
            w.StatusIndicator(status="warning", label="Warning")
            w.StatusIndicator(status="pending", label="Pending")
            w.StatusIndicator(status="info", label="Info")

        # Badges
        w.Label(text="Badges", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=8, style={"marginTop": "8px"}):
            w.Badge(text="Default")
            w.Badge(text="Success", variant="success")
            w.Badge(text="Error", variant="error")
            w.Badge(text="Warning", variant="warning")
            w.Badge(text="Info", variant="info")


@component
def TableSection() -> None:
    """Showcase table widget."""
    with w.Card(padding=20):
        SectionHeader(
            title="Table",
            description="Data tables with configurable columns and styling",
        )

        w.Table(
            columns=[
                {"key": "name", "label": "Name", "width": "150px"},
                {"key": "status", "label": "Status", "align": "center"},
                {"key": "value", "label": "Value", "align": "right"},
                {"key": "change", "label": "Change", "align": "right"},
            ],
            data=[
                {"name": "Revenue", "status": "Active", "value": "$12,450", "change": "+12%"},
                {"name": "Users", "status": "Active", "value": "1,234", "change": "+5%"},
                {"name": "Orders", "status": "Pending", "value": "456", "change": "-2%"},
                {"name": "Conversion", "status": "Active", "value": "3.2%", "change": "+0.5%"},
            ],
            striped=True,
        )


@component
def ProgressSection() -> None:
    """Showcase progress bars."""
    with w.Card(padding=20):
        SectionHeader(
            title="Progress Bars",
            description="Horizontal progress indicators with various states",
        )

        with w.Column(gap=12):
            with w.Row(gap=8, align="center"):
                w.Label(text="25%", style={"width": "40px"})
                w.ProgressBar(value=25, style={"flex": "1"})

            with w.Row(gap=8, align="center"):
                w.Label(text="50%", style={"width": "40px"})
                w.ProgressBar(value=50, style={"flex": "1"})

            with w.Row(gap=8, align="center"):
                w.Label(text="75%", style={"width": "40px"})
                w.ProgressBar(value=75, style={"flex": "1"})

            with w.Row(gap=8, align="center"):
                w.Label(text="100%", style={"width": "40px"})
                w.ProgressBar(value=100, style={"flex": "1"})


@component
def TooltipSection() -> None:
    """Showcase tooltips."""
    with w.Card(padding=20):
        SectionHeader(
            title="Tooltips",
            description="Hover over elements to see tooltip positioning",
        )

        with w.Row(gap=16, justify="center"):
            with w.Tooltip(content="Tooltip on top", position="top"):
                w.Button(text="Top", variant="outline")

            with w.Tooltip(content="Tooltip on bottom", position="bottom"):
                w.Button(text="Bottom", variant="outline")

            with w.Tooltip(content="Tooltip on left", position="left"):
                w.Button(text="Left", variant="outline")

            with w.Tooltip(content="Tooltip on right", position="right"):
                w.Button(text="Right", variant="outline")


@component
def TypographySection() -> None:
    """Showcase typography widgets."""
    with w.Card(padding=20):
        SectionHeader(
            title="Typography",
            description="Headings and labels with various sizes",
        )

        with w.Column(gap=8):
            w.Heading(text="Heading 1", level=1)
            w.Heading(text="Heading 2", level=2)
            w.Heading(text="Heading 3", level=3)
            w.Heading(text="Heading 4", level=4)
            w.Divider()
            w.Label(text="Regular label text")
            w.Label(text="Bold label text", bold=True)
            w.Label(text="Secondary text color", color="#64748b")


# =============================================================================
# Main App
# =============================================================================


@component
def App() -> None:
    """Main showcase application."""
    state = ShowcaseState()

    with state:
        with w.Column(
            gap=16,
            style={
                "minHeight": "100vh",
                "padding": "24px",
                "maxWidth": "800px",
                "margin": "0 auto",
            },
        ):
            # Header
            with w.Column(gap=4, style={"marginBottom": "8px"}):
                w.Heading(text="Trellis Widget Showcase", level=1)
                w.Label(
                    text="A comprehensive demonstration of all available widgets",
                    color="#64748b",
                )

            # Widget sections
            ButtonsSection()
            FormInputsSection()
            StatusSection()
            TableSection()
            ProgressSection()
            TooltipSection()
            TypographySection()


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
