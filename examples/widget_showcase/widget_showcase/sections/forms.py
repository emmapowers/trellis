"""Form inputs section of the widget showcase."""

from trellis import Stateful, component, mutable
from trellis import widgets as w
from trellis.desktop import open_file, open_files, save_file, select_directory

from ..components import ExampleCard
from ..example import example


class FormState(Stateful):
    """State for form inputs example."""

    text_value: str = ""
    number_value: int = 50
    select_value: str = "option1"
    checkbox_value: bool = False
    slider_value: float = 50


class DesktopDialogState(Stateful):
    """State for desktop dialog demo."""

    selected_file: str = "None"
    selected_files: str = "None"
    save_path: str = "None"
    selected_directory: str = "None"
    error: str = ""


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


@example("Desktop File Dialogs", includes=[DesktopDialogState])
def DesktopFileDialogs() -> None:
    """Desktop-native open/save/select dialog examples."""
    state = DesktopDialogState()
    with state:

        async def choose_file() -> None:
            try:
                result = await open_file()
                state.selected_file = str(result) if result is not None else "Cancelled"
                state.error = ""
            except RuntimeError as exc:
                state.error = str(exc)

        async def choose_files() -> None:
            try:
                result = await open_files()
                state.selected_files = (
                    ", ".join(str(path) for path in result) if result else "Cancelled"
                )
                state.error = ""
            except RuntimeError as exc:
                state.error = str(exc)

        async def choose_save_path() -> None:
            try:
                result = await save_file()
                state.save_path = str(result) if result is not None else "Cancelled"
                state.error = ""
            except RuntimeError as exc:
                state.error = str(exc)

        async def choose_directory() -> None:
            try:
                result = await select_directory()
                state.selected_directory = str(result) if result is not None else "Cancelled"
                state.error = ""
            except RuntimeError as exc:
                state.error = str(exc)

        with w.Column(gap=8):
            with w.Row(gap=8):
                w.Button(text="Open File", on_click=choose_file)
                w.Button(text="Open Files", on_click=choose_files)
                w.Button(text="Save File", on_click=choose_save_path)
                w.Button(text="Select Directory", on_click=choose_directory)
            w.Label(text=f"File: {state.selected_file}")
            w.Label(text=f"Files: {state.selected_files}")
            w.Label(text=f"Save: {state.save_path}")
            w.Label(text=f"Directory: {state.selected_directory}")
            if state.error:
                w.Label(text=state.error)


@component
def FormInputsSection() -> None:
    """Showcase form input widgets."""
    with w.Column(gap=16):
        ExampleCard(example=FormInputs)
        ExampleCard(example=DesktopFileDialogs)
