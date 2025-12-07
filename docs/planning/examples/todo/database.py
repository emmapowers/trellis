"""SQLite database layer for the TODO app using dataset."""

from datetime import date

import dataset

from .models import Tag, Todo

# Module-level database instance
db = dataset.connect("sqlite:///todos.db")


def _ensure_tables() -> None:
    """Create tables if they don't exist."""
    db.query("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.query("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#888888'
        )
    """)
    db.query("""
        CREATE TABLE IF NOT EXISTS todo_tags (
            todo_id INTEGER REFERENCES todos(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (todo_id, tag_id)
        )
    """)


_ensure_tables()


async def get_all_todos() -> list[Todo]:
    """Get all todos with their tags."""
    rows = db.query("""
        SELECT t.id, t.text, t.completed, t.due_date,
               GROUP_CONCAT(tg.name) as tags
        FROM todos t
        LEFT JOIN todo_tags tt ON t.id = tt.todo_id
        LEFT JOIN tags tg ON tt.tag_id = tg.id
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """)
    return [
        Todo(
            id=row["id"],
            text=row["text"],
            completed=bool(row["completed"]),
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
            tags=row["tags"].split(",") if row["tags"] else [],
        )
        for row in rows
    ]


async def get_all_tags() -> list[Tag]:
    """Get all tags."""
    return [
        Tag(id=row["id"], name=row["name"], color=row["color"])
        for row in db["tags"].find(order_by="name")
    ]


async def add_todo(text: str, due_date: date | None, tag_names: list[str]) -> Todo:
    """Add a new todo with optional tags."""
    todo_id = db["todos"].insert({
        "text": text,
        "due_date": due_date.isoformat() if due_date else None,
    })

    for tag_name in tag_names:
        db["tags"].upsert({"name": tag_name}, ["name"])
        tag = db["tags"].find_one(name=tag_name)
        db["todo_tags"].insert({"todo_id": todo_id, "tag_id": tag["id"]})

    return Todo(id=todo_id, text=text, completed=False, due_date=due_date, tags=tag_names)


async def update_todo(
    todo_id: int,
    text: str | None = None,
    completed: bool | None = None,
    due_date: date | None = None,
) -> None:
    """Update a todo's fields."""
    updates = {"id": todo_id}
    if text is not None:
        updates["text"] = text
    if completed is not None:
        updates["completed"] = int(completed)
    if due_date is not None:
        updates["due_date"] = due_date.isoformat()

    if len(updates) > 1:
        db["todos"].update(updates, ["id"])


async def delete_todo(todo_id: int) -> None:
    """Delete a todo."""
    db["todo_tags"].delete(todo_id=todo_id)
    db["todos"].delete(id=todo_id)


async def clear_completed() -> None:
    """Delete all completed todos."""
    for todo in db["todos"].find(completed=1):
        db["todo_tags"].delete(todo_id=todo["id"])
    db["todos"].delete(completed=1)


async def add_tag(name: str, color: str = "#888888") -> Tag:
    """Add a new tag."""
    db["tags"].upsert({"name": name, "color": color}, ["name"])
    tag = db["tags"].find_one(name=name)
    return Tag(id=tag["id"], name=name, color=color)


async def set_todo_tags(todo_id: int, tag_names: list[str]) -> None:
    """Set the tags for a todo."""
    db["todo_tags"].delete(todo_id=todo_id)

    for tag_name in tag_names:
        db["tags"].upsert({"name": tag_name}, ["name"])
        tag = db["tags"].find_one(name=tag_name)
        db["todo_tags"].insert({"todo_id": todo_id, "tag_id": tag["id"]})
