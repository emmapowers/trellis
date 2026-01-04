"""Basic UI widgets."""

from __future__ import annotations

import typing as tp

from trellis.core.components.composition import component
from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Margin, Padding, Width
from trellis.core.rendering.element import Element
from trellis.core.state.mutable import Mutable
from trellis.html.links import A
from trellis.widgets.icons import IconName

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
    text_align: tp.Literal["left", "center", "right"] | None = None,
    font_weight: tp.Literal["normal", "medium", "semibold", "bold"] | int | None = None,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Text display widget.

    Args:
        text: The text to display.
        font_size: Font size in pixels.
        color: Text color (CSS color string).
        bold: Whether to render text in bold.
        italic: Whether to render text in italics.
        text_align: Text alignment ("left", "center", "right").
        font_weight: Font weight as name ("normal", "medium", "semibold", "bold")
            or numeric value (100-900).
        padding: Padding around the text (Padding dataclass or int for all sides).
        margin: Margin around the label (Margin dataclass).
        width: Width of the label (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.

    Returns:
        An Element for the Label component.

    Example:
        Label(text="Hello, world!", font_size=16, color="blue")
        Label(text="Centered", text_align="center")
        Label(text="Light weight", font_weight=300)
    """
    ...


@component
def Button(
    text: str = "",
    *,
    icon: IconName | str | None = None,
    icon_position: tp.Literal["left", "right"] = "left",
    href: str | None = None,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    variant: tp.Literal["primary", "secondary", "outline", "ghost", "danger"] = "primary",
    size: tp.Literal["sm", "md", "lg"] = "md",
    full_width: bool = False,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Clickable button widget with modern styling.

    Args:
        text: The button label text.
        icon: Optional icon to display in the button (IconName enum or string).
        icon_position: Position of the icon relative to text ("left" or "right").
            Defaults to "left".
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
        margin: Margin around the button (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.

    Returns:
        An Element for the Button component.

    Example:
        Button(text="Save", on_click=save_handler, variant="primary")
        Button(text="Cancel", on_click=cancel_handler, variant="secondary")
        Button(text="Delete", on_click=delete_handler, variant="danger")
        Button(text="Add Item", icon=IconName.PLUS, on_click=add_handler)
        Button(icon=IconName.SETTINGS, variant="ghost")  # Icon-only button
    """
    if on_click is not None and href is not None:
        raise ValueError("Button cannot have both on_click and href set.")
    if href is not None:
        with A(href=href):
            _Button(
                text=text,
                icon=icon,
                icon_position=icon_position,
                on_click=None,
                disabled=disabled,
                variant=variant,
                size=size,
                full_width=full_width,
                margin=margin,
                flex=flex,
                class_name=class_name,
                style=style,
            )
    else:
        _Button(
            text=text,
            icon=icon,
            icon_position=icon_position,
            on_click=on_click,
            disabled=disabled,
            variant=variant,
            size=size,
            full_width=full_width,
            margin=margin,
            flex=flex,
            class_name=class_name,
            style=style,
        )


@react_component_base("Button")
def _Button(
    text: str = "",
    *,
    icon: IconName | str | None = None,
    icon_position: tp.Literal["left", "right"] = "left",
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    variant: tp.Literal["primary", "secondary", "outline", "ghost", "danger"] = "primary",
    size: tp.Literal["sm", "md", "lg"] = "md",
    full_width: bool = False,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element: ...


@react_component_base("Slider")
def Slider(
    *,
    value: float | Mutable[float] = 50,
    min: float = 0,
    max: float = 100,
    step: float = 1,
    disabled: bool = False,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Range slider widget.

    Args:
        value: Current slider value. Use mutable(state.prop) for two-way binding.
        min: Minimum value.
        max: Maximum value.
        step: Step increment.
        disabled: Whether the slider is disabled.
        margin: Margin around the slider (Margin dataclass).
        width: Width of the slider (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the Slider component.

    Example:
        Slider(value=mutable(state.slider_value), min=0, max=100)
    """
    ...


@react_component_base("TextInput")
def TextInput(
    value: str | Mutable[str] = "",
    *,
    placeholder: str | None = None,
    disabled: bool = False,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Single-line text input widget.

    Args:
        value: Current input value. Use mutable(state.prop) for two-way binding.
        placeholder: Placeholder text when empty.
        disabled: Whether the input is disabled.
        margin: Margin around the input (Margin dataclass).
        width: Width of the input (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the TextInput component.

    Example:
        TextInput(value=mutable(state.text), placeholder="Enter text...")
    """
    ...


@react_component_base("NumberInput")
def NumberInput(
    *,
    value: float | Mutable[float] | None = None,
    min: float | None = None,
    max: float | None = None,
    step: float | None = None,
    disabled: bool = False,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Numeric input widget.

    Args:
        value: Current numeric value. Use mutable(state.prop) for two-way binding,
            or callback(state.prop, handler) for custom processing.
        min: Minimum allowed value.
        max: Maximum allowed value.
        step: Step increment for value changes.
        disabled: Whether the input is disabled.
        margin: Margin around the input (Margin dataclass).
        width: Width of the input (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the NumberInput component.

    Example:
        NumberInput(value=mutable(state.count), min=0, max=100, step=1)
    """
    ...


@react_component_base("Checkbox")
def Checkbox(
    *,
    checked: bool | Mutable[bool] = False,
    label: str | None = None,
    disabled: bool = False,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Checkbox toggle widget.

    Args:
        checked: Whether the checkbox is checked. Use mutable(state.prop) for two-way binding.
        label: Optional label text displayed next to the checkbox.
        disabled: Whether the checkbox is disabled.
        margin: Margin around the checkbox (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the Checkbox component.

    Example:
        Checkbox(checked=mutable(state.enabled), label="Enable feature")
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
) -> Element:
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
        An Element for the Divider component.

    Example:
        Divider()  # horizontal divider
        Divider(orientation="vertical", margin=12)  # vertical divider in a Row
    """
    ...


@react_component_base("Select")
def Select(
    *,
    value: str | Mutable[str] | None = None,
    options: list[dict[str, str]] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Single-selection dropdown widget.

    Args:
        value: Currently selected value. Use mutable(state.prop) for two-way binding.
        options: List of option dicts with "value" and "label" keys.
        placeholder: Placeholder text when no value selected.
        disabled: Whether the select is disabled.
        margin: Margin around the select (Margin dataclass).
        width: Width of the select (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the Select component.

    Example:
        Select(
            value=mutable(state.selected_option),
            options=[{"value": "opt1", "label": "Option 1"}, {"value": "opt2", "label": "Option 2"}],
        )
    """
    ...


@react_component_base("Heading")
def Heading(
    text: str = "",
    *,
    level: tp.Literal[1, 2, 3, 4, 5, 6] = 1,
    color: str | None = None,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Semantic heading widget.

    Renders an HTML heading element (<h1> through <h6>) based on the level.

    Args:
        text: The heading text to display.
        level: Heading level from 1-6, corresponding to <h1>-<h6>. Defaults to 1.
        color: Text color (CSS color string).
        margin: Margin around the heading (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the Heading component.

    Example:
        Heading(text="Welcome", level=1)
        Heading(text="Section Title", level=2, color="#333")
    """
    ...


@react_component_base("ProgressBar")
def ProgressBar(
    *,
    value: float = 0,
    min: float = 0,
    max: float = 100,
    loading: bool = False,
    disabled: bool = False,
    color: str | None = None,
    height: int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Progress bar widget.

    Displays a horizontal progress indicator with optional loading animation.

    Args:
        value: Current progress value. Defaults to 0.
        min: Minimum value. Defaults to 0.
        max: Maximum value. Defaults to 100.
        loading: Whether to show indeterminate loading animation. Defaults to False.
        disabled: Whether the progress bar is disabled (grayed out). Defaults to False.
        color: Fill color (CSS color string). Defaults to indigo (#6366f1).
        height: Bar height in pixels. Defaults to 8.
        margin: Margin around the progress bar (Margin dataclass).
        width: Width of the progress bar (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the ProgressBar component.

    Example:
        ProgressBar(value=50, min=0, max=100)
        ProgressBar(loading=True)  # Indeterminate loading state
    """
    ...


@react_component_base("StatusIndicator")
def StatusIndicator(
    *,
    status: tp.Literal["success", "error", "warning", "pending", "info"] = "pending",
    label: str | None = None,
    show_icon: bool = True,
    size: tp.Literal["sm", "md"] = "md",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Status indicator with icon and optional label.

    Displays a semantic status (success, error, warning, etc.) with an icon
    and optional text label. Useful for showing operation status, validation
    state, or data health indicators.

    Args:
        status: The status type to display. One of:
            - "success": Green checkmark (✓)
            - "error": Red X (✗)
            - "warning": Amber warning (⚠)
            - "pending": Gray circle (○)
            - "info": Blue info (i)
        label: Optional text label to display next to the icon.
        show_icon: Whether to show the status icon. Defaults to True.
        size: Icon and text size. One of "sm", "md" (default).
        margin: Margin around the indicator (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the StatusIndicator component.

    Example:
        StatusIndicator(status="success", label="Passed")
        StatusIndicator(status="error", label="Failed")
        StatusIndicator(status="pending")  # Icon only
    """
    ...


@react_component_base("Badge")
def Badge(
    text: str = "",
    *,
    variant: tp.Literal["default", "success", "error", "warning", "info"] = "default",
    size: tp.Literal["sm", "md"] = "sm",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Small badge for counts or status labels.

    Displays a compact, pill-shaped badge with semantic coloring.
    Useful for tags, counts, status labels, or metadata.

    Args:
        text: The badge text to display.
        variant: Badge color variant. One of:
            - "default": Neutral gray
            - "success": Green
            - "error": Red
            - "warning": Amber
            - "info": Blue
        size: Badge size. One of "sm" (default), "md".
        margin: Margin around the badge (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An Element for the Badge component.

    Example:
        Badge(text="New", variant="success")
        Badge(text="3", variant="error")  # Count badge
        Badge(text="Beta", variant="info")
    """
    ...


@react_component_base("Tooltip", is_container=True)
def Tooltip(
    content: str = "",
    *,
    position: tp.Literal["top", "bottom", "left", "right"] = "top",
    delay: int = 200,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Tooltip wrapper for hover hints.

    Wraps child elements and shows a tooltip on hover. The tooltip appears
    after a short delay and hides when the mouse leaves.

    Args:
        content: The tooltip text to display on hover.
        position: Where the tooltip appears relative to the target. One of:
            - "top": Above the element (default)
            - "bottom": Below the element
            - "left": To the left of the element
            - "right": To the right of the element
        delay: Delay in milliseconds before showing tooltip. Defaults to 200.
        margin: Margin around the tooltip wrapper (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply to the wrapper.
        style: Additional inline styles to apply to the wrapper.
        key: Optional key for reconciliation.

    Returns:
        An Element for the Tooltip component.

    Example:
        with w.Tooltip(content="Click to save"):
            w.Button(text="Save")
    """
    ...
