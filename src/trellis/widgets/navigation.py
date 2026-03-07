"""Navigation widgets for Trellis.

Provides widgets for organizing and navigating content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.composition import component
from trellis.core.components.react import react
from trellis.core.state.mutable import Mutable
from trellis.html import A, Li, Nav, Ol, Span, Style, color, px, raw, rem
from trellis.html._style_compiler import merge_style_inputs, merge_widget_style_props
from trellis.html._style_runtime import HeightInput, SpacingInput, StyleInput, WidthInput

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
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Tab container for organizing content.

    Args:
        selected: ID of the currently selected tab. Use mutable(state.prop) for two-way binding.
        variant: Visual style variant
        size: Size variant
        margin: Margin around the tabs (CSS margin value).
        width: Width of the tabs container (CSS width value).
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
    padding: SpacingInput | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Individual tab within a Tabs container.

    Args:
        id: Unique identifier for this tab
        label: Display label
        icon: Optional icon name
        disabled: Whether the tab is disabled
        padding: Padding inside the tab content (CSS padding value).
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
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    height: HeightInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Hierarchical tree view.

    Args:
        data: Tree nodes as [{id, label, children?, icon?}, ...]
        selected: ID of the selected node
        expanded: List of expanded node IDs
        on_select: Callback when a node is selected
        on_expand: Callback when a node is expanded/collapsed (id, is_expanded)
        show_icons: Whether to show folder/file icons
        margin: Margin around the tree (CSS margin value).
        width: Width of the tree (CSS width value).
        height: Height of the tree (CSS height value).
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
    margin: SpacingInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Navigation breadcrumb trail with router-integrated links.

    Each breadcrumb item with an href becomes a native html.A element that
    automatically uses client-side router navigation for relative URLs.
    The last item (or items without href) renders as plain text.

    Args:
        items: Breadcrumb items as [{label, href?}, ...]
        separator: Separator character between items ("/" renders as chevron)
        margin: Margin around the breadcrumb (CSS margin value).
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

    nav_style = merge_style_inputs(
        Style(
            display="flex",
            align_items="center",
            font_family=raw(_FONT_FAMILY),
            font_size=rem(0.875),
            line_height=raw("1.5"),
        ),
        style,
    )
    nav_props = merge_widget_style_props(
        {
            "margin": margin,
            "flex": flex,
            "style": nav_style,
        },
        frozenset({"margin", "flex"}),
    )

    # Use chevron character when separator is "/"
    # U+203A SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    sep_char = "\u203a" if separator == "/" else separator

    with Nav(
        class_name=class_name or "",
        style=tp.cast("StyleInput | None", nav_props.get("style")),
        role="navigation",
        aria_label="Breadcrumb",
    ):
        with Ol(
            style=Style(
                display="flex",
                align_items="center",
                gap=px(4),
                list_style=raw("none"),
                margin=px(0),
                padding=px(0),
            )
        ):
            for i, item in enumerate(items_list):
                is_last = i == len(items_list) - 1
                label = item.get("label", "")
                href = item.get("href")

                with Li(style=Style(display="flex", align_items="center", gap=px(4))):
                    # Separator before non-first items
                    if i > 0:
                        Span(
                            sep_char,
                            style=Style(
                                color=color("var(--text-muted, #6b7280)"),
                                user_select=raw("none"),
                                display="flex",
                                align_items="center",
                            ),
                            aria_hidden=True,
                        )

                    # Content: link for navigable items, span for current page
                    # Only last item gets "current page" styling (bold, primary color)
                    # All other items use link-like styling regardless of href
                    if is_last:
                        Span(
                            label,
                            style=Style(
                                color=color("var(--text-primary, #1f2937)"),
                                font_weight=500,
                            ),
                        )
                    elif href:
                        A(
                            label,
                            href=href,
                            style=Style(
                                color=color("var(--text-secondary, #6b7280)"),
                                text_decoration=raw("none"),
                            ),
                        )
                    else:
                        # No href but not last - span with link-like styling
                        Span(
                            label,
                            style=Style(color=color("var(--text-secondary, #6b7280)")),
                        )
