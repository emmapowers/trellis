"""Tests for basic widgets: Label, Button, Slider, and widget serialization."""

from trellis.core.components.composition import component
from trellis.platforms.common.serialization import serialize_element
from trellis.widgets import Button, Column, Label, Row, Slider


class TestBasicWidgets:
    """Tests for Label and Button widgets."""

    def test_label_with_text(self, rendered) -> None:
        """Label stores text prop."""

        @component
        def App() -> None:
            Label(text="Hello World")

        result = rendered(App)

        label = result.session.elements.get(result.root_element.child_ids[0])
        assert label.component.name == "Label"
        assert label.properties["text"] == "Hello World"

    def test_label_with_styling(self, rendered) -> None:
        """Label accepts font_size and color props."""

        @component
        def App() -> None:
            Label(text="Styled", font_size=24, color="red")

        result = rendered(App)

        label = result.session.elements.get(result.root_element.child_ids[0])
        assert label.properties["font_size"] == 24
        assert label.properties["color"] == "red"

    def test_button_with_text(self, rendered) -> None:
        """Button stores text prop."""

        @component
        def App() -> None:
            Button(text="Click Me")

        result = rendered(App)

        button = result.session.elements.get(result.root_element.child_ids[0])
        assert button.component.name == "Button"
        assert button.properties["text"] == "Click Me"

    def test_button_with_callback(self, rendered) -> None:
        """Button captures on_click callback."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        result = rendered(App)

        button = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(button.properties["on_click"])

        # Invoke the callback
        button.properties["on_click"]()
        assert clicked == [True]

    def test_button_disabled(self, rendered) -> None:
        """Button accepts disabled prop."""

        @component
        def App() -> None:
            Button(text="Disabled", disabled=True)

        result = rendered(App)

        button = result.session.elements.get(result.root_element.child_ids[0])
        assert button.properties["disabled"] is True

    def test_slider_with_value(self, rendered) -> None:
        """Slider stores value and range props."""

        @component
        def App() -> None:
            Slider(value=50, min=0, max=100, step=1)

        result = rendered(App)

        slider = result.session.elements.get(result.root_element.child_ids[0])
        assert slider.component.name == "Slider"
        assert slider.properties["value"] == 50
        assert slider.properties["min"] == 0
        assert slider.properties["max"] == 100
        assert slider.properties["step"] == 1

    def test_slider_with_callback(self, rendered) -> None:
        """Slider captures on_change callback."""
        values: list[float] = []

        @component
        def App() -> None:
            Slider(value=25, on_change=lambda v: values.append(v))

        result = rendered(App)

        slider = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(slider.properties["on_change"])

        # Invoke the callback
        slider.properties["on_change"](75.0)
        assert values == [75.0]

    def test_slider_default_values(self, rendered) -> None:
        """Slider with no explicit props has empty properties.

        Default values (value=50, min=0, max=100, step=1) are defined in the
        function signature for documentation but applied by the React client.
        Only explicitly passed props appear in properties.
        """

        @component
        def App() -> None:
            Slider()

        result = rendered(App)

        slider = result.session.elements.get(result.root_element.child_ids[0])
        # No explicit props passed, so properties should be empty
        # (React client applies defaults)
        assert "value" not in slider.properties
        assert "min" not in slider.properties
        assert "max" not in slider.properties
        assert "step" not in slider.properties

    def test_slider_disabled(self, rendered) -> None:
        """Slider accepts disabled prop."""

        @component
        def App() -> None:
            Slider(disabled=True)

        result = rendered(App)

        slider = result.session.elements.get(result.root_element.child_ids[0])
        assert slider.properties["disabled"] is True

    def test_slider_custom_range(self, rendered) -> None:
        """Slider can have custom min/max/step."""

        @component
        def App() -> None:
            Slider(value=5.5, min=-10, max=10, step=0.5)

        result = rendered(App)

        slider = result.session.elements.get(result.root_element.child_ids[0])
        assert slider.properties["value"] == 5.5
        assert slider.properties["min"] == -10
        assert slider.properties["max"] == 10
        assert slider.properties["step"] == 0.5


class TestWidgetSerialization:
    """Tests for serializing widgets."""

    def test_serialize_label(self, rendered) -> None:
        """Label serializes correctly."""

        @component
        def App() -> None:
            Label(text="Test")

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)

        label_data = serialized["children"][0]
        assert label_data["type"] == "Label"
        assert label_data["props"]["text"] == "Test"

    def test_serialize_button_with_callback(self, rendered) -> None:
        """Button callback serializes as reference."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)

        # Button is a composition component wrapping _Button
        button_wrapper = serialized["children"][0]
        assert button_wrapper["type"] == "CompositionComponent"
        assert button_wrapper["name"] == "Button"
        # The inner _Button has the actual props
        inner_button = button_wrapper["children"][0]
        assert inner_button["type"] == "Button"
        assert "__callback__" in inner_button["props"]["on_click"]

    def test_serialize_nested_layout(self, rendered) -> None:
        """Nested layout serializes with structure."""

        @component
        def App() -> None:
            with Column(gap=16):
                Label(text="Header")
                with Row():
                    Button(text="OK")
                    Button(text="Cancel")

        result = rendered(App)

        serialized = serialize_element(result.root_element, result.session)

        column_data = serialized["children"][0]
        assert column_data["type"] == "Column"
        assert column_data["props"]["gap"] == 16
        assert len(column_data["children"]) == 2

        label_data = column_data["children"][0]
        row_data = column_data["children"][1]

        assert label_data["type"] == "Label"
        assert row_data["type"] == "Row"
        assert len(row_data["children"]) == 2
