"""Tests for input widgets: TextInput, NumberInput, Checkbox, Select."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import Checkbox, NumberInput, Select, TextInput


class TestInputWidgets:
    """Tests for TextInput, NumberInput, Checkbox, and Select widgets."""

    def test_text_input_with_value(self) -> None:
        """TextInput stores value and placeholder props."""

        @component
        def App() -> None:
            """
            Renders a TextInput component pre-filled with "hello" and a placeholder.
            
            Used by tests to produce a TextInput element with value "hello" and placeholder "Enter text...".
            """
            TextInput(value="hello", placeholder="Enter text...")

        ctx = RenderSession(App)
        render(ctx)

        text_input = ctx.elements.get(ctx.root_element.child_ids[0])
        assert text_input.component.name == "TextInput"
        assert text_input.properties["value"] == "hello"
        assert text_input.properties["placeholder"] == "Enter text..."

    def test_text_input_with_callback(self) -> None:
        """TextInput captures on_change callback."""
        values: list[str] = []

        @component
        def App() -> None:
            """
            Render a TextInput for tests with a preset value and a change handler.
            
            This component renders a TextInput initialized with the value "test". Its on_change callback appends the new input value to the external `values` list used by the test.
            """
            TextInput(value="test", on_change=lambda v: values.append(v))

        ctx = RenderSession(App)
        render(ctx)

        text_input = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(text_input.properties["on_change"])

        text_input.properties["on_change"]("new value")
        assert values == ["new value"]

    def test_text_input_disabled(self) -> None:
        """TextInput accepts disabled prop."""

        @component
        def App() -> None:
            """
            Renders an application component containing a disabled TextInput.
            
            This component is used in tests to verify that a TextInput is rendered with its disabled property set to True.
            """
            TextInput(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        text_input = ctx.elements.get(ctx.root_element.child_ids[0])
        assert text_input.properties["disabled"] is True

    def test_number_input_with_value(self) -> None:
        """
        Verify that the NumberInput component preserves value, min, max, and step properties when rendered.
        """

        @component
        def App() -> None:
            """
            Renders a NumberInput component preconfigured with value 42 and range 0 to 100 with step 1.
            
            This App component is used in tests to produce a single NumberInput element with:
            - value set to 42
            - min set to 0
            - max set to 100
            - step set to 1
            """
            NumberInput(value=42, min=0, max=100, step=1)

        ctx = RenderSession(App)
        render(ctx)

        number_input = ctx.elements.get(ctx.root_element.child_ids[0])
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
            """
            Renders a NumberInput initialized to 10 with an on_change handler that appends the new value to the outer `values` list.
            """
            NumberInput(value=10, on_change=lambda v: values.append(v))

        ctx = RenderSession(App)
        render(ctx)

        number_input = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(number_input.properties["on_change"])

        number_input.properties["on_change"](25.5)
        assert values == [25.5]

    def test_number_input_disabled(self) -> None:
        """NumberInput accepts disabled prop."""

        @component
        def App() -> None:
            """
            Render a NumberInput component configured as disabled.
            
            This test component mounts a NumberInput with the `disabled` property set to True for use in rendering assertions.
            """
            NumberInput(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        number_input = ctx.elements.get(ctx.root_element.child_ids[0])
        assert number_input.properties["disabled"] is True

    def test_checkbox_with_checked(self) -> None:
        """Checkbox stores checked and label props."""

        @component
        def App() -> None:
            """
            Render a Checkbox component configured as checked with the label "Enable feature".
            
            This component invocation mounts a Checkbox with checked=True and label="Enable feature".
            """
            Checkbox(checked=True, label="Enable feature")

        ctx = RenderSession(App)
        render(ctx)

        checkbox = ctx.elements.get(ctx.root_element.child_ids[0])
        assert checkbox.component.name == "Checkbox"
        assert checkbox.properties["checked"] is True
        assert checkbox.properties["label"] == "Enable feature"

    def test_checkbox_with_callback(self) -> None:
        """
        Ensures Checkbox exposes an on_change callback that receives the updated checked state.
        
        Invokes the callback with True and asserts the provided handler is called with the boolean value.
        """
        states: list[bool] = []

        @component
        def App() -> None:
            """
            Renders a Checkbox initialized as unchecked with an on_change callback that appends the new value to the enclosing `states` list.
            
            Used by tests to verify the Checkbox's callback is invoked with the updated boolean value.
            """
            Checkbox(checked=False, on_change=lambda v: states.append(v))

        ctx = RenderSession(App)
        render(ctx)

        checkbox = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(checkbox.properties["on_change"])

        checkbox.properties["on_change"](True)
        assert states == [True]

    def test_checkbox_disabled(self) -> None:
        """Checkbox accepts disabled prop."""

        @component
        def App() -> None:
            """
            Render a disabled Checkbox component.
            
            Used by tests to verify that a Checkbox rendered with `disabled=True` produces the expected disabled element.
            """
            Checkbox(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        checkbox = ctx.elements.get(ctx.root_element.child_ids[0])
        assert checkbox.properties["disabled"] is True

    def test_select_with_options(self) -> None:
        """Select stores value and options props."""

        @component
        def App() -> None:
            """
            Renders a Select component configured with two options and a default selection.
            
            The rendered Select has a default value of "opt1", two options (Option 1 and Option 2), and a placeholder of "Choose...".
            """
            Select(
                value="opt1",
                options=[
                    {"value": "opt1", "label": "Option 1"},
                    {"value": "opt2", "label": "Option 2"},
                ],
                placeholder="Choose...",
            )

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert select.component.name == "Select"
        assert select.properties["value"] == "opt1"
        assert len(select.properties["options"]) == 2
        assert select.properties["placeholder"] == "Choose..."

    def test_select_with_callback(self) -> None:
        """Select captures on_change callback."""
        selections: list[str] = []

        @component
        def App() -> None:
            """
            Render a Select widget that records chosen values.
            
            The Select is initialized with value "opt1", a single option labeled "Option 1", and an on_change callback that appends the selected value to the outer `selections` list.
            """
            Select(
                value="opt1",
                options=[{"value": "opt1", "label": "Option 1"}],
                on_change=lambda v: selections.append(v),
            )

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(select.properties["on_change"])

        select.properties["on_change"]("opt2")
        assert selections == ["opt2"]

    def test_select_disabled(self) -> None:
        """Select accepts disabled prop."""

        @component
        def App() -> None:
            """
            Provide an App component that renders a Select widget with the disabled flag set.
            
            This component is used by the test to produce a rendered Select element with disabled=True.
            """
            Select(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert select.properties["disabled"] is True