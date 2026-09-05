PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE IF NOT EXISTS recordings (
    id INTEGER PRIMARY KEY,
    source_path TEXT NOT NULL UNIQUE,
    source_sha256 TEXT NOT NULL UNIQUE,
    recorded_at TEXT,
    duration_ms INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER NOT NULL UNIQUE REFERENCES recordings(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    transcript TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    due_at TEXT,
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1))
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    context TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title,
    summary,
    transcript,
    content='notes',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS notes_fts_insert AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, summary, transcript)
    VALUES (new.id, new.title, new.summary, new.transcript);
END;

CREATE TRIGGER IF NOT EXISTS notes_fts_delete AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, summary, transcript)
    VALUES ('delete', old.id, old.title, old.summary, old.transcript);
END;

CREATE TRIGGER IF NOT EXISTS notes_fts_update AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, summary, transcript)
    VALUES ('delete', old.id, old.title, old.summary, old.transcript);
    INSERT INTO notes_fts(rowid, title, summary, transcript)
    VALUES (new.id, new.title, new.summary, new.transcript);
END;

COMMIT;