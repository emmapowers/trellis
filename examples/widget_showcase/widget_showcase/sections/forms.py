"""Form inputs section of the widget showcase."""

from trellis import component, mutable, state
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Form Inputs")
def FormInputs() -> None:
    """Interactive form controls with two-way data binding."""
    text_value = state("")
    number_value = state(50)
    select_value = state("option1")
    checkbox_value = state(False)
    slider_value = state(50.0)

    with w.Column(gap=12):
        with w.Row(gap=8, align="center"):
            w.Label(text="Text:", width=80)
            w.TextInput(
                value=mutable(text_value.value),
                placeholder="Enter text...",
                width=200,
            )

        with w.Row(gap=8, align="center"):
            w.Label(text="Number:", width=80)
            w.NumberInput(
                value=mutable(number_value.value),
                min=0,
                max=100,
                width=200,
            )

        with w.Row(gap=8, align="center"):
            w.Label(text="Select:", width=80)
            w.Select(
                value=mutable(select_value.value),
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
                checked=mutable(checkbox_value.value),
                label="Enable feature",
            )

        with w.Row(gap=8, align="center"):
            w.Label(text="Slider:", width=80)
            w.Slider(
                value=mutable(slider_value.value),
                min=0,
                max=100,
                width=200,
            )
            w.Label(text=f"{int(slider_value.value)}", width=40)


@example("Multiline Input")
def MultilineFormInput() -> None:
    """Multi-line text input with mutable state binding."""
    text_value = state("Line one\nLine two")

    with w.Column(gap=8):
        w.MultilineInput(
            value=mutable(text_value.value),
            placeholder="Write multiple lines...",
            rows=6,
            width=440,
        )
        w.Label(text=f"Length: {len(text_value.value)} chars")


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    with w.Column(gap=16):
        ExampleCard(example=FormInputs)
        ExampleCard(example=MultilineFormInput)
