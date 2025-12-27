"""Navigation widgets for Trellis.

Provides widgets for organizing and navigating content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Height, Margin, Padding, Width
from trellis.core.rendering.element import ElementNode
from trellis.core.state.mutable import Mutable

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Tabs", has_children=True)
def Tabs(
    *,
    selected: str | Mutable[str] | None = None,
    variant: Literal["line", "enclosed", "pills"] = "line",
    size: Literal["sm", "md"] = "md",
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Tab container for organizing content.

    Args:
        selected: ID of the currently selected tab. Use mutable(state.prop) for two-way binding.
        variant: Visual style variant
        size: Size variant
        margin: Margin around the tabs (Margin dataclass).
        width: Width of the tabs container (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("Tab", has_children=True)
def Tab(
    *,
    id: str,
    label: str,
    icon: str | None = None,
    disabled: bool = False,
    padding: Padding | int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Individual tab within a Tabs container.

    Args:
        id: Unique identifier for this tab
        label: Display label
        icon: Optional icon name
        disabled: Whether the tab is disabled
        padding: Padding inside the tab content (Padding dataclass or int for all sides).
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("Tree")
def Tree(
    *,
    data: list[dict[str, tp.Any]] | None = None,
    selected: str | None = None,
    expanded: list[str] | None = None,
    on_select: Callable[[str], None] | None = None,
    on_expand: Callable[[str, bool], None] | None = None,
    show_icons: bool = True,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Hierarchical tree view.

    Args:
        data: Tree nodes as [{id, label, children?, icon?}, ...]
        selected: ID of the selected node
        expanded: List of expanded node IDs
        on_select: Callback when a node is selected
        on_expand: Callback when a node is expanded/collapsed (id, is_expanded)
        show_icons: Whether to show folder/file icons
        margin: Margin around the tree (Margin dataclass).
        width: Width of the tree (Width dataclass, int for pixels, or str for CSS).
        height: Height of the tree (Height dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("Breadcrumb")
def Breadcrumb(
    *,
    items: list[dict[str, str]] | None = None,
    separator: str = "/",
    on_click: Callable[[int], None] | None = None,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Navigation breadcrumb trail.

    Args:
        items: Breadcrumb items as [{label, href?}, ...]
        separator: Separator character between items
        on_click: Callback when item is clicked (receives index)
        margin: Margin around the breadcrumb (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...
