"""Navigation widgets for Trellis.

Provides widgets for organizing and navigating content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Tabs", has_children=True)
def Tabs(
    *,
    selected: str | None = None,
    on_change: Callable[[str], None] | None = None,
    variant: Literal["line", "enclosed", "pills"] = "line",
    size: Literal["sm", "md"] = "md",
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Tab container for organizing content.

    Args:
        selected: ID of the currently selected tab
        on_change: Callback when tab selection changes
        variant: Visual style variant
        size: Size variant
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
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Navigation breadcrumb trail.

    Args:
        items: Breadcrumb items as [{label, href?}, ...]
        separator: Separator character between items
        on_click: Callback when item is clicked (receives index)
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...
