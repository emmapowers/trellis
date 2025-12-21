"""Progress bars section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Progress Bars")
def ProgressBars() -> None:
    """Determinate and indeterminate progress indicators."""
    with w.Column(gap=12):
        with w.Row(gap=8, align="center"):
            w.Label(text="25%", width=40)
            w.ProgressBar(value=25, flex=1)

        with w.Row(gap=8, align="center"):
            w.Label(text="50%", width=40)
            w.ProgressBar(value=50, flex=1)

        with w.Row(gap=8, align="center"):
            w.Label(text="75%", width=40)
            w.ProgressBar(value=75, flex=1)

        with w.Row(gap=8, align="center"):
            w.Label(text="100%", width=40)
            w.ProgressBar(value=100, flex=1)

        with w.Row(gap=8, align="center"):
            w.Label(text="Loading", width=60)
            w.ProgressBar(loading=True, flex=1)


@component
def ProgressSection() -> None:
    """Showcase progress bars."""
    with w.Column(gap=16):
        ExampleCard(example=ProgressBars)
