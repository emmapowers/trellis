"""Navigation widgets for Trellis.

Provides widgets for organizing and navigating content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.composition import component
from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Height, Margin, Padding, Width
from trellis.core.rendering.element import Element
from trellis.core.state.mutable import Mutable
from trellis.html.links import A
from trellis.widgets.basic import Label

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Tabs", is_container=True)
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
) -> Element:
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


@react_component_base("Tab", is_container=True)
def Tab(
    *,
    id: str,
    label: str,
    icon: str | None = None,
    disabled: bool = False,
    padding: Padding | int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
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
) -> Element:
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


@react_component_base("BreadcrumbContainer", is_container=True)
def _BreadcrumbContainer(
    *,
    separator: str = "/",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Container that renders breadcrumb children with separators.

    This is the React-rendered container that handles layout and separators.
    Children are native Trellis elements (A for links, Label for current page).
    """
    ...


@component
def Breadcrumb(
    *,
    items: list[dict[str, str]] | None = None,
    separator: str = "/",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Navigation breadcrumb trail with router-integrated links.

    Each breadcrumb item with an href becomes a native html.A element that
    automatically uses client-side router navigation for relative URLs.
    The last item (or items without href) renders as a Label.

    Args:
        items: Breadcrumb items as [{label, href?}, ...]
        separator: Separator character between items
        margin: Margin around the breadcrumb (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles

    Example:
        Breadcrumb(items=[
            {"label": "Home", "href": "/"},
            {"label": "Products", "href": "/products"},
            {"label": "Widget"},  # Current page, no link
        ])
    """
    items_list = items or []

    with _BreadcrumbContainer(
        separator=separator,
        margin=margin,
        flex=flex,
        class_name=class_name,
        style=style,
    ):
        for i, item in enumerate(items_list):
            is_last = i == len(items_list) - 1
            label = item.get("label", "")
            href = item.get("href")

            # Last item or items without href are labels (current page)
            if is_last or href is None:
                Label(text=label)
            else:
                # Items with href become native anchors with router integration
                A(label, href=href)
