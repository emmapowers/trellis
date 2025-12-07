"""Demo app to test end-to-end render loop.

Run with: pixi run -- python examples/demo.py
Then open: http://127.0.0.1:8000
"""

from dataclasses import dataclass

from trellis import Trellis
from trellis.core.functional_component import component
from trellis.core.state import Stateful
from trellis.utils.async_main import async_main
from trellis.widgets import Button, Column, Label, Row


@dataclass(kw_only=True)
class CounterState(Stateful):
    """Counter state with value constrained between 1 and 10."""

    count: int = 5


@component
def App() -> None:
    """Main application component with interactive counter."""
    state = CounterState()  # Cached across re-renders

    def increment() -> None:
        state.count = min(10, state.count + 1)

    def decrement() -> None:
        state.count = max(1, state.count - 1)

    with Column(gap=16, padding=20):
        Label(text="Counter Demo", font_size=24, color="blue")

        with Row(gap=8):
            Button(text="-", on_click=decrement, disabled=state.count <= 1)
            Label(text=str(state.count), font_size=20)
            Button(text="+", on_click=increment, disabled=state.count >= 10)


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App, port=8000)
    await app.serve()
