"""Tests for built-in widgets."""

from trellis.core.functional_component import component
from trellis.core.rendering import RenderContext
from trellis.core.serialization import clear_callbacks, serialize_element
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

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        # App has Column as child
        column = ctx.root_element.children[0]
        assert column.component.name == "Column"
        assert len(column.children) == 2
        assert column.children[0].component.name == "Label"
        assert column.children[1].component.name == "Label"

    def test_row_renders_children(self) -> None:
        """Row component renders its children."""

        @component
        def App() -> None:
            with Row():
                Button(text="Left")
                Button(text="Right")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        row = ctx.root_element.children[0]
        assert row.component.name == "Row"
        assert len(row.children) == 2

    def test_column_with_props(self) -> None:
        """Column accepts gap and padding props."""

        @component
        def App() -> None:
            with Column(gap=16, padding=8):
                Label(text="Test")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        column = ctx.root_element.children[0]
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

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        column = ctx.root_element.children[0]
        assert len(column.children) == 2

        row1 = column.children[0]
        row2 = column.children[1]

        assert row1.component.name == "Row"
        assert row2.component.name == "Row"
        assert len(row1.children) == 2
        assert len(row2.children) == 2


class TestBasicWidgets:
    """Tests for Label and Button widgets."""

    def setup_method(self) -> None:
        """Clear callbacks between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        clear_callbacks()

    def test_label_with_text(self) -> None:
        """Label stores text prop."""

        @component
        def App() -> None:
            Label(text="Hello World")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        label = ctx.root_element.children[0]
        assert label.component.name == "Label"
        assert label.properties["text"] == "Hello World"

    def test_label_with_styling(self) -> None:
        """Label accepts font_size and color props."""

        @component
        def App() -> None:
            Label(text="Styled", font_size=24, color="red")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        label = ctx.root_element.children[0]
        assert label.properties["font_size"] == 24
        assert label.properties["color"] == "red"

    def test_button_with_text(self) -> None:
        """Button stores text prop."""

        @component
        def App() -> None:
            Button(text="Click Me")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        button = ctx.root_element.children[0]
        assert button.component.name == "Button"
        assert button.properties["text"] == "Click Me"

    def test_button_with_callback(self) -> None:
        """Button captures on_click callback."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        button = ctx.root_element.children[0]
        assert callable(button.properties["on_click"])

        # Invoke the callback
        button.properties["on_click"]()
        assert clicked == [True]

    def test_button_disabled(self) -> None:
        """Button accepts disabled prop."""

        @component
        def App() -> None:
            Button(text="Disabled", disabled=True)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        button = ctx.root_element.children[0]
        assert button.properties["disabled"] is True


class TestWidgetSerialization:
    """Tests for serializing widgets."""

    def setup_method(self) -> None:
        """Clear callbacks between tests."""
        clear_callbacks()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        clear_callbacks()

    def test_serialize_label(self) -> None:
        """Label serializes correctly."""

        @component
        def App() -> None:
            Label(text="Test")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)

        label_data = result["children"][0]
        assert label_data["type"] == "Label"
        assert label_data["props"]["text"] == "Test"

    def test_serialize_button_with_callback(self) -> None:
        """Button callback serializes as reference."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)

        button_data = result["children"][0]
        assert button_data["type"] == "Button"
        assert "__callback__" in button_data["props"]["on_click"]

    def test_serialize_nested_layout(self) -> None:
        """Nested layout serializes with structure."""

        @component
        def App() -> None:
            with Column(gap=16):
                Label(text="Header")
                with Row():
                    Button(text="OK")
                    Button(text="Cancel")

        ctx = RenderContext(App)
        ctx.render(from_element=None)

        result = serialize_element(ctx.root_element)

        column_data = result["children"][0]
        assert column_data["type"] == "Column"
        assert column_data["props"]["gap"] == 16
        assert len(column_data["children"]) == 2

        label_data = column_data["children"][0]
        row_data = column_data["children"][1]

        assert label_data["type"] == "Label"
        assert row_data["type"] == "Row"
        assert len(row_data["children"]) == 2
