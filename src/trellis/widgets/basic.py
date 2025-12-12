"""Basic UI widgets."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.react_component import ReactComponent, react_component
from trellis.core.rendering import ElementNode

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component("Slider")
@dataclass(kw_only=True)
class _SliderComponent(ReactComponent):
    """Range slider widget."""

    name: str = "Slider"


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
_slider = _SliderComponent()
_label = _LabelComponent()
_button = _ButtonComponent()


def Label(
    text: str = "",
    *,
    font_size: int | None = None,
    color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Text display widget.

    Args:
        text: The text to display.
        font_size: Font size in pixels.
        color: Text color (CSS color string).
        bold: Whether to render text in bold.
        italic: Whether to render text in italics.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Label component.

    Example:
        Label(text="Hello, world!", font_size=16, color="blue")
    """
    return _label(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        italic=italic,
        className=class_name,
        style=style,
        key=key,
    )


def Button(
    text: str = "",
    *,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    variant: tp.Literal["primary", "secondary", "outline", "ghost", "danger"] = "primary",
    size: tp.Literal["sm", "md", "lg"] = "md",
    full_width: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Clickable button widget with modern styling.

    Args:
        text: The button label text.
        on_click: Callback invoked when the button is clicked.
        disabled: Whether the button is disabled.
        variant: Button style variant. One of:
            - "primary": Solid background, high emphasis (default)
            - "secondary": Subtle background, medium emphasis
            - "outline": Border only, low emphasis
            - "ghost": No background/border, minimal emphasis
            - "danger": Red/destructive action
        size: Button size. One of "sm", "md" (default), "lg".
        full_width: Whether button should take full container width.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Button component.

    Example:
        Button(text="Save", on_click=save_handler, variant="primary")
        Button(text="Cancel", on_click=cancel_handler, variant="secondary")
        Button(text="Delete", on_click=delete_handler, variant="danger")
    """
    return _button(
        text=text,
        on_click=on_click,
        disabled=disabled,
        variant=variant,
        size=size,
        full_width=full_width,
        className=class_name,
        style=style,
        key=key,
    )


def Slider(
    *,
    value: float = 50,
    min: float = 0,
    max: float = 100,
    step: float = 1,
    on_change: Callable[[float], None] | None = None,
    disabled: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Range slider widget.

    Args:
        value: Current slider value.
        min: Minimum value.
        max: Maximum value.
        step: Step increment.
        on_change: Callback invoked with new value when slider changes.
        disabled: Whether the slider is disabled.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Slider component.

    Example:
        Slider(value=50, min=0, max=100, on_change=handle_change)
    """
    return _slider(
        value=value,
        min=min,
        max=max,
        step=step,
        on_change=on_change,
        disabled=disabled,
        className=class_name,
        style=style,
        key=key,
    )
