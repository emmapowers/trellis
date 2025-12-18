"""Buttons section of the widget showcase."""

from trellis import component
from trellis import widgets as w


@component
def ButtonsSection() -> None:
    """Showcase all button variants and sizes."""
    with w.Column(gap=16):
        # Variants
        w.Label(text="Variants", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=8, style={"marginTop": "8px"}):
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

        # Disabled state
        w.Label(text="Disabled", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=8, style={"marginTop": "8px"}):
            w.Button(text="Disabled Primary", variant="primary", disabled=True)
            w.Button(text="Disabled Secondary", variant="secondary", disabled=True)
