"""UI components for the TODO app."""

from dataclasses import dataclass, field
from datetime import date

from trellis import mutable
from trellis.core.composition_component import component
from trellis.core.rendering import Element
from trellis.core.state import Stateful
from trellis import widgets as w

from .models import FilterType
from .state import TodosState


@component
def TodoApp() -> None:
    """Main application layout."""
    todos = TodosState.from_context()

    with w.Column(gap=16, padding=24, maxWidth=600):
        # Header
        w.Label(text="todos", fontSize=48, textColor="#b83f45", hAlign=w.Align.CENTER)

        # Error display
        if todos.error:
            ErrorBanner(message=todos.error, onDismiss=lambda: setattr(todos, "error", ""))

        # Input section
        TodoInput()

        # Tag filter bar
        if todos.tags:
            TagFilterBar()

        # Todo list
        TodoList()

        # Footer
        if todos.todos:
            TodoFooter()


@component
def ErrorBanner(message: str, onDismiss: callable) -> None:
    """Error message banner with dismiss button."""
    with w.Row(
        gap=8, padding=12, backgroundColor="#ffebee", borderRadius=4, hAlign=w.Align.SPACE_BETWEEN
    ):
        w.Label(text=message, textColor="#c62828")
        w.Button(label="Dismiss", variant="text", onClick=onDismiss)


# --- Local state for TodoInput ---
@dataclass
class NewTodoFormState(Stateful):
    text: str = ""
    due_date: date | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return bool(self.text.strip())

    def clear(self) -> None:
        self.text = ""
        self.due_date = None
        self.tags = []


@component
def TodoInput() -> None:
    """New todo input form with due date and tags."""
    todos = TodosState.from_context()
    form = NewTodoFormState()  # Local state

    async def submit():
        if not form.is_valid:
            return
        await todos.add_todo(
            text=form.text.strip(),
            due_date=form.due_date,
            tag_names=form.tags,
        )
        form.clear()

    with w.Column(gap=8):
        # Main input row
        with w.Row(gap=8):
            w.TextInput(
                text=mutable(form.text),
                placeholder="What needs to be done?",
                onEnter=submit,
                flex=1,
            )
            w.Button(label="Add", onClick=submit, disabled=not form.is_valid)

        # Optional fields row
        with w.Row(gap=8):
            w.DatePicker(
                value=mutable(form.due_date),
                placeholder="Due date (optional)",
            )
            w.TagInput(
                tags=mutable(form.tags),
                suggestions=[t.name for t in todos.tags],
                placeholder="Add tags...",
            )


@component
def TagFilterBar() -> None:
    """Horizontal bar of tag filters."""
    todos = TodosState.from_context()

    with w.Row(gap=4, wrap=True):
        # All tags button
        w.Button(
            label="All",
            variant="outlined" if todos.tag_filter else "contained",
            size="small",
            onClick=lambda: setattr(todos, "tag_filter", None),
        )
        # Individual tag buttons
        for tag in todos.tags:
            w.Button(
                label=tag.name,
                variant="contained" if todos.tag_filter == tag.name else "outlined",
                size="small",
                backgroundColor=tag.color if todos.tag_filter == tag.name else None,
                onClick=lambda t=tag: setattr(todos, "tag_filter", t.name),
            )


@component
def TodoList() -> None:
    """List of visible todos."""
    todos = TodosState.from_context()

    with w.Column(gap=0):
        if not todos.visible_todos:
            w.Label(
                text="No todos to show",
                textColor="#999",
                hAlign=w.Align.CENTER,
                padding=24,
            )
        else:
            for todo in todos.visible_todos:
                TodoItem(todo=todo, key=str(todo.id))


# --- Local state for TodoItem ---
@dataclass
class EditState(Stateful):
    editing_text: str = ""


@component
def TodoItem(todo) -> None:
    """Single todo item with edit, complete, and delete actions."""
    todos = TodosState.from_context()
    edit = EditState()  # Local state for edit text only

    is_editing = todos.editing_id == todo.id
    is_overdue = todo.due_date and todo.due_date < date.today() and not todo.completed

    def start_edit():
        todos.editing_id = todo.id  # Sets globally, cancels any other edit
        edit.editing_text = todo.text

    def cancel_edit():
        todos.editing_id = None
        edit.editing_text = ""

    async def save_edit():
        if edit.editing_text.strip():
            await todos.update_text(todo, edit.editing_text.strip())
        cancel_edit()

    with w.Row(
        gap=8,
        padding=12,
        borderBottom="1px solid #eee",
        backgroundColor="#fff3e0" if is_overdue else None,
        hAlign=w.Align.SPACE_BETWEEN,
    ):
        # Left side: checkbox and text/input
        with w.Row(gap=8, flex=1):
            w.Checkbox(checked=todo.completed, onChange=lambda: todos.toggle_complete(todo))

            if is_editing:
                w.TextInput(
                    text=mutable(edit.editing_text),
                    onEnter=save_edit,
                    onEscape=cancel_edit,
                    onBlur=save_edit,
                    autoFocus=True,
                    flex=1,
                )
            else:
                with w.Column(gap=4, flex=1):
                    w.Label(
                        text=todo.text,
                        textDecoration="line-through" if todo.completed else None,
                        textColor="#999" if todo.completed else None,
                        onDoubleClick=start_edit,
                    )
                    # Meta info row
                    with w.Row(gap=8):
                        if todo.due_date:
                            w.Label(
                                text=f"Due: {todo.due_date.isoformat()}",
                                fontSize=12,
                                textColor="#c62828" if is_overdue else "#666",
                            )
                        for tag_name in todo.tags:
                            w.Badge(text=tag_name, size="small")

        # Right side: action buttons
        with w.Row(gap=4):
            if is_editing:
                w.Button(label="Save", size="small", onClick=save_edit)
                w.Button(label="Cancel", size="small", variant="text", onClick=cancel_edit)
            else:
                w.Button(label="Edit", size="small", variant="text", onClick=start_edit)
                w.Button(
                    label="Delete",
                    size="small",
                    variant="text",
                    textColor="#c62828",
                    onClick=lambda: todos.delete_todo(todo.id),
                )


@component
def TodoFooter() -> None:
    """Footer with count, filters, and clear completed."""
    todos = TodosState.from_context()

    with w.Row(gap=16, padding=12, hAlign=w.Align.SPACE_BETWEEN):
        # Item count
        count_text = f"{todos.active_count} item{'s' if todos.active_count != 1 else ''} left"
        w.Label(text=count_text, textColor="#666")

        # Filter buttons
        with w.Row(gap=4):
            for filter_type in FilterType:
                w.Button(
                    label=filter_type.value.capitalize(),
                    variant="contained" if todos.filter == filter_type else "text",
                    size="small",
                    onClick=lambda f=filter_type: setattr(todos, "filter", f),
                )

        # Clear completed button
        if todos.completed_count > 0:
            w.Button(
                label=f"Clear completed ({todos.completed_count})",
                variant="text",
                size="small",
                onClick=todos.clear_completed,
            )
