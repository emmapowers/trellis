"""Root application component for breakfast todo app."""

from trellis import Padding, component
from trellis import widgets as w

from .components import TodoFooter, TodoInput, TodoList
from .state import Todo, TodosState


@component
def App() -> None:
    """Main application component. Provides TodosState as context."""
    state = TodosState(
        todos=[
            Todo(id=1, text="🥓 Bacon"),
            Todo(id=2, text="🍳 Eggs"),
            Todo(id=3, text="🥞 Pancakes"),
            Todo(id=4, text="☕ Coffee"),
            Todo(id=5, text="🍞 Toast"),
        ]
    )

    with state:  # Provide state as context for child components
        with w.Column(padding=Padding(x=20, y=40), align="center"):
            with w.Card(padding=0, width=500, style={"overflow": "hidden"}):
                # Header
                with w.Column(
                    align="center",
                    padding=20,
                    style={"borderBottom": "1px solid #e2e8f0"},
                ):
                    w.Label(
                        text="🍳 breakfast todos",
                        font_size=24,
                        color="#6366f1",
                        font_weight=300,
                    )

                # Input
                with w.Column(padding=12, style={"borderBottom": "1px solid #e2e8f0"}):
                    TodoInput()

                # List
                TodoList()

                # Footer (only show if there are todos)
                if state.todos:
                    with w.Column(style={"borderTop": "1px solid #e2e8f0"}):
                        TodoFooter()
