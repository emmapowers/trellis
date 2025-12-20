"""Progress bars section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Determinate Progress")
def DeterminateProgress() -> None:
    """Progress bars with specific values."""
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


@example("Indeterminate Progress")
def IndeterminateProgress() -> None:
    """Loading state with animated progress."""
    with w.Row(gap=8, align="center"):
        w.Label(text="Loading", style={"width": "60px"})
        w.ProgressBar(loading=True, style={"flex": "1"})


@component
def ProgressSection() -> None:
    """Showcase progress bars."""
    with w.Column(gap=16):
        ExampleCard(example=DeterminateProgress)
        ExampleCard(example=IndeterminateProgress)
