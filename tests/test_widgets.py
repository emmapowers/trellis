"""Tests for built-in widgets."""

from trellis.core.composition_component import component
from trellis.core.rendering import RenderTree
from trellis.core.serialization import serialize_node
from trellis.widgets import (
    Button,
    Card,
    Checkbox,
    Column,
    Divider,
    Heading,
    Label,
    NumberInput,
    ProgressBar,
    Row,
    Select,
    Slider,
    TextInput,
)


class TestLayoutWidgets:
    """Tests for Column and Row layout widgets."""

    def test_column_renders_children(self) -> None:
        """Column component renders its children."""

        @component
        def App() -> None:
            with Column():
                Label(text="A")
                Label(text="B")

        ctx = RenderTree(App)
        ctx.render()

        # App has Column as child
        column = ctx.root_node.children[0]
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

        ctx = RenderTree(App)
        ctx.render()

        row = ctx.root_node.children[0]
        assert row.component.name == "Row"
        assert len(row.children) == 2

    def test_column_with_props(self) -> None:
        """Column accepts gap and padding props."""

        @component
        def App() -> None:
            with Column(gap=16, padding=8):
                Label(text="Test")

        ctx = RenderTree(App)
        ctx.render()

        column = ctx.root_node.children[0]
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

        ctx = RenderTree(App)
        ctx.render()

        column = ctx.root_node.children[0]
        assert len(column.children) == 2

        row1 = column.children[0]
        row2 = column.children[1]

        assert row1.component.name == "Row"
        assert row2.component.name == "Row"
        assert len(row1.children) == 2
        assert len(row2.children) == 2


class TestBasicWidgets:
    """Tests for Label and Button widgets."""

    def test_label_with_text(self) -> None:
        """Label stores text prop."""

        @component
        def App() -> None:
            Label(text="Hello World")

        ctx = RenderTree(App)
        ctx.render()

        label = ctx.root_node.children[0]
        assert label.component.name == "Label"
        assert label.properties["text"] == "Hello World"

    def test_label_with_styling(self) -> None:
        """Label accepts font_size and color props."""

        @component
        def App() -> None:
            Label(text="Styled", font_size=24, color="red")

        ctx = RenderTree(App)
        ctx.render()

        label = ctx.root_node.children[0]
        assert label.properties["font_size"] == 24
        assert label.properties["color"] == "red"

    def test_button_with_text(self) -> None:
        """Button stores text prop."""

        @component
        def App() -> None:
            Button(text="Click Me")

        ctx = RenderTree(App)
        ctx.render()

        button = ctx.root_node.children[0]
        assert button.component.name == "Button"
        assert button.properties["text"] == "Click Me"

    def test_button_with_callback(self) -> None:
        """Button captures on_click callback."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        ctx = RenderTree(App)
        ctx.render()

        button = ctx.root_node.children[0]
        assert callable(button.properties["on_click"])

        # Invoke the callback
        button.properties["on_click"]()
        assert clicked == [True]

    def test_button_disabled(self) -> None:
        """Button accepts disabled prop."""

        @component
        def App() -> None:
            Button(text="Disabled", disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        button = ctx.root_node.children[0]
        assert button.properties["disabled"] is True

    def test_slider_with_value(self) -> None:
        """Slider stores value and range props."""

        @component
        def App() -> None:
            Slider(value=50, min=0, max=100, step=1)

        ctx = RenderTree(App)
        ctx.render()

        slider = ctx.root_node.children[0]
        assert slider.component.name == "Slider"
        assert slider.properties["value"] == 50
        assert slider.properties["min"] == 0
        assert slider.properties["max"] == 100
        assert slider.properties["step"] == 1

    def test_slider_with_callback(self) -> None:
        """Slider captures on_change callback."""
        values: list[float] = []

        @component
        def App() -> None:
            Slider(value=25, on_change=lambda v: values.append(v))

        ctx = RenderTree(App)
        ctx.render()

        slider = ctx.root_node.children[0]
        assert callable(slider.properties["on_change"])

        # Invoke the callback
        slider.properties["on_change"](75.0)
        assert values == [75.0]

    def test_slider_default_values(self) -> None:
        """Slider with no explicit props has empty properties.

        Default values (value=50, min=0, max=100, step=1) are defined in the
        function signature for documentation but applied by the React client.
        Only explicitly passed props appear in properties.
        """

        @component
        def App() -> None:
            Slider()

        ctx = RenderTree(App)
        ctx.render()

        slider = ctx.root_node.children[0]
        # No explicit props passed, so properties should be empty
        # (React client applies defaults)
        assert "value" not in slider.properties
        assert "min" not in slider.properties
        assert "max" not in slider.properties
        assert "step" not in slider.properties

    def test_slider_disabled(self) -> None:
        """Slider accepts disabled prop."""

        @component
        def App() -> None:
            Slider(disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        slider = ctx.root_node.children[0]
        assert slider.properties["disabled"] is True

    def test_slider_custom_range(self) -> None:
        """Slider can have custom min/max/step."""

        @component
        def App() -> None:
            Slider(value=5.5, min=-10, max=10, step=0.5)

        ctx = RenderTree(App)
        ctx.render()

        slider = ctx.root_node.children[0]
        assert slider.properties["value"] == 5.5
        assert slider.properties["min"] == -10
        assert slider.properties["max"] == 10
        assert slider.properties["step"] == 0.5


class TestWidgetSerialization:
    """Tests for serializing widgets."""

    def test_serialize_label(self) -> None:
        """Label serializes correctly."""

        @component
        def App() -> None:
            Label(text="Test")

        ctx = RenderTree(App)
        ctx.render()

        result = serialize_node(ctx.root_node, ctx)

        label_data = result["children"][0]
        assert label_data["type"] == "Label"
        assert label_data["props"]["text"] == "Test"

    def test_serialize_button_with_callback(self) -> None:
        """Button callback serializes as reference."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        ctx = RenderTree(App)
        ctx.render()

        result = serialize_node(ctx.root_node, ctx)

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

        ctx = RenderTree(App)
        ctx.render()

        result = serialize_node(ctx.root_node, ctx)

        column_data = result["children"][0]
        assert column_data["type"] == "Column"
        assert column_data["props"]["gap"] == 16
        assert len(column_data["children"]) == 2

        label_data = column_data["children"][0]
        row_data = column_data["children"][1]

        assert label_data["type"] == "Label"
        assert row_data["type"] == "Row"
        assert len(row_data["children"]) == 2


class TestInputWidgets:
    """Tests for TextInput, NumberInput, Checkbox, and Select widgets."""

    def test_text_input_with_value(self) -> None:
        """TextInput stores value and placeholder props."""

        @component
        def App() -> None:
            TextInput(value="hello", placeholder="Enter text...")

        ctx = RenderTree(App)
        ctx.render()

        text_input = ctx.root_node.children[0]
        assert text_input.component.name == "TextInput"
        assert text_input.properties["value"] == "hello"
        assert text_input.properties["placeholder"] == "Enter text..."

    def test_text_input_with_callback(self) -> None:
        """TextInput captures on_change callback."""
        values: list[str] = []

        @component
        def App() -> None:
            TextInput(value="test", on_change=lambda v: values.append(v))

        ctx = RenderTree(App)
        ctx.render()

        text_input = ctx.root_node.children[0]
        assert callable(text_input.properties["on_change"])

        text_input.properties["on_change"]("new value")
        assert values == ["new value"]

    def test_text_input_disabled(self) -> None:
        """TextInput accepts disabled prop."""

        @component
        def App() -> None:
            TextInput(disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        text_input = ctx.root_node.children[0]
        assert text_input.properties["disabled"] is True

    def test_number_input_with_value(self) -> None:
        """NumberInput stores value and range props."""

        @component
        def App() -> None:
            NumberInput(value=42, min=0, max=100, step=1)

        ctx = RenderTree(App)
        ctx.render()

        number_input = ctx.root_node.children[0]
        assert number_input.component.name == "NumberInput"
        assert number_input.properties["value"] == 42
        assert number_input.properties["min"] == 0
        assert number_input.properties["max"] == 100
        assert number_input.properties["step"] == 1

    def test_number_input_with_callback(self) -> None:
        """NumberInput captures on_change callback."""
        values: list[float] = []

        @component
        def App() -> None:
            NumberInput(value=10, on_change=lambda v: values.append(v))

        ctx = RenderTree(App)
        ctx.render()

        number_input = ctx.root_node.children[0]
        assert callable(number_input.properties["on_change"])

        number_input.properties["on_change"](25.5)
        assert values == [25.5]

    def test_number_input_disabled(self) -> None:
        """NumberInput accepts disabled prop."""

        @component
        def App() -> None:
            NumberInput(disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        number_input = ctx.root_node.children[0]
        assert number_input.properties["disabled"] is True

    def test_checkbox_with_checked(self) -> None:
        """Checkbox stores checked and label props."""

        @component
        def App() -> None:
            Checkbox(checked=True, label="Enable feature")

        ctx = RenderTree(App)
        ctx.render()

        checkbox = ctx.root_node.children[0]
        assert checkbox.component.name == "Checkbox"
        assert checkbox.properties["checked"] is True
        assert checkbox.properties["label"] == "Enable feature"

    def test_checkbox_with_callback(self) -> None:
        """Checkbox captures on_change callback."""
        states: list[bool] = []

        @component
        def App() -> None:
            Checkbox(checked=False, on_change=lambda v: states.append(v))

        ctx = RenderTree(App)
        ctx.render()

        checkbox = ctx.root_node.children[0]
        assert callable(checkbox.properties["on_change"])

        checkbox.properties["on_change"](True)
        assert states == [True]

    def test_checkbox_disabled(self) -> None:
        """Checkbox accepts disabled prop."""

        @component
        def App() -> None:
            Checkbox(disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        checkbox = ctx.root_node.children[0]
        assert checkbox.properties["disabled"] is True

    def test_select_with_options(self) -> None:
        """Select stores value and options props."""

        @component
        def App() -> None:
            Select(
                value="opt1",
                options=[
                    {"value": "opt1", "label": "Option 1"},
                    {"value": "opt2", "label": "Option 2"},
                ],
                placeholder="Choose...",
            )

        ctx = RenderTree(App)
        ctx.render()

        select = ctx.root_node.children[0]
        assert select.component.name == "Select"
        assert select.properties["value"] == "opt1"
        assert len(select.properties["options"]) == 2
        assert select.properties["placeholder"] == "Choose..."

    def test_select_with_callback(self) -> None:
        """Select captures on_change callback."""
        selections: list[str] = []

        @component
        def App() -> None:
            Select(
                value="opt1",
                options=[{"value": "opt1", "label": "Option 1"}],
                on_change=lambda v: selections.append(v),
            )

        ctx = RenderTree(App)
        ctx.render()

        select = ctx.root_node.children[0]
        assert callable(select.properties["on_change"])

        select.properties["on_change"]("opt2")
        assert selections == ["opt2"]

    def test_select_disabled(self) -> None:
        """Select accepts disabled prop."""

        @component
        def App() -> None:
            Select(disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        select = ctx.root_node.children[0]
        assert select.properties["disabled"] is True


class TestCardAndDivider:
    """Tests for Card and Divider widgets."""

    def test_card_renders_children(self) -> None:
        """Card component renders its children."""

        @component
        def App() -> None:
            with Card():
                Label(text="Inside card")

        ctx = RenderTree(App)
        ctx.render()

        card = ctx.root_node.children[0]
        assert card.component.name == "Card"
        assert len(card.children) == 1
        assert card.children[0].component.name == "Label"

    def test_card_with_padding(self) -> None:
        """Card accepts padding prop."""

        @component
        def App() -> None:
            with Card(padding=32):
                Label(text="Content")

        ctx = RenderTree(App)
        ctx.render()

        card = ctx.root_node.children[0]
        assert card.properties["padding"] == 32

    def test_card_nested_in_layout(self) -> None:
        """Card can be nested inside layout widgets."""

        @component
        def App() -> None:
            with Column():
                with Card():
                    Label(text="Card 1")
                with Card():
                    Label(text="Card 2")

        ctx = RenderTree(App)
        ctx.render()

        column = ctx.root_node.children[0]
        assert len(column.children) == 2
        assert column.children[0].component.name == "Card"
        assert column.children[1].component.name == "Card"

    def test_divider_renders(self) -> None:
        """Divider component renders."""

        @component
        def App() -> None:
            Divider()

        ctx = RenderTree(App)
        ctx.render()

        divider = ctx.root_node.children[0]
        assert divider.component.name == "Divider"

    def test_divider_with_props(self) -> None:
        """Divider accepts margin and color props."""

        @component
        def App() -> None:
            Divider(margin=24, color="#6366f1")

        ctx = RenderTree(App)
        ctx.render()

        divider = ctx.root_node.children[0]
        assert divider.properties["margin"] == 24
        assert divider.properties["color"] == "#6366f1"

    def test_divider_vertical_orientation(self) -> None:
        """Divider accepts orientation prop."""

        @component
        def App() -> None:
            Divider(orientation="vertical")

        ctx = RenderTree(App)
        ctx.render()

        divider = ctx.root_node.children[0]
        assert divider.properties["orientation"] == "vertical"

    def test_divider_in_layout(self) -> None:
        """Divider can separate content in a layout."""

        @component
        def App() -> None:
            with Column():
                Label(text="Above")
                Divider()
                Label(text="Below")

        ctx = RenderTree(App)
        ctx.render()

        column = ctx.root_node.children[0]
        assert len(column.children) == 3
        assert column.children[0].component.name == "Label"
        assert column.children[1].component.name == "Divider"
        assert column.children[2].component.name == "Label"


class TestHeadingWidget:
    """Tests for Heading widget."""

    def test_heading_with_text(self) -> None:
        """Heading stores text prop."""

        @component
        def App() -> None:
            Heading(text="Welcome")

        ctx = RenderTree(App)
        ctx.render()

        heading = ctx.root_node.children[0]
        assert heading.component.name == "Heading"
        assert heading.properties["text"] == "Welcome"

    def test_heading_with_level(self) -> None:
        """Heading accepts level prop for h1-h6."""

        @component
        def App() -> None:
            Heading(text="Section", level=2)

        ctx = RenderTree(App)
        ctx.render()

        heading = ctx.root_node.children[0]
        assert heading.properties["level"] == 2

    def test_heading_with_color(self) -> None:
        """Heading accepts color prop."""

        @component
        def App() -> None:
            Heading(text="Colored", color="#333")

        ctx = RenderTree(App)
        ctx.render()

        heading = ctx.root_node.children[0]
        assert heading.properties["color"] == "#333"

    def test_heading_with_style(self) -> None:
        """Heading accepts style dict."""

        @component
        def App() -> None:
            Heading(text="Styled", style={"marginBottom": "16px"})

        ctx = RenderTree(App)
        ctx.render()

        heading = ctx.root_node.children[0]
        assert heading.properties["style"] == {"marginBottom": "16px"}

    def test_heading_default_level(self) -> None:
        """Heading without explicit level has no level in properties."""

        @component
        def App() -> None:
            Heading(text="Default")

        ctx = RenderTree(App)
        ctx.render()

        heading = ctx.root_node.children[0]
        # Default values are applied by React client, not stored in properties
        assert "level" not in heading.properties


class TestProgressBarWidget:
    """Tests for ProgressBar widget."""

    def test_progress_bar_with_value(self) -> None:
        """ProgressBar stores value, min, max props."""

        @component
        def App() -> None:
            ProgressBar(value=50, min=0, max=100)

        ctx = RenderTree(App)
        ctx.render()

        progress = ctx.root_node.children[0]
        assert progress.component.name == "ProgressBar"
        assert progress.properties["value"] == 50
        assert progress.properties["min"] == 0
        assert progress.properties["max"] == 100

    def test_progress_bar_loading(self) -> None:
        """ProgressBar accepts loading prop."""

        @component
        def App() -> None:
            ProgressBar(loading=True)

        ctx = RenderTree(App)
        ctx.render()

        progress = ctx.root_node.children[0]
        assert progress.properties["loading"] is True

    def test_progress_bar_disabled(self) -> None:
        """ProgressBar accepts disabled prop."""

        @component
        def App() -> None:
            ProgressBar(disabled=True)

        ctx = RenderTree(App)
        ctx.render()

        progress = ctx.root_node.children[0]
        assert progress.properties["disabled"] is True

    def test_progress_bar_with_color(self) -> None:
        """ProgressBar accepts color prop."""

        @component
        def App() -> None:
            ProgressBar(value=75, color="#22c55e")

        ctx = RenderTree(App)
        ctx.render()

        progress = ctx.root_node.children[0]
        assert progress.properties["color"] == "#22c55e"

    def test_progress_bar_with_height(self) -> None:
        """ProgressBar accepts height prop."""

        @component
        def App() -> None:
            ProgressBar(value=25, height=12)

        ctx = RenderTree(App)
        ctx.render()

        progress = ctx.root_node.children[0]
        assert progress.properties["height"] == 12

    def test_progress_bar_with_style(self) -> None:
        """ProgressBar accepts style dict."""

        @component
        def App() -> None:
            ProgressBar(value=50, style={"marginBottom": "24px"})

        ctx = RenderTree(App)
        ctx.render()

        progress = ctx.root_node.children[0]
        assert progress.properties["style"] == {"marginBottom": "24px"}
