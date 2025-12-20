"""Form inputs section of the widget showcase."""

from trellis import Stateful, component, mutable
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


class TextInputState(Stateful):
    """State for text input example."""

    text_value: str = ""


@example("Text Input", state=TextInputState)
def TextInputExample() -> None:
    """Single-line text entry."""
    state = TextInputState()
    with state:
        with w.Row(gap=8, align="center"):
            w.Label(text="Name:", width=80)
            w.TextInput(
                value=mutable(state.text_value),
                placeholder="Enter text...",
                width=200,
            )


class NumberInputState(Stateful):
    """State for number input example."""

    number_value: int = 50


@example("Number Input", state=NumberInputState)
def NumberInputExample() -> None:
    """Numeric entry with min/max bounds."""
    state = NumberInputState()
    with state:
        with w.Row(gap=8, align="center"):
            w.Label(text="Value:", width=80)
            w.NumberInput(
                value=mutable(state.number_value),
                min=0,
                max=100,
                width=200,
            )


class SelectState(Stateful):
    """State for select example."""

    select_value: str = "option1"


@example("Select", state=SelectState)
def SelectExample() -> None:
    """Dropdown selection from options."""
    state = SelectState()
    with state:
        with w.Row(gap=8, align="center"):
            w.Label(text="Choice:", width=80)
            w.Select(
                value=mutable(state.select_value),
                options=[
                    {"value": "option1", "label": "Option 1"},
                    {"value": "option2", "label": "Option 2"},
                    {"value": "option3", "label": "Option 3"},
                ],
                width=200,
            )


class CheckboxState(Stateful):
    """State for checkbox example."""

    checkbox_value: bool = False


@example("Checkbox", state=CheckboxState)
def CheckboxExample() -> None:
    """Boolean toggle control."""
    state = CheckboxState()
    with state:
        with w.Row(gap=8, align="center"):
            w.Label(text="Toggle:", width=80)
            w.Checkbox(
                checked=mutable(state.checkbox_value),
                label="Enable feature",
            )


class SliderState(Stateful):
    """State for slider example."""

    slider_value: float = 50


@example("Slider", state=SliderState)
def SliderExample() -> None:
    """Range selection with visual feedback."""
    state = SliderState()
    with state:
        with w.Row(gap=8, align="center"):
            w.Label(text="Level:", width=80)
            w.Slider(
                value=mutable(state.slider_value),
                min=0,
                max=100,
                width=200,
            )
            w.Label(text=f"{int(state.slider_value)}", width=40)


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    with w.Column(gap=16):
        ExampleCard(example=TextInputExample)
        ExampleCard(example=NumberInputExample)
        ExampleCard(example=SelectExample)
        ExampleCard(example=CheckboxExample)
        ExampleCard(example=SliderExample)
