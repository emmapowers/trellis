"""Tests for layout widgets: Column, Row."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import Button, Column, Label, Row


class TestLayoutWidgets:
    """Tests for Column and Row layout widgets."""

    def test_column_renders_children(self) -> None:
        """Column component renders its children."""

        @component
        def App() -> None:
            with Column():
                Label(text="A")
                Label(text="B")

        ctx = RenderSession(App)
        render(ctx)

        # App has Column as child
        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert column.component.name == "Column"
        assert len(column.child_ids) == 2
        assert ctx.elements.get(column.child_ids[0]).component.name == "Label"
        assert ctx.elements.get(column.child_ids[1]).component.name == "Label"

    def test_row_renders_children(self) -> None:
        """Row component renders its children."""

        @component
        def App() -> None:
            with Row():
                Button(text="Left")
                Button(text="Right")

        ctx = RenderSession(App)
        render(ctx)

        row = ctx.elements.get(ctx.root_element.child_ids[0])
        assert row.component.name == "Row"
        assert len(row.child_ids) == 2

    def test_column_with_props(self) -> None:
        """Column accepts gap and padding props."""

        @component
        def App() -> None:
            with Column(gap=16, padding=8):
                Label(text="Test")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert column.properties["gap"] == 16
        assert column.properties["padding"] == 8

    def test_nested_layout(self) -> None:
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

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert len(column.child_ids) == 2

        row1 = ctx.elements.get(column.child_ids[0])
        row2 = ctx.elements.get(column.child_ids[1])

        assert row1.component.name == "Row"
        assert row2.component.name == "Row"
        assert len(row1.child_ids) == 2
        assert len(row2.child_ids) == 2
