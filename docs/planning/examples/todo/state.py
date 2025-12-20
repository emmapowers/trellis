"""Application state for the TODO app."""

from dataclasses import dataclass, field
from datetime import date

from trellis.core.state import Stateful

from .models import FilterType, Tag, Todo
from .database import db


@dataclass
class TodosState(Stateful):
    """Shared state for todos - provided as context."""

    # Data
    todos: list[Todo] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)
    error: str = ""

    # Filters
    filter: FilterType = FilterType.ALL
    tag_filter: str | None = None

    # Edit tracking (only one todo editable at a time)
    editing_id: int | None = None

    @property
    def visible_todos(self) -> list[Todo]:
        """Filter todos based on current filter settings."""
        result = self.todos

        match self.filter:
            case FilterType.ACTIVE:
                result = [t for t in result if not t.completed]
            case FilterType.COMPLETED:
                result = [t for t in result if t.completed]

        if self.tag_filter:
            result = [t for t in result if self.tag_filter in t.tags]

        return result

    @property
    def active_count(self) -> int:
        return sum(1 for t in self.todos if not t.completed)

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.todos if t.completed)

    # --- Data operations ---

    async def load_data(self) -> None:
        """Load initial data from database."""
        self.todos = await db.get_all_todos()
        self.tags = await db.get_all_tags()

    async def add_todo(self, text: str, due_date: date | None, tag_names: list[str]) -> None:
        """Add a new todo."""
        try:
            todo = await db.add_todo(text=text, due_date=due_date, tag_names=tag_names)
            self.todos.insert(0, todo)
            self.tags = await db.get_all_tags()
        except Exception as e:
            self.error = f"Failed to add todo: {e}"

    async def toggle_complete(self, todo: Todo) -> None:
        """Toggle a todo's completion status."""
        try:
            todo.completed = not todo.completed  # Auto-triggers re-render
            await db.update_todo(todo.id, completed=todo.completed)
        except Exception as e:
            self.error = f"Failed to update todo: {e}"

    async def update_text(self, todo: Todo, text: str) -> None:
        """Update a todo's text."""
        try:
            todo.text = text  # Auto-triggers re-render
            await db.update_todo(todo.id, text=text)
        except Exception as e:
            self.error = f"Failed to update todo: {e}"

    async def delete_todo(self, todo_id: int) -> None:
        """Delete a todo."""
        try:
            await db.delete_todo(todo_id)
            todo = next(t for t in self.todos if t.id == todo_id)
            self.todos.remove(todo)
        except Exception as e:
            self.error = f"Failed to delete todo: {e}"

    async def clear_completed(self) -> None:
        """Clear all completed todos."""
        try:
            await db.clear_completed()
            for todo in [t for t in self.todos if t.completed]:
                self.todos.remove(todo)
        except Exception as e:
            self.error = f"Failed to clear completed: {e}"
