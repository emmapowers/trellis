"""Data display widgets for Trellis.

Provides widgets for displaying metrics, stats, and tagged data.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Margin, Padding, Width
from trellis.core.rendering.element import Element

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Stat")
def Stat(
    *,
    label: str = "",
    value: str = "",
    delta: str | None = None,
    delta_type: Literal["increase", "decrease", "neutral"] | None = None,
    icon: str | None = None,
    size: Literal["sm", "md", "lg"] = "md",
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Display a key metric with label, value, and optional trend.

    Args:
        label: Descriptive label for the metric
        value: The main value to display
        delta: Change indicator (e.g., "+12%", "-5%")
        delta_type: Visual style for delta ("increase" = green, "decrease" = red)
        icon: Optional icon name to display
        size: Size variant ("sm", "md", "lg")
        padding: Padding inside the stat (Padding dataclass or int for all sides).
        margin: Margin around the stat (Margin dataclass).
        width: Width of the stat (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("Tag")
def Tag(
    text: str = "",
    *,
    variant: Literal["default", "primary", "success", "warning", "error"] = "default",
    removable: bool = False,
    on_remove: Callable[[], None] | None = None,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Display a tag/chip label.

    Args:
        text: The tag text
        variant: Color variant
        removable: Whether to show a remove button
        on_remove: Callback when remove is clicked
        margin: Margin around the tag (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...
