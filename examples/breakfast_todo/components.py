"""UI components for the todo app."""

from trellis import Padding, component
from trellis import widgets as w

from .state import FilterType, Todo, TodosState


@component
def TodoInput() -> None:
    """Input field and button for adding new todos."""
    state = TodosState.from_context()

    with w.Row(gap=8):
        w.TextInput(
            value=state.input_text,
            placeholder="What needs to be done?",
            on_change=state.set_input,
            flex=1,
        )
        w.Button(
            text="Add",
            on_click=state.add_todo,
            disabled=not state.input_text.strip(),
        )


@component
def TodoItem(todo: Todo) -> None:
    """Single todo item with toggle and delete actions."""
    state = TodosState.from_context()

    def toggle(checked: bool) -> None:
        todo.completed = checked

    def delete() -> None:
        state.delete_todo(todo.id)

    with w.Row(
        gap=12,
        align="center",
        padding=Padding(x=12, y=10),
    ):
        w.Checkbox(
            checked=todo.completed,
            on_change=toggle,
        )

        w.Label(
            text=todo.text,
            flex=1,
            style={
                "textDecoration": "line-through" if todo.completed else "none",
                "color": "#94a3b8" if todo.completed else None,
            },
        )

        w.Button(
            text="Delete",
            on_click=delete,
            variant="danger",
            size="sm",
        )


@component
def TodoList() -> None:
    """List of visible todos."""
    state = TodosState.from_context()

    with w.Column(gap=0, divider=True):
        if not state.visible_todos:
            w.Label(
                text="No todos to show",
                color="#94a3b8",
                padding=20,
                text_align="center",
            )
        else:
            for todo in state.visible_todos:
                TodoItem(todo=todo, key=str(todo.id))


@component
def TodoFooter() -> None:
    """Footer with count, filters, and clear completed button."""
    state = TodosState.from_context()

    def set_filter(f: FilterType) -> None:
        state.filter = f

    with w.Row(gap=12, align="center", justify="between", padding=Padding(x=12, y=10)):
        # Item count
        count_text = f"{state.active_count} item{'s' if state.active_count != 1 else ''} left"
        w.Label(text=count_text, color="#64748b", font_size=12)

        # Filter buttons
        with w.Row(gap=4):
            for filter_type in FilterType:
                w.Button(
                    text=filter_type.value.capitalize(),
                    on_click=lambda f=filter_type: set_filter(f),
                    variant="primary" if state.filter == filter_type else "ghost",
                    size="sm",
                )

        # Clear completed
        if state.completed_count > 0:
            w.Button(
                text=f"Clear completed ({state.completed_count})",
                on_click=state.clear_completed,
                variant="ghost",
                size="sm",
            )
