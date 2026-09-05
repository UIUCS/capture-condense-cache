import tempfile
import unittest
from pathlib import Path

from cache.repository import CacheRepository


class CacheRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "cache.sqlite3"
        self.repository = CacheRepository(database_path)

    def tearDown(self) -> None:
        self.repository.close()
        self.temp_directory.cleanup()

    def test_insert_search_and_actions(self) -> None:
        document = {
            "schema_version": 1,
            "source": {
                "path": "lecture.wav",
                "sha256": "a" * 64,
                "recorded_at": "2026-09-04T10:00:00Z",
                "duration_ms": 120000,
            },
            "title": "Operating systems",
            "summary": "Review paging before Friday",
            "transcript": "The exam covers paging and virtual memory.",
            "tags": ["lecture"],
            "action_items": [{"description": "Review paging", "due_at": "2026-09-11"}],
            "contacts": [{"name": "Ada", "email": "ada@example.com"}],
        }

        note_id = self.repository.insert_note(document)
        results = self.repository.search_notes("paging")
        actions = self.repository.list_open_actions()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], note_id)
        self.assertEqual(actions[0]["description"], "Review paging")

    def test_duplicate_source_is_idempotent(self) -> None:
        document = {
            "schema_version": 1,
            "source": {"path": "same.wav", "sha256": "b" * 64},
            "title": "A note",
            "summary": "A summary",
            "transcript": "Some text",
        }

        first_id = self.repository.insert_note(document)
        second_id = self.repository.insert_note(document)

        self.assertEqual(first_id, second_id)
        self.assertEqual(len(self.repository.search_notes("text")), 1)

    def test_invalid_document_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.insert_note({"title": "Missing required fields"})


if __name__ == "__main__":
    unittest.main()