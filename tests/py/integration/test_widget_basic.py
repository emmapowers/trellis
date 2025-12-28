"""Tests for basic widgets: Label, Button, Slider, and widget serialization."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import serialize_node
from trellis.widgets import Button, Column, Label, Row, Slider


class TestBasicWidgets:
    """Tests for Label and Button widgets."""

    def test_label_with_text(self) -> None:
        """
        Verify that a Label component preserves its text property after rendering.
        """

        @component
        def App() -> None:
            """
            Renders a component tree containing a single Label with text "Hello World".
            """
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
            """
            Creates an application component containing a single Label with text "Styled" and styling applied.
            
            The Label is configured with font_size 24 and color "red".
            """
            Label(text="Styled", font_size=24, color="red")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.properties["font_size"] == 24
        assert label.properties["color"] == "red"

    def test_button_with_text(self) -> None:
        """
        Verify that a Button component preserves its text property when rendered.
        
        Creates an App containing a Button with text "Click Me", renders it, and asserts the rendered element is a Button whose `text` property equals "Click Me".
        """

        @component
        def App() -> None:
            """
            Top-level app component that renders a single Button with the text "Click Me".
            
            Used in tests to create a simple UI containing a Button component.
            """
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
            """
            Create an app component that renders a Button which appends True to the surrounding `clicked` list when invoked.
            
            Used in tests to verify that a Button's `on_click` callback is stored and callable.
            """
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
            """
            Component that renders a single Button set to disabled.
            
            Creates a Button with text "Disabled" and disabled=True.
            """
            Button(text="Disabled", disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])
        assert button.properties["disabled"] is True

    def test_slider_with_value(self) -> None:
        """Slider stores value and range props."""

        @component
        def App() -> None:
            """
            Create an app component that renders a Slider initialized to 50 with a range of 0 to 100 and step 1.
            """
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
            """
            Create a Slider component initialized to 25 with an on_change callback that appends the new value to the surrounding `values` list.
            
            The function builds and returns no value; it produces a Slider node with `value=25` and an `on_change` handler that records changes by appending the passed value to the external `values` list.
            """
            Slider(value=25, on_change=lambda v: values.append(v))

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(slider.properties["on_change"])

        # Invoke the callback
        slider.properties["on_change"](75.0)
        assert values == [75.0]

    def test_slider_default_values(self) -> None:
        """
        Verify that a Slider created without explicit props yields no properties on the server-rendered element.
        
        Only props explicitly passed by the app appear in the element's properties; client-side defaults (value=50, min=0, max=100, step=1) are applied by the frontend and are not present on the server-rendered node.
        """

        @component
        def App() -> None:
            """
            Component that renders a Slider with default properties.
            
            Used as a minimal app component to produce a Slider element for rendering and testing.
            """
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
            """
            Create a minimal app that contains a single Slider component disabled for interaction.
            
            This component builds a UI tree with one Slider whose `disabled` property is set to True.
            """
            Slider(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["disabled"] is True

    def test_slider_custom_range(self) -> None:
        """Slider can have custom min/max/step."""

        @component
        def App() -> None:
            """
            Create an app component that renders a Slider configured with value 5.5, min -10, max 10, and step 0.5.
            
            This component is used by tests to verify a slider with a custom numeric range and fractional step behaves as expected.
            """
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
            """
            Creates an app component that renders a single Label with the text "Test".
            """
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
            """
            Create a minimal app component that declares a Button labeled "Click" with a no-op click handler.
            
            Used in tests as the component root for rendering and serialization checks.
            """
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
            """
            Create a simple component tree: a Column with a header label and a Row containing "OK" and "Cancel" buttons.
            
            This component is used in tests to render and serialize a nested layout consisting of:
            - a Column with gap set to 16
            - a Label with text "Header"
            - a Row containing two Buttons with texts "OK" and "Cancel"
            """
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