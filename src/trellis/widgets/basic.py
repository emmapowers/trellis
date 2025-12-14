"""Basic UI widgets."""

from __future__ import annotations

import typing as tp

from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Label")
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
    ...


@react_component_base("Button")
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
    ...


@react_component_base("Slider")
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
    ...


@react_component_base("TextInput")
def TextInput(
    value: str = "",
    *,
    placeholder: str | None = None,
    on_change: Callable[[str], None] | None = None,
    disabled: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Single-line text input widget.

    Args:
        value: Current input value.
        placeholder: Placeholder text when empty.
        on_change: Callback invoked with new value when input changes.
        disabled: Whether the input is disabled.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the TextInput component.

    Example:
        TextInput(value="hello", placeholder="Enter text...", on_change=handle_change)
    """
    ...


@react_component_base("NumberInput")
def NumberInput(
    *,
    value: float | None = None,
    min: float | None = None,
    max: float | None = None,
    step: float | None = None,
    on_change: Callable[[float], None] | None = None,
    disabled: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Numeric input widget.

    Args:
        value: Current numeric value.
        min: Minimum allowed value.
        max: Maximum allowed value.
        step: Step increment for value changes.
        on_change: Callback invoked with new value when input changes.
        disabled: Whether the input is disabled.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the NumberInput component.

    Example:
        NumberInput(value=42, min=0, max=100, step=1, on_change=handle_change)
    """
    ...


@react_component_base("Checkbox")
def Checkbox(
    *,
    checked: bool = False,
    label: str | None = None,
    on_change: Callable[[bool], None] | None = None,
    disabled: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Checkbox toggle widget.

    Args:
        checked: Whether the checkbox is checked.
        label: Optional label text displayed next to the checkbox.
        on_change: Callback invoked with new checked state when toggled.
        disabled: Whether the checkbox is disabled.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Checkbox component.

    Example:
        Checkbox(checked=True, label="Enable feature", on_change=handle_toggle)
    """
    ...


@react_component_base("Divider")
def Divider(
    *,
    orientation: tp.Literal["horizontal", "vertical"] = "horizontal",
    margin: int | None = None,
    color: str | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Divider line for separating content.

    Args:
        orientation: Direction of the divider. Use "horizontal" in Column,
            "vertical" in Row. Defaults to "horizontal".
        margin: Margin in pixels (vertical for horizontal, horizontal for vertical).
            Defaults to 16.
        color: Line color (CSS color string). Defaults to #334155.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Divider component.

    Example:
        Divider()  # horizontal divider
        Divider(orientation="vertical", margin=12)  # vertical divider in a Row
    """
    ...


@react_component_base("Select")
def Select(
    *,
    value: str | None = None,
    options: list[dict[str, str]] | None = None,
    on_change: Callable[[str], None] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Single-selection dropdown widget.

    Args:
        value: Currently selected value.
        options: List of option dicts with "value" and "label" keys.
        on_change: Callback invoked with selected value when selection changes.
        placeholder: Placeholder text when no value selected.
        disabled: Whether the select is disabled.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Select component.

    Example:
        Select(
            value="opt1",
            options=[{"value": "opt1", "label": "Option 1"}, {"value": "opt2", "label": "Option 2"}],
            on_change=handle_select,
        )
    """
    ...
