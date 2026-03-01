"""Desktop-only widget showcase section."""

from trellis import Stateful, component
from trellis import widgets as w
from trellis.desktop import open_file, open_files, save_file, select_directory

from ..components import ExampleCard
from ..example import example


class DesktopDialogState(Stateful):
    """State for desktop dialog demo."""

    selected_file: str = "None"
    selected_files: str = "None"
    save_path: str = "None"
    selected_directory: str = "None"
    error: str = ""


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
def DesktopSection() -> None:
    """Showcase desktop-only widgets and APIs."""
    with w.Column(gap=16):
        ExampleCard(example=DesktopFileDialogs)
