"""Tests for basic widgets: Label, Button, Slider, and widget serialization."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import serialize_node
from trellis.widgets import Button, Column, Label, Row, Slider


class TestBasicWidgets:
    """Tests for Label and Button widgets."""

    def test_label_with_text(self) -> None:
        """Label stores text prop."""

        @component
        def App() -> None:
            Label(text="Hello World")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.component.name == "Label"
        assert label.properties["text"] == "Hello World"

    def test_label_with_styling(self) -> None:
        """Label accepts font_size and color props."""

        @component
        def App() -> None:
            Label(text="Styled", font_size=24, color="red")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.properties["font_size"] == 24
        assert label.properties["color"] == "red"

    def test_button_with_text(self) -> None:
        """Button stores text prop."""

        @component
        def App() -> None:
            Button(text="Click Me")

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])
        assert button.component.name == "Button"
        assert button.properties["text"] == "Click Me"

    def test_button_with_callback(self) -> None:
        """Button captures on_click callback."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(button.properties["on_click"])

        # Invoke the callback
        button.properties["on_click"]()
        assert clicked == [True]

    def test_button_disabled(self) -> None:
        """Button accepts disabled prop."""

        @component
        def App() -> None:
            Button(text="Disabled", disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])
        assert button.properties["disabled"] is True

    def test_slider_with_value(self) -> None:
        """Slider stores value and range props."""

        @component
        def App() -> None:
            Slider(value=50, min=0, max=100, step=1)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
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

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
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

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
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

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["disabled"] is True

    def test_slider_custom_range(self) -> None:
        """Slider can have custom min/max/step."""

        @component
        def App() -> None:
            Slider(value=5.5, min=-10, max=10, step=0.5)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
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

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

        label_data = result["children"][0]
        assert label_data["type"] == "Label"
        assert label_data["props"]["text"] == "Test"

    def test_serialize_button_with_callback(self) -> None:
        """Button callback serializes as reference."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

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

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_element, ctx)

        column_data = result["children"][0]
        assert column_data["type"] == "Column"
        assert column_data["props"]["gap"] == 16
        assert len(column_data["children"]) == 2

        label_data = column_data["children"][0]
        row_data = column_data["children"][1]

        assert label_data["type"] == "Label"
        assert row_data["type"] == "Row"
        assert len(row_data["children"]) == 2
