"""SQLite3 database layer for the TODO app."""

import sqlite3
from datetime import date

from .models import Tag, Todo


class TodoDB:
    """SQLite3 database for todos with tags support."""

    def __init__(self, db_path: str = "todos.db") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                due_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#888888'
            );

            CREATE TABLE IF NOT EXISTS todo_tags (
                todo_id INTEGER REFERENCES todos(id) ON DELETE CASCADE,
                tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (todo_id, tag_id)
            );
        """)
        self.conn.commit()

    async def get_all_todos(self) -> list[Todo]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.id, t.text, t.completed, t.due_date,
                   GROUP_CONCAT(tg.name) as tags
            FROM todos t
            LEFT JOIN todo_tags tt ON t.id = tt.todo_id
            LEFT JOIN tags tg ON tt.tag_id = tg.id
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """)
        rows = cursor.fetchall()
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

    async def get_all_tags(self) -> list[Tag]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, color FROM tags ORDER BY name")
        return [Tag(id=row["id"], name=row["name"], color=row["color"]) for row in cursor.fetchall()]

    async def add_todo(self, text: str, due_date: date | None, tag_names: list[str]) -> Todo:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO todos (text, due_date) VALUES (?, ?)",
            (text, due_date.isoformat() if due_date else None),
        )
        todo_id = cursor.lastrowid

        for tag_name in tag_names:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_id = cursor.fetchone()["id"]
            cursor.execute("INSERT INTO todo_tags (todo_id, tag_id) VALUES (?, ?)", (todo_id, tag_id))

        self.conn.commit()
        return Todo(id=todo_id, text=text, completed=False, due_date=due_date, tags=tag_names)

    async def update_todo(
        self,
        todo_id: int,
        text: str | None = None,
        completed: bool | None = None,
        due_date: date | None = None,
    ) -> None:
        cursor = self.conn.cursor()
        updates = []
        params = []

        if text is not None:
            updates.append("text = ?")
            params.append(text)
        if completed is not None:
            updates.append("completed = ?")
            params.append(int(completed))
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date.isoformat())

        if updates:
            params.append(todo_id)
            cursor.execute(f"UPDATE todos SET {', '.join(updates)} WHERE id = ?", params)
            self.conn.commit()

    async def delete_todo(self, todo_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        self.conn.commit()

    async def clear_completed(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM todos WHERE completed = 1")
        self.conn.commit()

    async def add_tag(self, name: str, color: str = "#888888") -> Tag:
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)", (name, color))
        self.conn.commit()
        cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
        return Tag(id=cursor.fetchone()["id"], name=name, color=color)

    async def set_todo_tags(self, todo_id: int, tag_names: list[str]) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM todo_tags WHERE todo_id = ?", (todo_id,))

        for tag_name in tag_names:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_id = cursor.fetchone()["id"]
            cursor.execute("INSERT INTO todo_tags (todo_id, tag_id) VALUES (?, ?)", (todo_id, tag_id))

        self.conn.commit()


# Module-level database instance
db = TodoDB()
