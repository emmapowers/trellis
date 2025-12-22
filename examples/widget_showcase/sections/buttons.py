"""Buttons section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Variants")
def ButtonVariants() -> None:
    """Different button styles for various contexts."""
    with w.Row(gap=8):
        w.Button(text="Primary", variant="primary")
        w.Button(text="Secondary", variant="secondary")
        w.Button(text="Outline", variant="outline")
        w.Button(text="Ghost", variant="ghost")
        w.Button(text="Danger", variant="danger")


@example("Sizes")
def ButtonSizes() -> None:
    """Button size options."""
    with w.Row(gap=8, align="center"):
        w.Button(text="Small", size="sm")
        w.Button(text="Medium", size="md")
        w.Button(text="Large", size="lg")


@example("Disabled")
def ButtonDisabled() -> None:
    """Disabled button states."""
    with w.Row(gap=8):
        w.Button(text="Disabled Primary", variant="primary", disabled=True)
        w.Button(text="Disabled Secondary", variant="secondary", disabled=True)


@component
def ButtonsSection() -> None:
    """Showcase all button variants and sizes."""
    with w.Column(gap=16):
        ExampleCard(example=ButtonVariants)
        ExampleCard(example=ButtonSizes)
        ExampleCard(example=ButtonDisabled)
