"""Layout container widgets."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.react_component import ReactComponent, react_component
from trellis.core.rendering import ElementNode


@react_component("Column", has_children=True)
@dataclass(kw_only=True)
class _ColumnComponent(ReactComponent):
    """Vertical flex container."""

    name: str = "Column"


@react_component("Row", has_children=True)
@dataclass(kw_only=True)
class _RowComponent(ReactComponent):
    """Horizontal flex container."""

    name: str = "Row"


# Singleton instances used by factory functions
_column = _ColumnComponent()
_row = _RowComponent()


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
    return _column(
        gap=gap,
        padding=padding,
        align=align,
        justify=justify,
        className=class_name,
        style=style,
        key=key,
    )


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
    return _row(
        gap=gap,
        padding=padding,
        align=align,
        justify=justify,
        className=class_name,
        style=style,
        key=key,
    )
