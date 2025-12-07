"""Layout container widgets."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.react_component import ReactComponent, react_component
from trellis.core.rendering import ElementDescriptor


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
    gap: int = 0,
    padding: int = 0,
    align: tp.Literal["start", "center", "end", "stretch"] = "stretch",
    key: str | None = None,
) -> ElementDescriptor:
    """Vertical flex container.

    Renders children stacked vertically with configurable gap and padding.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels.
        padding: Inner padding in pixels.
        align: Cross-axis alignment of children.
        key: Optional key for reconciliation.

    Returns:
        An ElementDescriptor for the Column component.

    Example:
        with Column(gap=16):
            Label(text="First")
            Label(text="Second")
    """
    return _column(
        gap=gap,
        padding=padding,
        align=align,
        key=key,
    )


def Row(
    *,
    gap: int = 0,
    padding: int = 0,
    align: tp.Literal["start", "center", "end", "stretch"] = "stretch",
    key: str | None = None,
) -> ElementDescriptor:
    """Horizontal flex container.

    Renders children in a row with configurable gap and padding.
    Use as a context manager to add children.

    Args:
        gap: Space between children in pixels.
        padding: Inner padding in pixels.
        align: Cross-axis alignment of children.
        key: Optional key for reconciliation.

    Returns:
        An ElementDescriptor for the Row component.

    Example:
        with Row(gap=8):
            Button(text="Left")
            Button(text="Right")
    """
    return _row(
        gap=gap,
        padding=padding,
        align=align,
        key=key,
    )
