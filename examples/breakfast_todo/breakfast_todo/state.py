"""Application state for the todo app."""

from dataclasses import dataclass, field
from enum import StrEnum, auto

from trellis import Stateful


@dataclass
class Todo(Stateful):
    """A todo item. Inherits from Stateful so property changes trigger re-renders."""

    id: int
    text: str
    completed: bool = False


class FilterType(StrEnum):
    """Filter options for the todo list."""

    ALL = auto()
    ACTIVE = auto()
    COMPLETED = auto()


@dataclass
class TodosState(Stateful):
    """Shared state for the todo app. Provided as context to child components."""

    # Data
    todos: list[Todo] = field(default_factory=list)
    filter: FilterType = FilterType.ALL

    # Input state (for controlled input)
    input_text: str = ""

    # Auto-incrementing ID for new todos
    _next_id: int = 1

    @property
    def visible_todos(self) -> list[Todo]:
        """Get todos filtered by current filter setting."""
        match self.filter:
            case FilterType.ALL:
                return self.todos
            case FilterType.ACTIVE:
                return [t for t in self.todos if not t.completed]
            case FilterType.COMPLETED:
                return [t for t in self.todos if t.completed]

    @property
    def active_count(self) -> int:
        """Count of incomplete todos."""
        return sum(1 for t in self.todos if not t.completed)

    @property
    def completed_count(self) -> int:
        """Count of completed todos."""
        return sum(1 for t in self.todos if t.completed)

    def add_todo(self) -> None:
        """Add a new todo from the current input text."""
        text = self.input_text.strip()
        if not text:
            return

        todo = Todo(id=self._next_id, text=text)
        self._next_id += 1

        self.todos.insert(0, todo)
        self.input_text = ""

    def delete_todo(self, todo_id: int) -> None:
        """Delete a todo by ID."""
        for todo in self.todos:
            if todo.id == todo_id:
                self.todos.remove(todo)
                break

    def clear_completed(self) -> None:
        """Remove all completed todos."""
        for todo in [t for t in self.todos if t.completed]:
            self.todos.remove(todo)

    def set_input(self, text: str) -> None:
        """Update the input text (for controlled input)."""
        self.input_text = text
