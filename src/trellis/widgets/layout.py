"""Layout container widgets."""

from __future__ import annotations

import typing as tp

from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode


@react_component_base("Column", has_children=True)
def Column(
    *,
    gap: int | None = None,
    padding: int | None = None,
    align: tp.Literal["start", "center", "end", "stretch"] | None = None,
    justify: tp.Literal["start", "center", "end", "between", "around"] | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Vertical flex container.

    Renders children stacked vertically with configurable gap and padding.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels. Defaults to 12.
        padding: Inner padding in pixels. Defaults to 0.
        align: Cross-axis alignment of children. Defaults to "stretch".
        justify: Main-axis alignment of children. Defaults to "start".
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Column component.

    Example:
        with Column(gap=16):
            Label(text="First")
            Label(text="Second")
    """
    ...


@react_component_base("Row", has_children=True)
def Row(
    *,
    gap: int | None = None,
    padding: int | None = None,
    align: tp.Literal["start", "center", "end", "stretch"] | None = None,
    justify: tp.Literal["start", "center", "end", "between", "around"] | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Horizontal flex container.

    Renders children in a row with configurable gap and padding.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels. Defaults to 12.
        padding: Inner padding in pixels. Defaults to 0.
        align: Cross-axis alignment of children. Defaults to "center".
        justify: Main-axis alignment of children. Defaults to "start".
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
    padding: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Visual container with card styling.

    Renders children inside a styled container with background, border,
    and shadow. Use as a context manager to add children.

    Args:
        padding: Inner padding in pixels. Defaults to 24.
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
