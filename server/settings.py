from __future__ import annotations

import json
import os
import re
from pathlib import Path


THEMES = {"mission", "cyberpunk", "lcars", "midnight"}
CONTENT_LANGUAGES = {"de", "en", "fr", "es", "it", "pt", "pl", "ru", "uk", "tr", "ar", "zh", "ja", "ko"}
DEFAULT_SERVER_NAME = os.environ.get("MISSION_CONTROL_SERVER_NAME", "Mission Control").strip()
DEFAULT_LIBRARY_NAME = os.environ.get(
    "MISSION_CONTROL_LIBRARY_NAME", f"{DEFAULT_SERVER_NAME} GAME ARCHIVE"
).strip()

DEFAULTS = {
    "server_name": DEFAULT_SERVER_NAME,
    "library_name": DEFAULT_LIBRARY_NAME,
    "theme": "mission",
    "background_name": None,
    "background_opacity": 0.28,
    "background_blur": 2,
    "crosshair_cursor": False,
    "scan_exclusions": [],
    "rawg_api_key": "",
    "thegamesdb_api_key": "",
    "content_language": "de",
    "translator_url": "",
    "translator_api_key": "",
}


class SettingsStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULTS)

    def load(self) -> dict:
        values = DEFAULTS.copy()
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                values.update(stored)
        except (OSError, ValueError, TypeError):
            pass
        return self.validate(values)

    def update(self, changes: dict) -> dict:
        values = self.load()
        values.update(changes)
        values = self.validate(values)
        self.save(values)
        return values

    def save(self, values: dict) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.chmod(0o600)
        temporary.replace(self.path)

    @staticmethod
    def validate(values: dict) -> dict:
        server_name = str(values.get("server_name") or DEFAULT_SERVER_NAME).strip()[:80]
        library_name = str(values.get("library_name") or DEFAULT_LIBRARY_NAME).strip()[:120]
        theme = str(values.get("theme") or "mission")
        if theme not in THEMES:
            theme = "mission"

        try:
            opacity = float(values.get("background_opacity", 0.28))
        except (TypeError, ValueError):
            opacity = 0.28
        opacity = min(0.85, max(0.0, opacity))

        try:
            blur = int(values.get("background_blur", 2))
        except (TypeError, ValueError):
            blur = 2
        blur = min(20, max(0, blur))

        exclusions = values.get("scan_exclusions", [])
        if isinstance(exclusions, str):
            exclusions = re.split(r"[,\n]", exclusions)
        if not isinstance(exclusions, list):
            exclusions = []
        exclusions = sorted(
            {
                str(item).strip().casefold()
                for item in exclusions
                if str(item).strip() and "/" not in str(item) and "\\" not in str(item)
            }
        )[:100]

        background_name = values.get("background_name")
        if background_name is not None:
            background_name = Path(str(background_name)).name

        return {
            "server_name": server_name or DEFAULT_SERVER_NAME,
            "library_name": library_name or DEFAULT_LIBRARY_NAME,
            "theme": theme,
            "background_name": background_name,
            "background_opacity": opacity,
            "background_blur": blur,
            "crosshair_cursor": bool(values.get("crosshair_cursor", False)),
            "scan_exclusions": exclusions,
            "rawg_api_key": str(values.get("rawg_api_key") or "").strip()[:200],
            "thegamesdb_api_key": str(values.get("thegamesdb_api_key") or "").strip()[:200],
            "content_language": (
                str(values.get("content_language") or "de").strip().casefold()
                if str(values.get("content_language") or "de").strip().casefold() in CONTENT_LANGUAGES
                else "de"
            ),
            "translator_url": str(values.get("translator_url") or "").strip().rstrip("/")[:500],
            "translator_api_key": str(values.get("translator_api_key") or "").strip()[:300],
        }
