"""Root application component."""

from trellis import component
from trellis import widgets as w

from .components import TodoFooter, TodoInput, TodoList
from .state import TodosState, Todo


STYLE_PAGE = {
    "minHeight": "100vh",
    "backgroundColor": "#0f172a",
    "padding": "40px 20px",
    "fontFamily": "'Inter', system-ui, sans-serif",
}


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
        with w.Column(style=STYLE_PAGE, align="center"):
            with w.Card(padding=0, style={"width": "500px", "overflow": "hidden"}):
                # Header
                with w.Column(
                    align="center",
                    style={"padding": "24px", "borderBottom": "1px solid #334155"},
                ):
                    w.Label(
                        text="todos",
                        font_size=32,
                        color="#b83f45",
                        style={"fontWeight": "300"},
                    )

                # Input
                with w.Column(style={"padding": "16px", "borderBottom": "1px solid #334155"}):
                    TodoInput()

                # List
                TodoList()

                # Footer (only show if there are todos)
                if state.todos:
                    with w.Column(style={"borderTop": "1px solid #334155"}):
                        TodoFooter()
