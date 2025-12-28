"""Reusable components for the widget showcase."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis import Stateful, component
from trellis import html as h
from trellis import widgets as w
from trellis.widgets import theme

from .example import make_playground_url

if tp.TYPE_CHECKING:
    from trellis.core.components.composition import CompositionComponent


@component
def CodeBlock(*, code: str) -> None:
    """Display code in a monospace styled block.

    Args:
        code: The source code to display.
    """
    w.Label(
        text=code,
        style={
            "fontFamily": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            "fontSize": "13px",
            "lineHeight": "1.5",
            "whiteSpace": "pre",
            "backgroundColor": "#000000",
            "color": "#e2e8f0",
            "padding": "16px",
            "borderRadius": "6px",
            "overflow": "auto",
            "display": "block",
        },
    )


@dataclass
class ExampleCardState(Stateful):
    """State for ExampleCard code visibility."""

    show_code: bool = False


@component
def ExampleCard(*, example: CompositionComponent) -> None:
    """Card wrapper for examples with code display and playground link.

    Args:
        example: An example component created with @example decorator.
            Must have .title, .source, and .func_name attributes.
    """
    state = ExampleCardState()

    title: str = getattr(example, "title", "Example")
    source: str = getattr(example, "source", "")
    func_name: str = getattr(example, "func_name", "example")

    with w.Column(gap=12):
        # Header with title and action buttons
        with w.Row(justify="between", align="center"):
            w.Label(text=title, font_size=12, color=theme.text_secondary, bold=True)

            with w.Row(gap=4):
                w.Button(
                    text="Code" if not state.show_code else "Hide",
                    variant="ghost",
                    size="sm",
                    on_click=lambda: setattr(state, "show_code", not state.show_code),
                )
                with h.A(
                    href=make_playground_url(source, func_name),
                    target="_blank",
                    style={"textDecoration": "none"},
                ):
                    w.Button(
                        text="Playground",
                        variant="ghost",
                        size="sm",
                    )

        # Render the example
        example()

        # Show code block if toggled
        if state.show_code:
            CodeBlock(code=source)
