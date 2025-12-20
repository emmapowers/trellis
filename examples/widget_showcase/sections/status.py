"""Status indicators and badges section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Status Indicators")
def StatusIndicators() -> None:
    """Visual indicators for different states."""
    with w.Row(gap=16):
        w.StatusIndicator(status="success", label="Success")
        w.StatusIndicator(status="error", label="Error")
        w.StatusIndicator(status="warning", label="Warning")
        w.StatusIndicator(status="pending", label="Pending")
        w.StatusIndicator(status="info", label="Info")


@example("Badges")
def BadgeVariants() -> None:
    """Small labels for categorization."""
    with w.Row(gap=8):
        w.Badge(text="Default")
        w.Badge(text="Success", variant="success")
        w.Badge(text="Error", variant="error")
        w.Badge(text="Warning", variant="warning")
        w.Badge(text="Info", variant="info")


@component
def StatusSection() -> None:
    """Showcase status indicators and badges."""
    with w.Column(gap=16):
        ExampleCard(example=StatusIndicators)
        ExampleCard(example=BadgeVariants)
