"""Form inputs section of the widget showcase."""

from trellis import Stateful, component, mutable, state_var
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


class FormInputsState(Stateful):
    """State for form inputs example."""

    text_value: str = ""
    number_value: int = 50
    select_value: str = "option1"
    checkbox_value: bool = False
    slider_value: float = 50.0


@example("Form Inputs", includes=[FormInputsState])
def FormInputs() -> None:
    """Interactive form controls with two-way data binding."""
    form = FormInputsState()
    with form:
        with w.Column(gap=12):
            with w.Row(gap=8, align="center"):
                w.Label(text="Text:", width=80)
                w.TextInput(
                    value=mutable(form.text_value),
                    placeholder="Enter text...",
                    width=200,
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Number:", width=80)
                w.NumberInput(
                    value=mutable(form.number_value),
                    min=0,
                    max=100,
                    width=200,
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Select:", width=80)
                w.Select(
                    value=mutable(form.select_value),
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
                    checked=mutable(form.checkbox_value),
                    label="Enable feature",
                )

            with w.Row(gap=8, align="center"):
                w.Label(text="Slider:", width=80)
                w.Slider(
                    value=mutable(form.slider_value),
                    min=0,
                    max=100,
                    width=200,
                )
                w.Label(text=f"{int(form.slider_value)}", width=40)


@example("Multiline Input")
def MultilineFormInput() -> None:
    """Multi-line text input with mutable state binding."""
    text_value = state_var("Line one\nLine two")

    with w.Column(gap=8):
        w.MultilineInput(
            value=mutable(text_value),
            placeholder="Write multiple lines...",
            rows=6,
            width=440,
        )
        w.Label(text=f"Length: {len(text_value)} chars")


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    with w.Column(gap=16):
        ExampleCard(example=FormInputs)
        ExampleCard(example=MultilineFormInput)
