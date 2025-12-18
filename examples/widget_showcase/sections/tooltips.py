"""Tooltips section of the widget showcase."""

from trellis import component
from trellis import widgets as w


@component
def TooltipSection() -> None:
    """Showcase tooltips."""
    with w.Row(gap=16, justify="center"):
        with w.Tooltip(content="Tooltip on top", position="top"):
            w.Button(text="Top", variant="outline")

        with w.Tooltip(content="Tooltip on bottom", position="bottom"):
            w.Button(text="Bottom", variant="outline")

        with w.Tooltip(content="Tooltip on left", position="left"):
            w.Button(text="Left", variant="outline")

        with w.Tooltip(content="Tooltip on right", position="right"):
            w.Button(text="Right", variant="outline")
