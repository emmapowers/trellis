"""Basic UI widgets."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.react_component import ReactComponent, react_component
from trellis.core.rendering import ElementDescriptor

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component("Label")
@dataclass(kw_only=True)
class _LabelComponent(ReactComponent):
    """Text display widget."""

    name: str = "Label"


@react_component("Button")
@dataclass(kw_only=True)
class _ButtonComponent(ReactComponent):
    """Clickable button widget."""

    name: str = "Button"


# Singleton instances used by factory functions
_label = _LabelComponent()
_button = _ButtonComponent()


def Label(
    text: str = "",
    *,
    font_size: int | None = None,
    color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    key: str | None = None,
) -> ElementDescriptor:
    """Text display widget.

    Args:
        text: The text to display.
        font_size: Font size in pixels.
        color: Text color (CSS color string).
        bold: Whether to render text in bold.
        italic: Whether to render text in italics.
        key: Optional key for reconciliation.

    Returns:
        An ElementDescriptor for the Label component.

    Example:
        Label(text="Hello, world!", font_size=16, color="blue")
    """
    return _label(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        italic=italic,
        key=key,
    )


def Button(
    text: str = "",
    *,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    key: str | None = None,
) -> ElementDescriptor:
    """Clickable button widget.

    Args:
        text: The button label text.
        on_click: Callback invoked when the button is clicked.
        disabled: Whether the button is disabled.
        key: Optional key for reconciliation.

    Returns:
        An ElementDescriptor for the Button component.

    Example:
        Button(text="Click me", on_click=lambda: print("clicked!"))
    """
    return _button(
        text=text,
        on_click=on_click,
        disabled=disabled,
        key=key,
    )
