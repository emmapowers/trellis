"""
Advanced TODO App Example

Demonstrates Trellis framework patterns with SQLite3 persistence,
due dates, and tag categorization.

Run with: python -m docs.planning.examples.todo.app
"""

import asyncio

from trellis import App
from trellis.core.functional_component import component
from trellis.core.rendering import Elements

from .components import TodoApp
from .state import TodosState


@component
def top() -> Elements:
    """Root component - provides TodosState context."""
    todos = TodosState()

    # Provide state as context - children access via TodosState.from_context()
    with todos:
        return TodoApp()


async def main():
    # Load initial data before serving
    todos = TodosState()
    await todos.load_data()

    app = App()
    await app.serve(top)


if __name__ == "__main__":
    asyncio.run(main())
