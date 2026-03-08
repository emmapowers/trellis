"""Layout container widgets."""

from __future__ import annotations

import typing as tp

from trellis.core.components.composition import component
from trellis.core.components.react import react
from trellis.core.state.mutable import Mutable
from trellis.html._style_runtime import HeightInput, SpacingInput, StyleInput, WidthInput
from trellis.widgets._style_props import widget_style_props

if tp.TYPE_CHECKING:
    from trellis.core.rendering.child_ref import ChildRef

_SPLIT_PANE_REQUIRED_CHILDREN = 2


@widget_style_props("padding", "margin", "width", "height", "flex")
@react("client/Column.tsx", is_container=True)
def Column(
    *,
    gap: int | None = None,
    align: tp.Literal["start", "center", "end", "stretch"] | None = None,
    justify: tp.Literal["start", "center", "end", "between", "around"] | None = None,
    divider: bool = False,
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    height: HeightInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Vertical flex container.

    Renders children stacked vertically with configurable gap.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels. Defaults to 12.
        align: Cross-axis alignment of children. Defaults to "stretch".
        justify: Main-axis alignment of children. Defaults to "start".
        divider: Whether to show dividers between children. Defaults to False.
        padding: Padding inside the container (CSS padding value).
        margin: Margin around the container (CSS margin value).
        width: Width of the container (CSS width value).
        height: Height of the container (CSS height value).
        flex: Flex grow/shrink value for the container.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Example:
        with Column(gap=16):
            Label(text="First")
            Label(text="Second")

        with Column(divider=True):  # Dividers between items
            Label(text="Item 1")
            Label(text="Item 2")
    """
    pass


@widget_style_props("padding", "margin", "width", "height", "flex")
@react("client/Row.tsx", is_container=True)
def Row(
    *,
    gap: int | None = None,
    align: tp.Literal["start", "center", "end", "stretch"] | None = None,
    justify: tp.Literal["start", "center", "end", "between", "around"] | None = None,
    divider: bool = False,
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    height: HeightInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Horizontal flex container.

    Renders children in a row with configurable gap.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels. Defaults to 12.
        align: Cross-axis alignment of children. Defaults to "center".
        justify: Main-axis alignment of children. Defaults to "start".
        divider: Whether to show dividers between children. Defaults to False.
        padding: Padding inside the container (CSS padding value).
        margin: Margin around the container (CSS margin value).
        width: Width of the container (CSS width value).
        height: Height of the container (CSS height value).
        flex: Flex grow/shrink value for the container.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Example:
        with Row(gap=8):
            Button(text="Left")
            Button(text="Right")
    """
    pass


@widget_style_props("padding", "margin", "width", "height", "flex")
@react("client/Card.tsx", is_container=True)
def Card(
    *,
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    height: HeightInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Visual container with card styling.

    Renders children inside a styled container with background, border,
    and shadow. Use as a context manager to add children.

    Args:
        padding: Padding inside the card (CSS padding value).
        margin: Margin around the card (CSS margin value).
        width: Width of the card (CSS width value).
        height: Height of the card (CSS height value).
        flex: Flex grow/shrink value for the card.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Example:
        with Card(padding=16):
            Label(text="Card content")
            Button(text="Action")
    """
    pass


@component(is_container=True)
def SplitPane(
    *,
    orientation: tp.Literal["horizontal", "vertical"] = "horizontal",
    split: float | Mutable[float] = 0.5,
    min_size: int = 120,
    divider_size: int = 8,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    height: HeightInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
    children: list[ChildRef] | None = None,
) -> None:
    """Resizable two-pane layout container.

    SplitPane requires exactly two child panes.

    Args:
        orientation: Split direction ("horizontal" for left/right, "vertical" for top/bottom).
        split: Initial split ratio from 0.0 to 1.0.
        min_size: Minimum size in pixels for each pane.
        divider_size: Draggable divider thickness in pixels.
        margin: Margin around the split pane.
        width: Width of the split pane.
        height: Height of the split pane.
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        children: Exactly two child panes.
    """
    pane_children = children or []
    if len(pane_children) != _SPLIT_PANE_REQUIRED_CHILDREN:
        raise ValueError("SplitPane requires exactly two children")

    _SplitPane(
        orientation=orientation,
        split=split,
        min_size=min_size,
        divider_size=divider_size,
        margin=margin,
        width=width,
        height=height,
        flex=flex,
        class_name=class_name,
        style=style,
        children=pane_children,
    )


@widget_style_props("margin", "width", "height", "flex")
@react("client/SplitPane.tsx", export_name="SplitPane", is_container=True)
def _SplitPane(
    *,
    orientation: tp.Literal["horizontal", "vertical"] = "horizontal",
    split: float | Mutable[float] = 0.5,
    min_size: int = 120,
    divider_size: int = 8,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    height: HeightInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
    children: list[ChildRef] | None = None,
) -> None:
    pass
