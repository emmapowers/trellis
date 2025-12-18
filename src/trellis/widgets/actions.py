"""Action widgets for Trellis.

Provides menu, toolbar, and action-related widgets.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Menu", has_children=True)
def Menu(
    *,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Menu container for menu items.

    Args:
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
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("MenuDivider")
def MenuDivider(
    *,
    key: str | None = None,
) -> ElementNode:
    """Horizontal divider between menu items."""
    ...


@react_component_base("Toolbar", has_children=True)
def Toolbar(
    *,
    variant: Literal["default", "minimal"] = "default",
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Horizontal toolbar container for action buttons.

    Args:
        variant: Visual style variant
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...
