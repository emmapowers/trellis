"""Demo app to test end-to-end render loop.

Run with: pixi run -- python examples/demo.py
Then open: http://127.0.0.1:8000
"""

from trellis import Trellis
from trellis.core.functional_component import component
from trellis.utils.async_main import async_main
from trellis.widgets import Button, Column, Label, Row


@component
def App() -> None:
    """Main application component."""
    with Column(gap=16, padding=20):
        Label(text="Hello from Trellis!", font_size=24, color="blue")

        with Row(gap=8):
            Label(text="This is rendered from Python")

        with Column(gap=4):
            Label(text="Item 1")
            Label(text="Item 2")
            Label(text="Item 3")

        with Row(gap=8):
            Button(text="Click Me", on_click=lambda: print("Button clicked!"))
            Button(text="Disabled", disabled=True)


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App, port=8000)
    await app.serve()
