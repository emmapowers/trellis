"""Form inputs section of the widget showcase."""

from trellis import Stateful, component, mutable
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


class FormState(Stateful):
    """State for form inputs example."""

    text_value: str = ""
    number_value: int = 50
    select_value: str = "option1"
    checkbox_value: bool = False
    slider_value: float = 50


class MultilineFormState(Stateful):
    """State for multiline input example."""

    text_value: str = "Line one\nLine two"


@example("Form Inputs", includes=[FormState])
def FormInputs() -> None:
    """Interactive form controls with two-way data binding."""
    state = FormState()
    with state:
        with w.Column(gap=12):
            with w.Row(gap=8, align="center"):
                w.Label(text="Text:", width=80)
                w.TextInput(
                    value=mutable(state.text_value),
                    placeholder="Enter text...",
                    width=200,
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Number:", width=80)
                w.NumberInput(
                    value=mutable(state.number_value),
                    min=0,
                    max=100,
                    width=200,
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Select:", width=80)
                w.Select(
                    value=mutable(state.select_value),
                    options=[
                        {"value": "option1", "label": "Option 1"},
                        {"value": "option2", "label": "Option 2"},
                        {"value": "option3", "label": "Option 3"},
                    ],
                    width=200,
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Toggle:", width=80)
                w.Checkbox(
                    checked=mutable(state.checkbox_value),
                    label="Enable feature",
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Slider:", width=80)
                w.Slider(
                    value=mutable(state.slider_value),
                    min=0,
                    max=100,
                    width=200,
                )
                w.Label(text=f"{int(state.slider_value)}", width=40)


@example("Multiline Input", includes=[MultilineFormState])
def MultilineFormInput() -> None:
    """Multi-line text input with mutable state binding."""
    state = MultilineFormState()
    with state:
        with w.Column(gap=8):
            w.MultilineInput(
                value=mutable(state.text_value),
                placeholder="Write multiple lines...",
                rows=6,
                width=440,
            )
            w.Label(text=f"Length: {len(state.text_value)} chars")


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    with w.Column(gap=16):
        ExampleCard(example=FormInputs)
        ExampleCard(example=MultilineFormInput)
