"""Data display widgets for Trellis.

Provides widgets for displaying metrics, stats, and tagged data.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.react import react
from trellis.html._style_runtime import SpacingInput, StyleInput, WidthInput

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react("client/Stat.tsx")
def Stat(
    *,
    label: str = "",
    value: str = "",
    delta: str | None = None,
    delta_type: Literal["increase", "decrease", "neutral"] | None = None,
    icon: str | None = None,
    size: Literal["sm", "md", "lg"] = "md",
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Display a key metric with label, value, and optional trend.

    Args:
        label: Descriptive label for the metric
        value: The main value to display
        delta: Change indicator (e.g., "+12%", "-5%")
        delta_type: Visual style for delta ("increase" = green, "decrease" = red)
        icon: Optional icon name to display
        size: Size variant ("sm", "md", "lg")
        padding: Padding inside the stat (CSS padding value).
        margin: Margin around the stat (CSS margin value).
        width: Width of the stat (CSS width value).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    pass


@react("client/Tag.tsx")
def Tag(
    text: str = "",
    *,
    variant: Literal["default", "primary", "success", "warning", "error"] = "default",
    removable: bool = False,
    on_remove: Callable[[], None] | None = None,
    margin: SpacingInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Display a tag/chip label.

    Args:
        text: The tag text
        variant: Color variant
        removable: Whether to show a remove button
        on_remove: Callback when remove is clicked
        margin: Margin around the tag (CSS margin value).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    pass
