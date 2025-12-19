"""Feedback section of the widget showcase."""

from trellis import component
from trellis import widgets as w


@component
def FeedbackSection() -> None:
    """Showcase feedback widgets."""
    with w.Column(gap=16):
        # Callouts
        w.Label(text="Callouts", font_size=12, color="#64748b", bold=True)
        with w.Column(gap=8, style={"marginTop": "8px"}):
            with w.Callout(title="Information", intent="info"):
                w.Label(text="This is an informational message.")
            with w.Callout(title="Success", intent="success"):
                w.Label(text="Operation completed successfully.")
            with w.Callout(title="Warning", intent="warning"):
                w.Label(text="Please review before continuing.")
            with w.Callout(title="Error", intent="error", dismissible=True):
                w.Label(text="An error occurred. Please try again.")
