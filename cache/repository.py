import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

from jsonschema import Draft202012Validator


Document = Mapping[str, Any]
PathLike = Union[str, Path]


class CacheRepository:
    """Validate condensed notes and store/query them in SQLite."""

    def __init__(
        self,
        database_path: PathLike,
        schema_path: Optional[PathLike] = None,
    ) -> None:
        module_dir = Path(__file__).resolve().parent
        schema_file = Path(schema_path) if schema_path else module_dir / "note.schema.json"
        schema = json.loads(schema_file.read_text())
        self._validator = Draft202012Validator(schema)
        self._connection = sqlite3.connect(str(database_path))
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        schema_sql = (module_dir / "schema.sql").read_text()
        self._connection.executescript(schema_sql)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "CacheRepository":
        return self

    def __exit__(self, _exception_type: Any, _exception: Any, _traceback: Any) -> None:
        self.close()

    def insert_note(self, document: Document) -> int:
        """Validate and insert a note, returning its stable note ID."""
        errors = sorted(self._validator.iter_errors(document), key=lambda error: list(error.path))
        if errors:
            location = ".".join(str(part) for part in errors[0].path) or "document"
            raise ValueError("Invalid note at {}: {}".format(location, errors[0].message))

        source = document["source"]
        source_path = source["path"]
        source_sha256 = source["sha256"].lower()
        connection = self._connection

        try:
            with connection:
                existing = connection.execute(
                    "SELECT id, source_sha256 FROM recordings WHERE source_path = ?",
                    (source_path,),
                ).fetchone()
                if existing and existing["source_sha256"] != source_sha256:
                    raise ValueError("Source path already exists with a different SHA-256 hash")

                connection.execute(
                    """
                    INSERT OR IGNORE INTO recordings
                        (source_path, source_sha256, recorded_at, duration_ms)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        source_path,
                        source_sha256,
                        source.get("recorded_at"),
                        source.get("duration_ms"),
                    ),
                )
                recording = connection.execute(
                    "SELECT id FROM recordings WHERE source_sha256 = ?",
                    (source_sha256,),
                ).fetchone()
                if recording is None:
                    raise ValueError("Source SHA-256 already belongs to another recording")

                note = connection.execute(
                    "SELECT id FROM notes WHERE recording_id = ?",
                    (recording["id"],),
                ).fetchone()
                if note:
                    return int(note["id"])

                cursor = connection.execute(
                    """
                    INSERT INTO notes(recording_id, title, summary, transcript)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        recording["id"],
                        document["title"],
                        document["summary"],
                        document["transcript"],
                    ),
                )
                note_id = int(cursor.lastrowid)

                for tag in document.get("tags", []):
                    connection.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
                    tag_row = connection.execute(
                        "SELECT id FROM tags WHERE name = ?", (tag,)
                    ).fetchone()
                    connection.execute(
                        "INSERT INTO note_tags(note_id, tag_id) VALUES (?, ?)",
                        (note_id, tag_row["id"]),
                    )

                for action in document.get("action_items", []):
                    connection.execute(
                        "INSERT INTO action_items(note_id, description, due_at) VALUES (?, ?, ?)",
                        (note_id, action["description"], action.get("due_at")),
                    )

                for contact in document.get("contacts", []):
                    connection.execute(
                        """
                        INSERT INTO contacts(note_id, name, email, phone, context)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            note_id,
                            contact["name"],
                            contact.get("email"),
                            contact.get("phone"),
                            contact.get("context"),
                        ),
                    )
                return note_id
        except sqlite3.IntegrityError as error:
            raise ValueError("Could not insert note: {}".format(error)) from error

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search note title, summary, and transcript with FTS5."""
        rows = self._connection.execute(
            """
            SELECT notes.id, notes.title, notes.summary, notes.transcript,
                   notes.created_at, bm25(notes_fts) AS rank
            FROM notes_fts
            JOIN notes ON notes.id = notes_fts.rowid
            WHERE notes_fts MATCH ?
            ORDER BY rank
            """,
            (query,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_open_actions(self) -> List[Dict[str, Any]]:
        """Return incomplete action items, with undated items last."""
        rows = self._connection.execute(
            """
            SELECT action_items.id, action_items.description, action_items.due_at,
                   action_items.note_id, notes.title
            FROM action_items
            JOIN notes ON notes.id = action_items.note_id
            WHERE action_items.completed = 0
            ORDER BY action_items.due_at IS NULL, action_items.due_at, action_items.id
            """
        ).fetchall()
        return [dict(row) for row in rows]