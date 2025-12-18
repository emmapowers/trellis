"""Status indicators and badges section of the widget showcase."""

from trellis import component
from trellis import widgets as w


@component
def StatusSection() -> None:
    """Showcase status indicators and badges."""
    with w.Column(gap=16):
        # Status indicators
        w.Label(text="Status Indicators", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, style={"marginTop": "8px"}):
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
