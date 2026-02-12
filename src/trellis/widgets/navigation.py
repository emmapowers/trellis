"""Navigation widgets for Trellis.

Provides widgets for organizing and navigating content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.composition import component
from trellis.core.components.react import react
from trellis.core.components.style_props import Height, Margin, Padding, Width
from trellis.core.state.mutable import Mutable
from trellis.html.layout import Nav, Span
from trellis.html.links import A
from trellis.html.lists import Li, Ol

if tp.TYPE_CHECKING:
    from collections.abc import Callable

# Typography settings for server-side rendered components
_ARIA_PACKAGES = {"react-aria": "3.35.0", "react-stately": "3.33.0"}

_FONT_FAMILY = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
)


@react("client/Tabs.tsx", is_container=True, packages=_ARIA_PACKAGES)
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
) -> None:
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
    pass


@react("client/Tabs.tsx", export_name="Tab", is_container=True)
def Tab(
    *,
    id: str,
    label: str,
    icon: str | None = None,
    disabled: bool = False,
    padding: Padding | int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
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
    pass


@react("client/Tree.tsx")
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
) -> None:
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
    pass


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
    The last item (or items without href) renders as plain text.

    Args:
        items: Breadcrumb items as [{label, href?}, ...]
        separator: Separator character between items ("/" renders as chevron)
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

    # Build nav styles
    nav_style: dict[str, tp.Any] = {
        "display": "flex",
        "alignItems": "center",
        "fontFamily": _FONT_FAMILY,
        "fontSize": "0.875rem",
        "lineHeight": "1.5",
    }
    if margin:
        if margin.top is not None:
            nav_style["marginTop"] = f"{margin.top}px"
        if margin.right is not None:
            nav_style["marginRight"] = f"{margin.right}px"
        if margin.bottom is not None:
            nav_style["marginBottom"] = f"{margin.bottom}px"
        if margin.left is not None:
            nav_style["marginLeft"] = f"{margin.left}px"
    if flex is not None:
        nav_style["flex"] = flex
    if style:
        nav_style.update(style)

    # Use chevron character when separator is "/"
    # U+203A SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    sep_char = "\u203a" if separator == "/" else separator

    with Nav(
        className=class_name or "",
        style=nav_style,
        role="navigation",
        **{"aria-label": "Breadcrumb"},
    ):
        with Ol(
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "4px",
                "listStyle": "none",
                "margin": "0",
                "padding": "0",
            }
        ):
            for i, item in enumerate(items_list):
                is_last = i == len(items_list) - 1
                label = item.get("label", "")
                href = item.get("href")

                with Li(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "4px",
                    }
                ):
                    # Separator before non-first items
                    if i > 0:
                        # aria-hidden passed as kwarg for accessibility
                        aria_props: dict[str, tp.Any] = {"aria-hidden": "true"}
                        Span(
                            sep_char,
                            style={
                                "color": "var(--text-muted, #6b7280)",
                                "userSelect": "none",
                                "display": "flex",
                                "alignItems": "center",
                            },
                            **aria_props,
                        )

                    # Content: link for navigable items, span for current page
                    # Only last item gets "current page" styling (bold, primary color)
                    # All other items use link-like styling regardless of href
                    if is_last:
                        Span(
                            label,
                            style={
                                "color": "var(--text-primary, #1f2937)",
                                "fontWeight": "500",
                            },
                        )
                    elif href:
                        A(
                            label,
                            href=href,
                            style={
                                "color": "var(--text-secondary, #6b7280)",
                                "textDecoration": "none",
                            },
                        )
                    else:
                        # No href but not last - span with link-like styling
                        Span(
                            label,
                            style={
                                "color": "var(--text-secondary, #6b7280)",
                            },
                        )
