"""Data display section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.widgets import IconName
from trellis.app import theme

from ..components import ExampleCard
from ..example import example


@example("Stats")
def Stats() -> None:
    """Key metrics with delta indicators."""
    with w.Row(gap=16):
        w.Stat(
            label="Revenue",
            value="$12,450",
            delta="+12%",
            delta_type="increase",
            icon=IconName.TRENDING_UP,
        )
        w.Stat(
            label="Users",
            value="1,234",
            delta="-5%",
            delta_type="decrease",
            icon=IconName.USERS,
        )
        w.Stat(
            label="Orders",
            value="456",
            delta="0%",
            delta_type="neutral",
            icon=IconName.ACTIVITY,
        )


@example("Tags")
def Tags() -> None:
    """Categorization labels."""
    with w.Row(gap=8):
        w.Tag(text="Default")
        w.Tag(text="Primary", variant="primary")
        w.Tag(text="Success", variant="success")
        w.Tag(text="Warning", variant="warning")
        w.Tag(text="Error", variant="error")
        w.Tag(text="Removable", variant="primary", removable=True)


@component
def DataDisplaySection() -> None:
    """Showcase data display widgets."""
    with w.Column(gap=16):
        ExampleCard(example=Stats)
        ExampleCard(example=Tags)
