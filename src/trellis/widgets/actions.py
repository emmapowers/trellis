"""Action widgets for Trellis.

Provides menu, toolbar, and action-related widgets.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.react import react
from trellis.html._style_runtime import SpacingInput, StyleInput, WidthInput

if tp.TYPE_CHECKING:
    from collections.abc import Callable

_ARIA_PACKAGES = {"react-aria": "3.35.0", "react-stately": "3.33.0"}


@react("client/Menu.tsx", is_container=True, packages=_ARIA_PACKAGES)
def Menu(
    *,
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Menu container for menu items.

    Args:
        padding: Padding inside the menu (CSS padding value).
        margin: Margin around the menu (CSS margin value).
        width: Width of the menu (CSS width value).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
    """
    pass


@react("client/Menu.tsx", export_name="MenuItem")
def MenuItem(
    text: str = "",
    *,
    icon: str | None = None,
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    shortcut: str | None = None,
    margin: SpacingInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Individual menu item.

    Args:
        text: Menu item label
        icon: Optional icon name
        on_click: Callback when clicked
        disabled: Whether item is disabled
        shortcut: Keyboard shortcut hint (display only)
        margin: Margin around the menu item (CSS margin value).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
    """
    pass


@react("client/Menu.tsx", export_name="MenuDivider")
def MenuDivider(
    *,
    margin: SpacingInput | None = None,
) -> None:
    """Horizontal divider between menu items.

    Args:
        margin: Margin around the divider (CSS margin value).
    """
    pass


@react("client/Toolbar.tsx", is_container=True, packages=_ARIA_PACKAGES)
def Toolbar(
    *,
    variant: Literal["default", "minimal"] = "default",
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Toolbar container for action buttons with keyboard navigation.

    Args:
        variant: Visual style variant
        orientation: Layout direction (horizontal or vertical)
        padding: Padding inside the toolbar (CSS padding value).
        margin: Margin around the toolbar (CSS margin value).
        width: Width of the toolbar (CSS width value).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
    """
    pass
