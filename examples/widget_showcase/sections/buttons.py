"""Buttons section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.widgets import IconName

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


@example("With Icons")
def ButtonWithIcons() -> None:
    """Buttons with icons on left or right."""
    with w.Row(gap=8):
        w.Button(text="Add Item", icon=IconName.PLUS, variant="primary")
        w.Button(text="Download", icon=IconName.DOWNLOAD, variant="secondary")
        w.Button(text="Next", icon=IconName.ARROW_RIGHT, icon_position="right", variant="outline")
        w.Button(text="Delete", icon=IconName.TRASH, variant="danger")


@example("Icon Only")
def ButtonIconOnly() -> None:
    """Compact icon-only buttons."""
    with w.Row(gap=8):
        w.Button(icon=IconName.PLUS, variant="primary")
        w.Button(icon=IconName.EDIT, variant="secondary")
        w.Button(icon=IconName.COPY, variant="outline")
        w.Button(icon=IconName.SETTINGS, variant="ghost")
        w.Button(icon=IconName.TRASH, variant="danger")


@example("Disabled")
def ButtonDisabled() -> None:
    """Disabled button states."""
    with w.Row(gap=8):
        w.Button(text="Disabled Primary", variant="primary", disabled=True)
        w.Button(text="Disabled", icon=IconName.SAVE, variant="secondary", disabled=True)


@component
def ButtonsSection() -> None:
    """Showcase all button variants and sizes."""
    with w.Column(gap=16):
        ExampleCard(example=ButtonVariants)
        ExampleCard(example=ButtonSizes)
        ExampleCard(example=ButtonWithIcons)
        ExampleCard(example=ButtonIconOnly)
        ExampleCard(example=ButtonDisabled)
