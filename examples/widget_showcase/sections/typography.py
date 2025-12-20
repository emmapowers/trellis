"""Typography section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Headings")
def Headings() -> None:
    """Heading elements at different levels."""
    with w.Column(gap=8):
        w.Heading(text="Heading 1", level=1)
        w.Heading(text="Heading 2", level=2)
        w.Heading(text="Heading 3", level=3)
        w.Heading(text="Heading 4", level=4)


@example("Labels")
def Labels() -> None:
    """Text labels with different styles."""
    with w.Column(gap=8):
        w.Label(text="Regular label text")
        w.Label(text="Bold label text", bold=True)
        w.Label(text="Secondary text color", color="#64748b")


@component
def TypographySection() -> None:
    """Showcase typography widgets."""
    with w.Column(gap=16):
        ExampleCard(example=Headings)
        ExampleCard(example=Labels)
