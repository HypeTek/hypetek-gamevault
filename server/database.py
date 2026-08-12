from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from scanner import ScanResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    relative_path TEXT NOT NULL UNIQUE,
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

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def apply_scan(self, results: list[ScanResult]) -> None:
        now = int(time.time())
        with self.connect() as connection:
            connection.execute("UPDATE games SET present = 0")
            for result in results:
                connection.execute(
                    """
                    INSERT INTO games (
                        id, relative_path, detected_title, detected_type,
                        detected_launcher, detection_note, file_count,
                        logical_size, present, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        relative_path=excluded.relative_path,
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

    def list_games(self, include_hidden: bool = False) -> list[dict]:
        where = "present = 1" if include_hidden else "present = 1 AND hidden = 0"
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM games WHERE {where} ORDER BY COALESCE(custom_title, detected_title) COLLATE NOCASE"
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

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> dict:
        game = dict(row)
        game["title"] = game["custom_title"] or game["detected_title"]
        game["action"] = game["action_override"] or game["detected_type"]
        game["launcher"] = game["launcher_override"] or game["detected_launcher"]
        return game
