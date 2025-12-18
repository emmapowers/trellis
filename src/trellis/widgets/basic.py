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


@react_component_base("Heading")
def Heading(
    text: str = "",
    *,
    level: tp.Literal[1, 2, 3, 4, 5, 6] = 1,
    color: str | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Semantic heading widget.

    Renders an HTML heading element (<h1> through <h6>) based on the level.

    Args:
        text: The heading text to display.
        level: Heading level from 1-6, corresponding to <h1>-<h6>. Defaults to 1.
        color: Text color (CSS color string).
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Heading component.

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
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
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
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the ProgressBar component.

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
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
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
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the StatusIndicator component.

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
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
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
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Badge component.

    Example:
        Badge(text="New", variant="success")
        Badge(text="3", variant="error")  # Count badge
        Badge(text="Beta", variant="info")
    """
    ...


@react_component_base("Tooltip", has_children=True)
def Tooltip(
    content: str = "",
    *,
    position: tp.Literal["top", "bottom", "left", "right"] = "top",
    delay: int = 200,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
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
        class_name: CSS class name(s) to apply to the wrapper.
        style: Additional inline styles to apply to the wrapper.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Tooltip component.

    Example:
        with w.Tooltip(content="Click to save"):
            w.Button(text="Save")
    """
    ...


@react_component_base("Table")
def Table(
    *,
    columns: list[dict[str, tp.Any]] | None = None,
    data: list[dict[str, tp.Any]] | None = None,
    striped: bool = False,
    compact: bool = True,
    bordered: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Data table widget.

    Displays tabular data with configurable columns. Supports striped rows,
    compact mode, and bordered styling for data-dense dashboard displays.

    Args:
        columns: List of column definitions. Each dict should have:
            - "key": The data key to display in this column (required)
            - "label": The column header text (required)
            - "width": Optional column width (CSS string, e.g., "100px", "20%")
            - "align": Text alignment ("left", "center", "right")
        data: List of row data dicts. Keys should match column keys.
        striped: Whether to show alternating row colors. Defaults to False.
        compact: Whether to use compact row height. Defaults to True.
        bordered: Whether to show cell borders. Defaults to False.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Table component.

    Example:
        Table(
            columns=[
                {"key": "name", "label": "Name"},
                {"key": "status", "label": "Status", "align": "center"},
                {"key": "value", "label": "Value", "align": "right"},
            ],
            data=[
                {"name": "Item 1", "status": "Active", "value": 100},
                {"name": "Item 2", "status": "Pending", "value": 50},
            ],
            striped=True,
        )
    """
    ...
