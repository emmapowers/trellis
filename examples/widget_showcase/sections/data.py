"""Data display section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.icons import IconName


@component
def DataDisplaySection() -> None:
    """Showcase data display widgets."""
    with w.Column(gap=16):
        # Stats
        w.Label(text="Stats", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, style={"marginTop": "8px"}):
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

        # Tags
        w.Label(text="Tags", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=8, style={"marginTop": "8px"}):
            w.Tag(text="Default")
            w.Tag(text="Primary", variant="primary")
            w.Tag(text="Success", variant="success")
            w.Tag(text="Warning", variant="warning")
            w.Tag(text="Error", variant="error")
            w.Tag(text="Removable", variant="primary", removable=True)
