"""Table widget with custom cell rendering support.

Provides a data table component that supports custom cell rendering via
column render functions, while remaining compatible with future react-aria
integration for sorting, filtering, and selection.

Usage:
    from trellis.widgets import Table, TableColumn

    # Simple usage with string columns
    Table(
        columns=["name", "status", "value"],
        data=[
            {"name": "Item 1", "status": "Active", "value": 100},
            {"name": "Item 2", "status": "Pending", "value": 50},
        ],
    )

    # Full control with TableColumn
    def PriceCell(*, row: dict) -> None:
        Label(text=f"${row['price']:.2f}")

    Table(
        columns=[
            TableColumn(name="ticker", label="Ticker", row_key=True),
            TableColumn(name="name", label="Company"),
            TableColumn(name="price", label="Price", align="right", render=PriceCell),
        ],
        data=[
            {"ticker": "AAPL", "name": "Apple Inc.", "price": 150.0, "change": 2.5},
        ],
    )
"""

from __future__ import annotations

import typing as tp
from collections.abc import Callable
from dataclasses import dataclass

from trellis.core.components.composition import component
from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Height, Margin, Width
from trellis.core.rendering.element import Element
from trellis.widgets.icons import IconName

__all__ = ["Table", "TableColumn"]


@dataclass
class TableColumn:
    """Configuration for a Table column.

    Attributes:
        name: Key to look up in row data. Also used as React key for the column.
        label: Display label for the column header. Defaults to name.title().
        icon: Optional icon to show before the label in the header.
        width: Optional CSS width (e.g., "100px", "20%").
        align: Text alignment for the column. Defaults to "left".
        render: Optional function that receives the row dict and renders custom
            cell content. If not provided, displays row[name] as text.
        row_key: If True, use this column's value as the row key for reconciliation.
    """

    name: str
    label: str | None = None
    icon: IconName | None = None
    width: str | None = None
    align: tp.Literal["left", "center", "right"] = "left"
    render: Callable[..., None] | None = None  # Signature: (*, row: dict[str, Any]) -> None
    row_key: bool = False


def _normalize_column(col: str | TableColumn) -> TableColumn:
    """Convert string column to TableColumn."""
    if isinstance(col, str):
        return TableColumn(name=col)
    return col


def _escape_slot_key_part(s: str) -> str:
    """Escape colons in a string for use in slot keys.

    This prevents collision when row keys contain colons.
    Must match the escaping in Table.tsx.
    """
    return s.replace("\\", "\\\\").replace(":", "\\:")


def _get_row_key(
    row: dict[str, tp.Any],
    row_index: int,
    key_column: TableColumn | None,
) -> str:
    """Get the key for a row."""
    # Priority: column with row_key=True > _key field > index
    if key_column is not None:
        return str(row.get(key_column.name, row_index))
    if "_key" in row:
        return str(row["_key"])
    return str(row_index)


@react_component_base("CellSlot", has_children=True)
def CellSlot(
    *,
    slot: str,
) -> Element:
    """Marker component for custom cell content.

    Used internally by Table to position custom cell content.
    The slot prop identifies the cell position as "rowKey:columnName".
    """
    ...


@react_component_base("TableInner", has_children=True)
def _TableInner(
    *,
    columns: list[dict[str, tp.Any]],
    data: list[dict[str, tp.Any]],
    striped: bool = False,
    compact: bool = True,
    bordered: bool = False,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> Element:
    """Internal React table component.

    Renders the actual table structure and positions custom cell content
    from CellSlot children.
    """
    ...


@component
def Table(
    *,
    columns: list[str] | list[TableColumn] | None = None,
    data: list[dict[str, tp.Any]] | None = None,
    striped: bool = False,
    compact: bool = True,
    bordered: bool = False,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    height: Height | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Data table widget with custom cell rendering support.

    Displays tabular data with configurable columns. Supports custom cell
    rendering via column render functions, striped rows, compact mode,
    and bordered styling.

    Args:
        columns: Column definitions. Can be a simple list of strings (used as
            both key and label), or a list of TableColumn configs for full
            control over rendering.
        data: List of row dicts. Keys should match column names. Row identity
            for updates is determined by:
            1. The column with row_key=True
            2. A "_key" field in the row dict
            3. Row index (not recommended for dynamic data)
        striped: Show alternating row colors. Defaults to False.
        compact: Use compact row height and font size. Defaults to True.
        bordered: Show cell borders and rounded corners. Defaults to False.
        margin: Margin around the table.
        width: Table width (Width dataclass, int for pixels, or str for CSS).
        height: Table height (enables vertical scrolling if content overflows).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Example:
        # Simple usage - strings as column names
        Table(
            columns=["name", "status", "value"],
            data=[
                {"name": "Item 1", "status": "Active", "value": 100},
                {"name": "Item 2", "status": "Pending", "value": 50},
            ],
        )

        # Custom cell rendering
        def status_cell(*, row: dict) -> None:
            color = "green" if row["status"] == "Active" else "orange"
            with Row(gap=4):
                Icon(name=IconName.CIRCLE, size=8, color=color)
                Label(text=row["status"])

        Table(
            columns=[
                TableColumn(name="name", label="Name"),
                TableColumn(name="status", label="Status", render=status_cell),
            ],
            data=[...],
        )
    """
    # Default to empty lists if None
    if columns is None:
        columns = []
    if data is None:
        data = []

    # Normalize columns to TableColumn instances
    cols = [_normalize_column(c) for c in columns]

    # Find key column (if any)
    key_column = next((c for c in cols if c.row_key), None)

    # Build column specs for React (without render functions)
    col_specs = [
        {
            "name": c.name,
            "label": c.label if c.label is not None else c.name.title(),
            "icon": c.icon.value if c.icon is not None else None,
            "width": c.width,
            "align": c.align,
        }
        for c in cols
    ]

    # Build combined style
    combined_style: dict[str, tp.Any] = {}
    if margin is not None:
        combined_style.update(margin.to_style())
    if width is not None:
        if isinstance(width, Width):
            combined_style.update(width.to_style())
        elif isinstance(width, int):
            combined_style["width"] = f"{width}px"
        else:
            combined_style["width"] = width
    if height is not None:
        if isinstance(height, Height):
            combined_style.update(height.to_style())
        elif isinstance(height, int):
            combined_style["height"] = f"{height}px"
        else:
            combined_style["height"] = height
    if flex is not None:
        combined_style["flex"] = flex
    if style:
        combined_style.update(style)

    # Render the inner table with cell slot children
    with _TableInner(
        columns=col_specs,
        data=data,
        striped=striped,
        compact=compact,
        bordered=bordered,
        class_name=class_name,
        style=combined_style if combined_style else None,
    ):
        # Generate cell slots for columns with custom renderers
        for row_index, row in enumerate(data):
            row_key = _get_row_key(row, row_index, key_column)
            for col in cols:
                if col.render is not None:
                    # Escape colons in row key to prevent collision
                    slot_id = f"{_escape_slot_key_part(row_key)}:{col.name}"
                    with CellSlot(slot=slot_id).key(slot_id):
                        col.render(row=row)
