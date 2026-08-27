import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "server"))
from database import Database
from scanner import ScanResult


def result(game_id: str, path: str) -> ScanResult:
    return ScanResult(game_id, path, path, "manual", None, "test", 1, 1)


class DatabaseLibraryTests(unittest.TestCase):
    def test_scans_only_mark_selected_library_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Database(Path(temp) / "games.sqlite3")
            database.apply_scan([result("primary-id", "Same")], "primary")
            database.apply_scan([result("archive-id", "Same")], "archive")
            database.apply_scan([], "archive")
            self.assertEqual([item["id"] for item in database.list_games()], ["primary-id"])

    def test_legacy_unique_path_database_is_migrated(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.sqlite3"
            with sqlite3.connect(path) as connection:
                connection.executescript("""
                    CREATE TABLE games (
                      id TEXT PRIMARY KEY, relative_path TEXT UNIQUE NOT NULL,
                      detected_title TEXT NOT NULL, detected_type TEXT NOT NULL,
                      detection_note TEXT NOT NULL, file_count INTEGER NOT NULL DEFAULT 0,
                      logical_size INTEGER NOT NULL DEFAULT 0, platform TEXT NOT NULL DEFAULT 'Windows',
                      description TEXT NOT NULL DEFAULT '', hidden INTEGER NOT NULL DEFAULT 0,
                      present INTEGER NOT NULL DEFAULT 1, updated_at INTEGER NOT NULL
                    );
                """)
            database = Database(path)
            database.apply_scan([result("one", "Same")], "primary")
            database.apply_scan([result("two", "Same")], "archive")
            self.assertEqual(len(database.list_games()), 2)

    def test_removing_library_deletes_its_indexed_games(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Database(Path(temp) / "games.sqlite3")
            database.apply_scan([result("primary-id", "Primary")], "primary")
            database.apply_scan([result("removed-id", "Removed")], "library-3")
            database.remove_library("library-3")
            self.assertEqual([item["id"] for item in database.list_games()], ["primary-id"])

    def test_rescan_cleanup_removes_preexisting_orphan_library(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Database(Path(temp) / "games.sqlite3")
            database.apply_scan([result("primary-id", "Primary")], "primary")
            database.apply_scan([result("orphan-id", "SKATSTOR")], "library-3")
            removed = database.remove_unconfigured_libraries({"primary"})
            self.assertEqual(removed, ["library-3"])
            self.assertEqual([item["id"] for item in database.list_games()], ["primary-id"])


if __name__ == "__main__":
    unittest.main()
