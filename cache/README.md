# Cache

`cache/` is the host-side Pillar 3 component. It consumes JSON emitted by
`condense/`, stores normalized records in SQLite, and exposes search and query
operations to downstream tools.

## Data flow

1. `capture/` produces a WAV file.
2. `condense/` produces one JSON document conforming to
   [`note.schema.json`](note.schema.json).
3. The cache parses the JSON, validates it, and inserts it in one SQLite
   transaction.
4. Downstream code searches `notes_fts` or queries the normalized tables.

GBNF is useful while generating JSON with `llama.cpp`, but it is not a
replacement for parsing and validation. Treat every model response as
untrusted input: parse it, validate it against the schema, then insert it.

## Database

Initialize a local database with:

```sh
sqlite3 cache.sqlite3 < schema.sql
```

The database contains:

- `recordings`: source-file identity and recording metadata.
- `notes`: one structured note per recording.
- `tags` and `note_tags`: many-to-many note labels.
- `action_items`: extracted tasks and deadlines.
- `contacts`: people and contact details mentioned in a note.
- `notes_fts`: full-text search over title, summary, and transcript.

Use `source_sha256` as the idempotency key. A daemon can safely retry a file
without creating a duplicate note. Insert the recording, note, child rows, and
FTS content in one transaction; roll back the whole note if any validation or
database operation fails.

## Suggested implementation order

### Week 1: parse and validate

Use a JSON parser (`json.loads` in Python or a standard C++ JSON library), then
validate against `note.schema.json`. Save invalid model responses to a rejected
directory with the validation error; do not partially insert them.

### Week 2: schema and indexes

Start with [`schema.sql`](schema.sql). Add indexes only after measuring real
queries. The unique source hash and FTS5 virtual table already cover the first
important correctness and search requirements.

### Week 3: repository functions

Implement three small operations around a single database connection:

- `insert_note(document) -> note_id`: validate, begin a transaction, insert
  the parent and child rows, and commit.
- `search_notes(query) -> notes`: query `notes_fts` with `bm25(notes_fts)` and
  join back to `notes`.
- `list_open_actions() -> actions`: query `action_items` where `completed = 0`,
  ordered by `due_at` with undated items last.

Keep filesystem watching, JSON validation, database access, and CLI output in
separate modules so each can be tested independently.