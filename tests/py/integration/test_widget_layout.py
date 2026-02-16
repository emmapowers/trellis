"""Tests for layout widgets: Column, Row, SplitPane."""

import pytest

from trellis.core.components.composition import component
from trellis.widgets import Button, Column, Label, Row, SplitPane


class TestLayoutWidgets:
    """Tests for Column and Row layout widgets."""

    def test_column_renders_children(self, rendered) -> None:
        """Column component renders its children."""

        @component
        def App() -> None:
            with Column():
                Label(text="A")
                Label(text="B")

        result = rendered(App)

        # App has Column as child
        column = result.session.elements.get(result.root_element.child_ids[0])
        assert column.component.name == "Column"
        assert len(column.child_ids) == 2
        assert result.session.elements.get(column.child_ids[0]).component.name == "Label"
        assert result.session.elements.get(column.child_ids[1]).component.name == "Label"

    def test_row_renders_children(self, rendered) -> None:
        """Row component renders its children."""

        @component
        def App() -> None:
            with Row():
                Button(text="Left")
                Button(text="Right")

        result = rendered(App)

        row = result.session.elements.get(result.root_element.child_ids[0])
        assert row.component.name == "Row"
        assert len(row.child_ids) == 2

    def test_column_with_props(self, rendered) -> None:
        """Column accepts gap and padding props."""

        @component
        def App() -> None:
            with Column(gap=16, padding=8):
                Label(text="Test")

        result = rendered(App)

        column = result.session.elements.get(result.root_element.child_ids[0])
        assert column.properties["gap"] == 16
        assert column.properties["padding"] == 8

    def test_nested_layout(self, rendered) -> None:
        """Layouts can be nested."""

        @component
        def App() -> None:
            with Column():
                with Row():
                    Label(text="A")
                    Label(text="B")
                with Row():
                    Label(text="C")
                    Label(text="D")

        result = rendered(App)

        column = result.session.elements.get(result.root_element.child_ids[0])
        assert len(column.child_ids) == 2

        row1 = result.session.elements.get(column.child_ids[0])
        row2 = result.session.elements.get(column.child_ids[1])

        assert row1.component.name == "Row"
        assert row2.component.name == "Row"
        assert len(row1.child_ids) == 2
        assert len(row2.child_ids) == 2

    def test_split_pane_renders_two_children(self, rendered) -> None:
        """SplitPane renders exactly two panes."""

        @component
        def App() -> None:
            with SplitPane(split=0.4, min_size=80):
                Label(text="Left")
                Label(text="Right")

        result = rendered(App)

        split_pane = result.session.elements.get(result.root_element.child_ids[0])
        assert split_pane.component.name == "SplitPane"
        assert split_pane.properties["split"] == 0.4
        assert split_pane.properties["min_size"] == 80

        rendered_split_pane = result.session.elements.get(split_pane.child_ids[0])
        assert rendered_split_pane.component.element_name == "SplitPane"
        assert len(rendered_split_pane.child_ids) == 2

    def test_split_pane_requires_exactly_two_children(self, rendered) -> None:
        """SplitPane raises when child count is not exactly two."""

        @component
        def App() -> None:
            with SplitPane():
                Label(text="Only one")

        with pytest.raises(ValueError, match="exactly two"):
            rendered(App)
