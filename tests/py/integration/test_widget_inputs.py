"""Tests for input widgets: TextInput, NumberInput, Checkbox, Select, MultilineInput."""

from trellis.core.components.composition import component
from trellis.widgets import Checkbox, MultilineInput, NumberInput, Select, TextInput


class TestInputWidgets:
    """Tests for TextInput, NumberInput, Checkbox, and Select widgets."""

    def test_text_input_with_value(self, rendered) -> None:
        """TextInput stores value and placeholder props."""

        @component
        def App() -> None:
            TextInput(value="hello", placeholder="Enter text...")

        result = rendered(App)

        text_input = result.session.elements.get(result.root_element.child_ids[0])
        assert text_input.component.name == "TextInput"
        assert text_input.properties["value"] == "hello"
        assert text_input.properties["placeholder"] == "Enter text..."

    def test_text_input_with_callback(self, rendered) -> None:
        """TextInput captures on_change callback."""
        values: list[str] = []

        @component
        def App() -> None:
            TextInput(value="test", on_change=lambda v: values.append(v))

        result = rendered(App)

        text_input = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(text_input.properties["on_change"])

        text_input.properties["on_change"]("new value")
        assert values == ["new value"]

    def test_text_input_disabled(self, rendered) -> None:
        """TextInput accepts disabled prop."""

        @component
        def App() -> None:
            TextInput(disabled=True)

        result = rendered(App)

        text_input = result.session.elements.get(result.root_element.child_ids[0])
        assert text_input.properties["disabled"] is True

    def test_number_input_with_value(self, rendered) -> None:
        """NumberInput stores value and range props."""

        @component
        def App() -> None:
            NumberInput(value=42, min=0, max=100, step=1)

        result = rendered(App)

        number_input = result.session.elements.get(result.root_element.child_ids[0])
        assert number_input.component.name == "NumberInput"
        assert number_input.properties["value"] == 42
        assert number_input.properties["min"] == 0
        assert number_input.properties["max"] == 100
        assert number_input.properties["step"] == 1

    def test_number_input_with_callback(self, rendered) -> None:
        """NumberInput captures on_change callback."""
        values: list[float] = []

        @component
        def App() -> None:
            NumberInput(value=10, on_change=lambda v: values.append(v))

        result = rendered(App)

        number_input = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(number_input.properties["on_change"])

        number_input.properties["on_change"](25.5)
        assert values == [25.5]

    def test_number_input_disabled(self, rendered) -> None:
        """NumberInput accepts disabled prop."""

        @component
        def App() -> None:
            NumberInput(disabled=True)

        result = rendered(App)

        number_input = result.session.elements.get(result.root_element.child_ids[0])
        assert number_input.properties["disabled"] is True

    def test_checkbox_with_checked(self, rendered) -> None:
        """Checkbox stores checked and label props."""

        @component
        def App() -> None:
            Checkbox(checked=True, label="Enable feature")

        result = rendered(App)

        checkbox = result.session.elements.get(result.root_element.child_ids[0])
        assert checkbox.component.name == "Checkbox"
        assert checkbox.properties["checked"] is True
        assert checkbox.properties["label"] == "Enable feature"

    def test_checkbox_with_callback(self, rendered) -> None:
        """Checkbox captures on_change callback."""
        states: list[bool] = []

        @component
        def App() -> None:
            Checkbox(checked=False, on_change=lambda v: states.append(v))

        result = rendered(App)

        checkbox = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(checkbox.properties["on_change"])

        checkbox.properties["on_change"](True)
        assert states == [True]

    def test_checkbox_disabled(self, rendered) -> None:
        """Checkbox accepts disabled prop."""

        @component
        def App() -> None:
            Checkbox(disabled=True)

        result = rendered(App)

        checkbox = result.session.elements.get(result.root_element.child_ids[0])
        assert checkbox.properties["disabled"] is True

    def test_select_with_options(self, rendered) -> None:
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

        result = rendered(App)

        select = result.session.elements.get(result.root_element.child_ids[0])
        assert select.component.name == "Select"
        assert select.properties["value"] == "opt1"
        assert len(select.properties["options"]) == 2
        assert select.properties["placeholder"] == "Choose..."

    def test_select_with_callback(self, rendered) -> None:
        """Select captures on_change callback."""
        selections: list[str] = []

        @component
        def App() -> None:
            Select(
                value="opt1",
                options=[{"value": "opt1", "label": "Option 1"}],
                on_change=lambda v: selections.append(v),
            )

        result = rendered(App)

        select = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(select.properties["on_change"])

        select.properties["on_change"]("opt2")
        assert selections == ["opt2"]

    def test_select_disabled(self, rendered) -> None:
        """Select accepts disabled prop."""

        @component
        def App() -> None:
            Select(disabled=True)

        result = rendered(App)

        select = result.session.elements.get(result.root_element.child_ids[0])
        assert select.properties["disabled"] is True

    def test_multiline_input_with_value(self, rendered) -> None:
        """MultilineInput stores value and placeholder props."""

        @component
        def App() -> None:
            MultilineInput(value="line one\nline two", placeholder="Enter text...")

        result = rendered(App)

        multiline = result.session.elements.get(result.root_element.child_ids[0])
        assert multiline.component.name == "MultilineInput"
        assert multiline.properties["value"] == "line one\nline two"
        assert multiline.properties["placeholder"] == "Enter text..."

    def test_multiline_input_with_callback(self, rendered) -> None:
        """MultilineInput captures on_change callback."""
        values: list[str] = []

        @component
        def App() -> None:
            MultilineInput(value="test", on_change=lambda v: values.append(v))

        result = rendered(App)

        multiline = result.session.elements.get(result.root_element.child_ids[0])
        assert callable(multiline.properties["on_change"])

        multiline.properties["on_change"]("updated")
        assert values == ["updated"]

    def test_multiline_input_disabled_and_read_only(self, rendered) -> None:
        """MultilineInput accepts disabled and read_only props."""

        @component
        def App() -> None:
            MultilineInput(disabled=True, read_only=True)

        result = rendered(App)

        multiline = result.session.elements.get(result.root_element.child_ids[0])
        assert multiline.properties["disabled"] is True
        assert multiline.properties["read_only"] is True
