"""Typography section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.app import theme

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
        w.Label(text="Secondary text color", color=theme.text_secondary)


_MARKDOWN_SAMPLE = """\
# Markdown

This is a formatting-focused markdown sample for Trellis.

- Bullet item one
- Bullet item two

```python
def greet(name: str) -> str:
    return f"hello {name}"
```

Visit [Trellis on GitHub](https://github.com/emmapowers/trellis).
"""


@example("Markdown")
def MarkdownExample() -> None:
    """Markdown renderer example with common formatting."""
    w.Markdown(content=_MARKDOWN_SAMPLE)


@component
def TypographySection() -> None:
    """Showcase typography widgets."""
    with w.Column(gap=16):
        ExampleCard(example=Headings)
        ExampleCard(example=Labels)
        ExampleCard(example=MarkdownExample)
