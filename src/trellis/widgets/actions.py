"""Action widgets for Trellis.

Provides menu, toolbar, and action-related widgets.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.element_node import ElementNode
from trellis.core.react_component import react_component_base
from trellis.core.style_props import Margin, Padding, Width

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Menu", has_children=True)
def Menu(
    *,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Menu container for menu items.

    Args:
        padding: Padding inside the menu (Padding dataclass or int for all sides).
        margin: Margin around the menu (Margin dataclass).
        width: Width of the menu (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("MenuItem")
def MenuItem(
    text: str = "",
    *,
    icon: str | None = None,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    shortcut: str | None = None,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Individual menu item.

    Args:
        text: Menu item label
        icon: Optional icon name
        on_click: Callback when clicked
        disabled: Whether item is disabled
        shortcut: Keyboard shortcut hint (display only)
        margin: Margin around the menu item (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("MenuDivider")
def MenuDivider(
    *,
    margin: Margin | None = None,
    key: str | None = None,
) -> ElementNode:
    """Horizontal divider between menu items.

    Args:
        margin: Margin around the divider (Margin dataclass).
        key: Unique key for reconciliation
    """
    ...


@react_component_base("Toolbar", has_children=True)
def Toolbar(
    *,
    variant: Literal["default", "minimal"] = "default",
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Toolbar container for action buttons with keyboard navigation.

    Args:
        variant: Visual style variant
        orientation: Layout direction (horizontal or vertical)
        padding: Padding inside the toolbar (Padding dataclass or int for all sides).
        margin: Margin around the toolbar (Margin dataclass).
        width: Width of the toolbar (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...
