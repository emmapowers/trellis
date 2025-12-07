"""Data models for the TODO app."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum, auto

from trellis.core.state import Stateful


@dataclass
class Todo(Stateful):
    """A todo item - Stateful so property changes trigger re-renders."""

    id: int
    text: str
    completed: bool
    due_date: date | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Tag(Stateful):
    """A tag - Stateful for potential future editing."""

    id: int
    name: str
    color: str = "#888888"


class FilterType(StrEnum):
    ALL = auto()
    ACTIVE = auto()
    COMPLETED = auto()
