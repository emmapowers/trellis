"""Tests for Table widget."""

from trellis.core.components.composition import component
from trellis.platforms.common.serialization import serialize_element
from trellis.widgets import Label, Table, TableColumn


class TestTableWidget:
    """Tests for Table widget."""

    def test_table_with_columns_and_data(self, rendered) -> None:
        """Table stores columns and data props."""

        @component
        def App() -> None:
            Table(
                columns=["name", "value"],
                data=[
                    {"name": "Item 1", "value": 100},
                    {"name": "Item 2", "value": 200},
                ],
            )

        result = rendered(App)

        # Table is a CompositionComponent that wraps _TableInner
        table_comp = result.session.elements.get(result.root_element.child_ids[0])
        assert table_comp.component.name == "Table"
        # The actual TableInner is a child
        table_inner = result.session.elements.get(table_comp.child_ids[0])
        assert table_inner.component.element_name == "TableInner"
        assert len(table_inner.properties["columns"]) == 2
        assert len(table_inner.properties["data"]) == 2

    def test_table_with_styling_options(self, rendered) -> None:
        """Table accepts striped, compact, bordered props."""

        @component
        def App() -> None:
            Table(striped=True, compact=False, bordered=True)

        result = rendered(App)

        table = result.session.elements.get(result.root_element.child_ids[0])
        assert table.properties["striped"] is True
        assert table.properties["compact"] is False
        assert table.properties["bordered"] is True

    def test_table_with_custom_cell_render(self, rendered) -> None:
        """Table with custom cell rendering creates CellSlot children."""
        render_calls: list[dict] = []

        def CustomCell(*, row: dict) -> None:
            render_calls.append(row)
            Label(text=f"Custom: {row['name']}")

        @component
        def App() -> None:
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

        result = rendered(App)

        # Verify render function was called for each row
        assert len(render_calls) == 2
        assert render_calls[0]["name"] == "Item 1"
        assert render_calls[1]["name"] == "Item 2"

        # Verify CellSlot children were created
        table_comp = result.session.elements.get(result.root_element.child_ids[0])
        table_inner = result.session.elements.get(table_comp.child_ids[0])
        assert table_inner.component.element_name == "TableInner"

        # CellSlots are children of TableInner
        cell_slots = [
            result.session.elements.get(cid)
            for cid in table_inner.child_ids
            if result.session.elements.get(cid).component.element_name == "CellSlot"
        ]
        assert len(cell_slots) == 2  # One per row (only 'value' column has render)

        # Verify slot IDs follow "rowKey:columnName" format
        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "row1:value" in slot_ids
        assert "row2:value" in slot_ids

    def test_table_row_key_from_column(self, rendered) -> None:
        """Table uses column with row_key=True for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            Label(text=row["name"])

        @component
        def App() -> None:
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

        result = rendered(App)

        table_comp = result.session.elements.get(result.root_element.child_ids[0])
        table_inner = result.session.elements.get(table_comp.child_ids[0])
        cell_slots = [
            result.session.elements.get(cid)
            for cid in table_inner.child_ids
            if result.session.elements.get(cid).component.element_name == "CellSlot"
        ]

        # Slot keys should use the row_key column value
        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "abc123:name" in slot_ids
        assert "def456:name" in slot_ids

    def test_table_row_key_from_key_field(self, rendered) -> None:
        """Table falls back to _key field for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            Label(text=row["name"])

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"_key": "custom1", "name": "Item 1"},
                    {"_key": "custom2", "name": "Item 2"},
                ],
            )

        result = rendered(App)

        table_comp = result.session.elements.get(result.root_element.child_ids[0])
        table_inner = result.session.elements.get(table_comp.child_ids[0])
        cell_slots = [
            result.session.elements.get(cid)
            for cid in table_inner.child_ids
            if result.session.elements.get(cid).component.element_name == "CellSlot"
        ]

        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "custom1:name" in slot_ids
        assert "custom2:name" in slot_ids

    def test_table_row_key_from_index(self, rendered) -> None:
        """Table falls back to row index for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            Label(text=row["name"])

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"name": "Item 1"},  # No _key or row_key column
                    {"name": "Item 2"},
                ],
            )

        result = rendered(App)

        table_comp = result.session.elements.get(result.root_element.child_ids[0])
        table_inner = result.session.elements.get(table_comp.child_ids[0])
        cell_slots = [
            result.session.elements.get(cid)
            for cid in table_inner.child_ids
            if result.session.elements.get(cid).component.element_name == "CellSlot"
        ]

        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "0:name" in slot_ids
        assert "1:name" in slot_ids

    def test_table_custom_cell_serialization(self, rendered) -> None:
        """Serialized CellSlot children contain the rendered content."""

        def CustomCell(*, row: dict) -> None:
            Label(text=f"Custom: {row['name']}")

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"_key": "row1", "name": "Item 1"},
                ],
            )

        result = rendered(App)

        # Serialize the tree
        serialized = serialize_element(result.root_element, result.session)

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
