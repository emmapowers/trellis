"""Tests for Table widget."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import serialize_node
from trellis.widgets import Label, Table, TableColumn


class TestTableWidget:
    """Tests for Table widget."""

    def test_table_with_columns_and_data(self) -> None:
        """Table stores columns and data props."""

        @component
        def App() -> None:
            """
            Top-level test App component that renders a Table configured with two columns and two data rows.
            
            Renders a Table with columns "name" and "value" and two rows:
            - {"name": "Item 1", "value": 100}
            - {"name": "Item 2", "value": 200}
            """
            Table(
                columns=["name", "value"],
                data=[
                    {"name": "Item 1", "value": 100},
                    {"name": "Item 2", "value": 200},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        # Table is a CompositionComponent that wraps _TableInner
        table_comp = ctx.elements.get(ctx.root_element.child_ids[0])
        assert table_comp.component.name == "Table"
        # The actual TableInner is a child
        table_inner = ctx.elements.get(table_comp.child_ids[0])
        assert table_inner.component.element_name == "TableInner"
        assert len(table_inner.properties["columns"]) == 2
        assert len(table_inner.properties["data"]) == 2

    def test_table_with_styling_options(self) -> None:
        """Table accepts striped, compact, bordered props."""

        @component
        def App() -> None:
            """
            Render a Table configured with specific styling options.
            
            Creates a Table with striped rows enabled, compact spacing disabled, and borders enabled.
            """
            Table(striped=True, compact=False, bordered=True)

        ctx = RenderSession(App)
        render(ctx)

        table = ctx.elements.get(ctx.root_element.child_ids[0])
        assert table.properties["striped"] is True
        assert table.properties["compact"] is False
        assert table.properties["bordered"] is True

    def test_table_with_custom_cell_render(self) -> None:
        """
        Verifies that a column-level custom render function is invoked per row and that per-cell CellSlot elements are created with correct slot IDs.
        
        Asserts the custom renderer is called once for each data row, that TableInner contains one CellSlot per rendered column cell, and that each CellSlot's `slot` property uses the format "rowKey:columnName" (using the row `_key`).
        """
        render_calls: list[dict] = []

        def CustomCell(*, row: dict) -> None:
            """
            Render a table cell that records the provided row and creates a Label displaying the row's name.
            
            Parameters:
                row (dict): The data for the current table row; must contain a 'name' key used for the Label text.
            """
            render_calls.append(row)
            Label(text=f"Custom: {row['name']}")

        @component
        def App() -> None:
            """
            Defines an App component that renders a Table with two columns ("name" and "value") and two data rows.
            
            The "value" column uses CustomCell for custom cell rendering; the two data rows include _key values "row1" and "row2".
            """
            Table(
                columns=[
                    TableColumn(name="name", label="Name"),
                    TableColumn(name="value", label="Value", render=CustomCell),
                ],
                data=[
                    {"_key": "row1", "name": "Item 1", "value": 100},
                    {"_key": "row2", "name": "Item 2", "value": 200},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        # Verify render function was called for each row
        assert len(render_calls) == 2
        assert render_calls[0]["name"] == "Item 1"
        assert render_calls[1]["name"] == "Item 2"

        # Verify CellSlot children were created
        table_comp = ctx.elements.get(ctx.root_element.child_ids[0])
        table_inner = ctx.elements.get(table_comp.child_ids[0])
        assert table_inner.component.element_name == "TableInner"

        # CellSlots are children of TableInner
        cell_slots = [
            ctx.elements.get(cid)
            for cid in table_inner.child_ids
            if ctx.elements.get(cid).component.element_name == "CellSlot"
        ]
        assert len(cell_slots) == 2  # One per row (only 'value' column has render)

        # Verify slot IDs follow "rowKey:columnName" format
        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "row1:value" in slot_ids
        assert "row2:value" in slot_ids

    def test_table_row_key_from_column(self) -> None:
        """Table uses column with row_key=True for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            """
            Render a Label showing the provided row's "name" value.
            
            Parameters:
                row (dict): Mapping representing the table row; must contain the "name" key whose value will be displayed.
            """
            Label(text=row["name"])

        @component
        def App() -> None:
            """
            Component that renders a Table with an ID row-key column and a name column using a custom cell renderer.
            
            Renders a Table with two columns and two data rows; the "id" column is marked as the row key and the "name" column uses `CustomCell` to render each cell's content.
            """
            Table(
                columns=[
                    TableColumn(name="id", label="ID", row_key=True),
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"id": "abc123", "name": "Item 1"},
                    {"id": "def456", "name": "Item 2"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        table_comp = ctx.elements.get(ctx.root_element.child_ids[0])
        table_inner = ctx.elements.get(table_comp.child_ids[0])
        cell_slots = [
            ctx.elements.get(cid)
            for cid in table_inner.child_ids
            if ctx.elements.get(cid).component.element_name == "CellSlot"
        ]

        # Slot keys should use the row_key column value
        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "abc123:name" in slot_ids
        assert "def456:name" in slot_ids

    def test_table_row_key_from_key_field(self) -> None:
        """Table falls back to _key field for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            """
            Render a Label showing the provided row's "name" value.
            
            Parameters:
                row (dict): Mapping representing the table row; must contain the "name" key whose value will be displayed.
            """
            Label(text=row["name"])

        @component
        def App() -> None:
            """
            Renders a Table with a single "name" column that uses CustomCell for cell rendering and two data rows identified by `_key` values.
            
            The table's data contains two rows with `_key` "custom1" and "custom2" and names "Item 1" and "Item 2", respectively. This component is used in tests to exercise custom cell rendering and row-key-based slot generation.
            """
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"_key": "custom1", "name": "Item 1"},
                    {"_key": "custom2", "name": "Item 2"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        table_comp = ctx.elements.get(ctx.root_element.child_ids[0])
        table_inner = ctx.elements.get(table_comp.child_ids[0])
        cell_slots = [
            ctx.elements.get(cid)
            for cid in table_inner.child_ids
            if ctx.elements.get(cid).component.element_name == "CellSlot"
        ]

        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "custom1:name" in slot_ids
        assert "custom2:name" in slot_ids

    def test_table_row_key_from_index(self) -> None:
        """Table falls back to row index for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            """
            Render a Label showing the provided row's "name" value.
            
            Parameters:
                row (dict): Mapping representing the table row; must contain the "name" key whose value will be displayed.
            """
            Label(text=row["name"])

        @component
        def App() -> None:
            """
            Defines an App component that renders a Table with a single "name" column using a custom cell renderer.
            
            The table is populated with two rows that do not provide a `_key` field or a column marked as `row_key`; row identifiers therefore use the row index. Used to test custom cell rendering and index-based row-key resolution.
            """
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"name": "Item 1"},  # No _key or row_key column
                    {"name": "Item 2"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        table_comp = ctx.elements.get(ctx.root_element.child_ids[0])
        table_inner = ctx.elements.get(table_comp.child_ids[0])
        cell_slots = [
            ctx.elements.get(cid)
            for cid in table_inner.child_ids
            if ctx.elements.get(cid).component.element_name == "CellSlot"
        ]

        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "0:name" in slot_ids
        assert "1:name" in slot_ids

    def test_table_custom_cell_serialization(self) -> None:
        """Serialized CellSlot children contain the rendered content."""

        def CustomCell(*, row: dict) -> None:
            """
            Render a Label showing the row's name prefixed with "Custom:".
            
            Parameters:
                row (dict): The table row data. Must contain a 'name' key whose value will be displayed.
            """
            Label(text=f"Custom: {row['name']}")

        @component
        def App() -> None:
            """
            Render a Table with a single "name" column that uses CustomCell and one data row with _key "row1".
            
            This component is used in tests to exercise custom cell rendering and row-key handling for a table containing one row ("Item 1").
            """
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"_key": "row1", "name": "Item 1"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        # Serialize the tree
        serialized = serialize_node(ctx.root_element, ctx)

        # Navigate to the TableInner children (CellSlots)
        table_comp = serialized["children"][0]
        table_inner = table_comp["children"][0]
        assert table_inner["type"] == "TableInner"

        # Find CellSlot children
        cell_slots = [c for c in table_inner["children"] if c["type"] == "CellSlot"]
        assert len(cell_slots) == 1

        # The CellSlot should have the Label as a child
        cell_slot = cell_slots[0]
        assert cell_slot["props"]["slot"] == "row1:name"
        assert len(cell_slot["children"]) == 1
        label_child = cell_slot["children"][0]
        assert label_child["type"] == "Label"
        assert label_child["props"]["text"] == "Custom: Item 1"