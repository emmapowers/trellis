"""Root application component for breakfast todo app."""

from trellis import component
from trellis import html as h
from trellis import widgets as w
from trellis.app import App, theme

from .components import TodoFooter, TodoInput, TodoList
from .state import Todo, TodosState


@component
def BreakfastTodo() -> None:
    """Main application component. Provides TodosState as context."""
    state = TodosState(
        todos=[
            Todo(id=1, text="🥓 Bacon"),
            Todo(id=2, text="🍳 Eggs"),
            Todo(id=3, text="🥞 Pancakes"),
            Todo(id=4, text="☕ Coffee"),
            Todo(id=5, text="🍞 Toast"),
        ],
        _next_id=6,  # Start after existing IDs
    )

    with state:  # Provide state as context for child components
        with w.Column(padding=h.padding(40, 20), align="center"):
            with w.Card(padding=0, width=500, style=h.Style(overflow="hidden")):
                # Header
                with w.Column(
                    align="center",
                    padding=20,
                    style=h.Style(border_bottom=f"1px solid {theme.border_default}"),
                ):
                    w.Label(
                        text="🍳 breakfast todos",
                        font_size=24,
                        color=theme.accent_primary,
                        font_weight=300,
                    )

                # Input
                with w.Column(
                    padding=12, style=h.Style(border_bottom=f"1px solid {theme.border_default}")
                ):
                    TodoInput()

                # List
                TodoList()

                # Footer (only show if there are todos)
                if state.todos:
                    with w.Column(style=h.Style(border_top=f"1px solid {theme.border_default}")):
                        TodoFooter()


app = App(BreakfastTodo)
