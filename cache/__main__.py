import argparse
import json
import sys
from typing import Any, Dict, List

from .repository import CacheRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query the local knowledge cache")
    parser.add_argument(
        "--database", default="cache.sqlite3", help="SQLite database path"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search notes with FTS5 MATCH")
    search.add_argument("query", help='FTS5 query, for example: exam AND "machine learning"')
    search.add_argument("--limit", type=int, default=20, help="Maximum results to print")
    search.add_argument("--json", action="store_true", help="Output JSON")

    actions = subparsers.add_parser("actions", help="List incomplete action items")
    actions.add_argument("--json", action="store_true", help="Output JSON")

    note = subparsers.add_parser("note", help="Show one complete note")
    note.add_argument("note_id", type=int)
    note.add_argument("--json", action="store_true", help="Output JSON")
    return parser


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True))


def print_search_results(results: List[Dict[str, Any]]) -> None:
    if not results:
        print("No matching notes.")
        return
    for result in results:
        print("[{}] {} (rank: {:.4f})".format(result["id"], result["title"], result["rank"]))
        print("  {}".format(result["summary"]))
        print("  {}".format(result["transcript"]))


def print_actions(actions: List[Dict[str, Any]]) -> None:
    if not actions:
        print("No open action items.")
        return
    for action in actions:
        due = action["due_at"] or "no due date"
        print("[{}] {} ({}) - {}".format(action["id"], action["title"], due, action["description"]))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        with CacheRepository(args.database) as repository:
            if args.command == "search":
                results = repository.search_notes(args.query)[: max(args.limit, 0)]
                if args.json:
                    print_json(results)
                else:
                    print_search_results(results)
            elif args.command == "actions":
                actions = repository.list_open_actions()
                if args.json:
                    print_json(actions)
                else:
                    print_actions(actions)
            else:
                note = repository.get_note(args.note_id)
                if note is None:
                    print("Note {} was not found.".format(args.note_id), file=sys.stderr)
                    return 1
                if args.json:
                    print_json(note)
                else:
                    print("[{}] {}".format(note["id"], note["title"]))
                    print(note["summary"])
                    print("\n{}".format(note["transcript"]))
                    if note["tags"]:
                        print("\nTags: {}".format(", ".join(note["tags"])))
                    if note["action_items"]:
                        print("\nAction items:")
                        for action in note["action_items"]:
                            print("- {}".format(action["description"]))
    except (OSError, ValueError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())