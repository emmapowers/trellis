"""Form inputs section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..state import ShowcaseState


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    state = ShowcaseState.from_context()

    with w.Column(gap=12):
        # Text input
        with w.Row(gap=8, align="center"):
            w.Label(text="Text:", width=80)
            w.TextInput(
                value=state.text_value,
                placeholder="Enter text...",
                on_change=lambda v: setattr(state, "text_value", v),
                width=200,
            )

        # Number input
        with w.Row(gap=8, align="center"):
            w.Label(text="Number:", width=80)
            w.NumberInput(
                value=state.number_value,
                min=0,
                max=100,
                on_change=lambda v: setattr(state, "number_value", v),
                width=200,
            )

        # Select
        with w.Row(gap=8, align="center"):
            w.Label(text="Select:", width=80)
            w.Select(
                value=state.select_value,
                options=[
                    {"value": "option1", "label": "Option 1"},
                    {"value": "option2", "label": "Option 2"},
                    {"value": "option3", "label": "Option 3"},
                ],
                on_change=lambda v: setattr(state, "select_value", v),
                width=200,
            )

        # Checkbox
        with w.Row(gap=8, align="center"):
            w.Label(text="Toggle:", width=80)
            w.Checkbox(
                checked=state.checkbox_value,
                label="Enable feature",
                on_change=lambda v: setattr(state, "checkbox_value", v),
            )

        # Slider
        with w.Row(gap=8, align="center"):
            w.Label(text="Slider:", width=80)
            w.Slider(
                value=state.slider_value,
                min=0,
                max=100,
                on_change=lambda v: setattr(state, "slider_value", v),
                width=200,
            )
            w.Label(text=f"{int(state.slider_value)}", width=40)
