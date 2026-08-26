from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from scanner import ScanResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    library_id TEXT NOT NULL DEFAULT 'primary',
    relative_path TEXT NOT NULL,
    detected_title TEXT NOT NULL,
    custom_title TEXT,
    detected_type TEXT NOT NULL,
    action_override TEXT,
    detected_launcher TEXT,
    launcher_override TEXT,
    detection_note TEXT NOT NULL,
    file_count INTEGER NOT NULL DEFAULT 0,
    logical_size INTEGER NOT NULL DEFAULT 0,
    platform TEXT NOT NULL DEFAULT 'Windows',
    description TEXT NOT NULL DEFAULT '',
    cover_name TEXT,
    cover_position_y INTEGER NOT NULL DEFAULT 50,
    metadata_provider TEXT,
    metadata_provider_id TEXT,
    metadata_source_url TEXT,
    metadata_title TEXT,
    metadata_overview TEXT,
    metadata_overview_original TEXT,
    metadata_overview_language TEXT,
    metadata_release_date TEXT,
    metadata_platform TEXT,
    metadata_rating TEXT,
    metadata_players TEXT,
    metadata_coop TEXT,
    favorite INTEGER NOT NULL DEFAULT 0,
    hidden INTEGER NOT NULL DEFAULT 0,
    present INTEGER NOT NULL DEFAULT 1,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS launch_tickets (
    token TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    requested_action TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    used_at INTEGER,
    FOREIGN KEY(game_id) REFERENCES games(id)
);
CREATE TABLE IF NOT EXISTS agent_probes (
    token TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL,
    confirmed_at INTEGER
);
CREATE TABLE IF NOT EXISTS folder_pickers (
    token TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL,
    selected_path TEXT,
    confirmed_at INTEGER
);
CREATE TABLE IF NOT EXISTS agent_scans (
    token TEXT PRIMARY KEY,
    library_id TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    started_at INTEGER,
    completed_at INTEGER,
    result_count INTEGER,
    error TEXT
);
"""

LAUNCH_TICKETS_SCHEMA = """
CREATE TABLE IF NOT EXISTS launch_tickets (
    token TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    requested_action TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    used_at INTEGER,
    FOREIGN KEY(game_id) REFERENCES games(id)
);
"""


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(launch_tickets)").fetchall()
            }
            if "requested_action" not in columns:
                connection.execute(
                    "ALTER TABLE launch_tickets ADD COLUMN requested_action TEXT NOT NULL DEFAULT 'open_folder'"
                )
            game_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(games)").fetchall()
            }
            if "library_id" not in game_columns:
                connection.execute(
                    "ALTER TABLE games ADD COLUMN library_id TEXT NOT NULL DEFAULT 'primary'"
                )
                # Older databases have an automatic UNIQUE index on
                # relative_path. It is harmless for the migrated primary
                # library but would block equal paths in later libraries, so
                # rebuild the table once using the current schema.
                self._rebuild_games_for_libraries(connection)
                game_columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(games)").fetchall()
                }
            if "cover_position_y" not in game_columns:
                connection.execute(
                    "ALTER TABLE games ADD COLUMN cover_position_y INTEGER NOT NULL DEFAULT 50"
                )
            if "favorite" not in game_columns:
                connection.execute(
                    "ALTER TABLE games ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0"
                )
            agent_scan_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(agent_scans)").fetchall()
            }
            if "started_at" not in agent_scan_columns:
                connection.execute("ALTER TABLE agent_scans ADD COLUMN started_at INTEGER")
            for name in (
                "metadata_provider",
                "metadata_provider_id",
                "metadata_source_url",
                "metadata_title",
                "metadata_overview",
                "metadata_overview_original",
                "metadata_overview_language",
                "metadata_release_date",
                "metadata_platform",
                "metadata_rating",
                "metadata_players",
                "metadata_coop",
            ):
                if name not in game_columns:
                    connection.execute(f"ALTER TABLE games ADD COLUMN {name} TEXT")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS games_library_path "
                "ON games(library_id, relative_path)"
            )

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _rebuild_games_for_libraries(connection: sqlite3.Connection) -> None:
        columns = [row["name"] for row in connection.execute("PRAGMA table_info(games)")]
        # Tickets live for only two minutes and can safely be discarded during
        # this one-time migration. Dropping them avoids SQLite rewriting their
        # foreign key to the temporary legacy table name.
        connection.execute("DROP TABLE IF EXISTS launch_tickets")
        connection.execute("ALTER TABLE games RENAME TO games_legacy_library_migration")
        schema = SCHEMA.split("CREATE TABLE IF NOT EXISTS launch_tickets", 1)[0]
        connection.executescript(schema)
        target_columns = [row["name"] for row in connection.execute("PRAGMA table_info(games)")]
        shared = [name for name in target_columns if name in columns]
        names = ", ".join(shared)
        connection.execute(
            f"INSERT INTO games ({names}) SELECT {names} FROM games_legacy_library_migration"
        )
        connection.execute("DROP TABLE games_legacy_library_migration")
        connection.executescript(LAUNCH_TICKETS_SCHEMA)

    def apply_scan(self, results: list[ScanResult], library_id: str = "primary") -> None:
        now = int(time.time())
        with self.connect() as connection:
            connection.execute("UPDATE games SET present = 0 WHERE library_id = ?", (library_id,))
            for result in results:
                connection.execute(
                    """
                    INSERT INTO games (
                        id, library_id, relative_path, detected_title, detected_type,
                        detected_launcher, detection_note, file_count,
                        logical_size, present, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        library_id=excluded.library_id,
                        relative_path=excluded.relative_path,
                        custom_title=CASE
                            WHEN games.custom_title = games.detected_title THEN NULL
                            ELSE games.custom_title
                        END,
                        detected_title=excluded.detected_title,
                        detected_type=excluded.detected_type,
                        detected_launcher=excluded.detected_launcher,
                        detection_note=excluded.detection_note,
                        file_count=excluded.file_count,
                        logical_size=excluded.logical_size,
                        present=1,
                        updated_at=excluded.updated_at
                    """,
                    (
                        result.game_id,
                        library_id,
                        result.relative_path,
                        result.title,
                        result.detected_type,
                        result.launcher_relative_path,
                        result.detection_note,
                        result.file_count,
                        result.logical_size,
                        now,
                    ),
                )

    def list_games(self, include_hidden: bool = False, library_id: str | None = None) -> list[dict]:
        where = "present = 1" if include_hidden else "present = 1 AND hidden = 0"
        parameters: tuple = ()
        if library_id:
            where += " AND library_id = ?"
            parameters = (library_id,)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM games WHERE {where} ORDER BY COALESCE(custom_title, detected_title) COLLATE NOCASE",
                parameters,
            ).fetchall()
        return [self._row_to_game(row) for row in rows]

    def get_game(self, game_id: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        return self._row_to_game(row) if row else None

    def update_game(self, game_id: str, values: dict) -> None:
        allowed = {
            "custom_title",
            "action_override",
            "launcher_override",
            "platform",
            "description",
            "cover_name",
            "cover_position_y",
            "metadata_provider",
            "metadata_provider_id",
            "metadata_source_url",
            "metadata_title",
            "metadata_overview",
            "metadata_overview_original",
            "metadata_overview_language",
            "metadata_release_date",
            "metadata_platform",
            "metadata_rating",
            "metadata_players",
            "metadata_coop",
            "favorite",
            "hidden",
        }
        updates = {key: value for key, value in values.items() if key in allowed}
        if not updates:
            return
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE games SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), int(time.time()), game_id),
            )

    def create_ticket(
        self, token: str, game_id: str, requested_action: str, expires_at: int
    ) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM launch_tickets WHERE expires_at < ?", (int(time.time()),))
            connection.execute(
                """
                INSERT INTO launch_tickets(token, game_id, requested_action, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, game_id, requested_action, expires_at),
            )

    def consume_ticket(self, token: str) -> dict | None:
        now = int(time.time())
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT games.*, launch_tickets.requested_action FROM launch_tickets
                JOIN games ON games.id = launch_tickets.game_id
                WHERE launch_tickets.token = ?
                  AND launch_tickets.expires_at >= ?
                  AND launch_tickets.used_at IS NULL
                """,
                (token, now),
            ).fetchone()
            if not row:
                return None
            connection.execute(
                "UPDATE launch_tickets SET used_at = ? WHERE token = ?",
                (now, token),
            )
        game = self._row_to_game(row)
        game["requested_action"] = row["requested_action"]
        return game

    def create_agent_probe(self, token: str, expires_at: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM agent_probes WHERE expires_at < ?", (int(time.time()),))
            connection.execute(
                "INSERT INTO agent_probes(token, expires_at) VALUES (?, ?)",
                (token, expires_at),
            )

    def confirm_agent_probe(self, token: str) -> bool:
        now = int(time.time())
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE agent_probes SET confirmed_at = ?
                WHERE token = ? AND expires_at >= ? AND confirmed_at IS NULL
                """,
                (now, token, now),
            )
        return result.rowcount == 1

    def get_agent_probe(self, token: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT expires_at, confirmed_at FROM agent_probes WHERE token = ?",
                (token,),
            ).fetchone()
        return dict(row) if row else None

    def create_folder_picker(self, token: str, expires_at: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM folder_pickers WHERE expires_at < ?", (int(time.time()),))
            connection.execute(
                "INSERT INTO folder_pickers(token, expires_at) VALUES (?, ?)",
                (token, expires_at),
            )

    def complete_folder_picker(self, token: str, selected_path: str) -> bool:
        now = int(time.time())
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE folder_pickers SET selected_path = ?, confirmed_at = ?
                WHERE token = ? AND expires_at >= ? AND confirmed_at IS NULL
                """,
                (selected_path, now, token, now),
            )
        return result.rowcount == 1

    def get_folder_picker(self, token: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT expires_at, selected_path, confirmed_at FROM folder_pickers WHERE token = ?",
                (token,),
            ).fetchone()
        return dict(row) if row else None

    def create_agent_scan(self, token: str, library_id: str, expires_at: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM agent_scans WHERE expires_at < ?", (int(time.time()),))
            connection.execute(
                "INSERT INTO agent_scans(token, library_id, expires_at) VALUES (?, ?, ?)",
                (token, library_id, expires_at),
            )

    def get_agent_scan(self, token: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT token, library_id, expires_at, started_at, completed_at, result_count, error "
                "FROM agent_scans WHERE token = ?",
                (token,),
            ).fetchone()
        return dict(row) if row else None

    def start_agent_scan(self, token: str) -> bool:
        now = int(time.time())
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE agent_scans SET started_at = COALESCE(started_at, ?)
                WHERE token = ? AND expires_at >= ? AND completed_at IS NULL
                """,
                (now, token, now),
            )
        return result.rowcount == 1

    def complete_agent_scan(self, token: str, result_count: int, error: str | None = None) -> bool:
        now = int(time.time())
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE agent_scans SET completed_at = ?, result_count = ?, error = ?
                WHERE token = ? AND expires_at >= ? AND completed_at IS NULL
                """,
                (now, result_count, error, token, now),
            )
        return result.rowcount == 1

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> dict:
        game = dict(row)
        game["title"] = game["custom_title"] or game["detected_title"]
        game["action"] = game["action_override"] or game["detected_type"]
        game["launcher"] = game["launcher_override"] or game["detected_launcher"]
        game["favorite"] = bool(game.get("favorite", 0))
        return game
