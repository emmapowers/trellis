"""
Advanced TODO App Example

Demonstrates Trellis framework patterns with SQLite3 persistence,
due dates, and tag categorization.

Run with: python -m docs.planning.examples.todo.app
"""

from trellis import App
from trellis.core.functional_component import component
from trellis.core.rendering import Elements
from trellis.utils import async_main

from .components import TodoApp
from .state import TodosState


@component
def top() -> Elements:
    """Root component - provides TodosState context."""
    todos = TodosState()

    # Provide state as context - children access via TodosState.from_context()
    with todos:
        return TodoApp()


@async_main
async def main() -> None:
    # Load initial data before serving
    todos = TodosState()
    await todos.load_data()

    app = App()
    await app.serve(top)
