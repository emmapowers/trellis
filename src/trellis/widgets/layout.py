"""Layout container widgets."""

from __future__ import annotations

import typing as tp

from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Height, Margin, Padding, Width
from trellis.core.rendering.element import ElementNode


@react_component_base("Column", has_children=True)
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
    key: str | None = None,
) -> ElementNode:
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

    Returns:
        An ElementNode for the Column component.

    Example:
        with Column(gap=16):
            Label(text="First")
            Label(text="Second")

        with Column(divider=True):  # Dividers between items
            Label(text="Item 1")
            Label(text="Item 2")
    """
    ...


@react_component_base("Row", has_children=True)
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
    key: str | None = None,
) -> ElementNode:
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

    Returns:
        An ElementNode for the Row component.

    Example:
        with Row(gap=8):
            Button(text="Left")
            Button(text="Right")
    """
    ...


@react_component_base("Card", has_children=True)
def Card(
    *,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
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

    Returns:
        An ElementNode for the Card component.

    Example:
        with Card(padding=16):
            Label(text="Card content")
            Button(text="Action")
    """
    ...
