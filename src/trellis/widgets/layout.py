"""Layout container widgets."""

from __future__ import annotations

import typing as tp

from trellis.core.components.composition import component
from trellis.core.components.react import react
from trellis.core.components.style_props import Height, Margin, Padding, Width

if tp.TYPE_CHECKING:
    from trellis.core.rendering.child_ref import ChildRef


@react("client/Column.tsx", is_container=True)
def Column(
    *,
    gap: int | None = None,
    align: tp.Literal["start", "center", "end", "stretch"] | None = None,
    justify: tp.Literal["start", "center", "end", "between", "around"] | None = None,
    divider: bool = False,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Vertical flex container.

    Renders children stacked vertically with configurable gap.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels. Defaults to 12.
        align: Cross-axis alignment of children. Defaults to "stretch".
        justify: Main-axis alignment of children. Defaults to "start".
        divider: Whether to show dividers between children. Defaults to False.
        padding: Padding inside the container (Padding dataclass or int for all sides).
        margin: Margin around the container (Margin dataclass).
        width: Width of the container (Width dataclass, int for pixels, or str for CSS).
        height: Height of the container (Height dataclass, int for pixels, or str for CSS).
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


@react("client/Row.tsx", is_container=True)
def Row(
    *,
    gap: int | None = None,
    align: tp.Literal["start", "center", "end", "stretch"] | None = None,
    justify: tp.Literal["start", "center", "end", "between", "around"] | None = None,
    divider: bool = False,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Horizontal flex container.

    Renders children in a row with configurable gap.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels. Defaults to 12.
        align: Cross-axis alignment of children. Defaults to "center".
        justify: Main-axis alignment of children. Defaults to "start".
        divider: Whether to show dividers between children. Defaults to False.
        padding: Padding inside the container (Padding dataclass or int for all sides).
        margin: Margin around the container (Margin dataclass).
        width: Width of the container (Width dataclass, int for pixels, or str for CSS).
        height: Height of the container (Height dataclass, int for pixels, or str for CSS).
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


@react("client/Card.tsx", is_container=True)
def Card(
    *,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Visual container with card styling.

    Renders children inside a styled container with background, border,
    and shadow. Use as a context manager to add children.

    Args:
        padding: Padding inside the card (Padding dataclass or int for all sides).
        margin: Margin around the card (Margin dataclass).
        width: Width of the card (Width dataclass, int for pixels, or str for CSS).
        height: Height of the card (Height dataclass, int for pixels, or str for CSS).
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


@component
def SplitPane(
    *,
    orientation: tp.Literal["horizontal", "vertical"] = "horizontal",
    split: float = 0.5,
    min_size: int = 120,
    divider_size: int = 8,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
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
    if len(pane_children) != 2:
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


@react("client/SplitPane.tsx", export_name="SplitPane", is_container=True)
def _SplitPane(
    *,
    orientation: tp.Literal["horizontal", "vertical"] = "horizontal",
    split: float = 0.5,
    min_size: int = 120,
    divider_size: int = 8,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    pass
