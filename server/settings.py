from __future__ import annotations

import json
import os
import re
from pathlib import Path


THEMES = {"mission", "cyberpunk", "lcars", "midnight"}
UI_LANGUAGES = {"auto", "de", "en", "ru", "it", "fr", "es", "pt", "pl", "nl", "tr", "ar", "zh", "tlh", "sjn"}
MOTION_PREFERENCES = {"auto", "reduce", "full"}
DEFAULT_SERVER_NAME = os.environ.get("MISSION_CONTROL_SERVER_NAME", "Mission Control").strip()
DEFAULT_LIBRARY_NAME = os.environ.get(
    "MISSION_CONTROL_LIBRARY_NAME", f"{DEFAULT_SERVER_NAME} GAME ARCHIVE"
).strip()
DEFAULT_TRANSLATOR_URL = os.environ.get(
    "MISSION_CONTROL_TRANSLATOR_URL", ""
).strip().rstrip("/")
DEFAULT_GAME_ROOT = os.environ.get("GAMEVAULT_GAME_ROOT", "/games").strip() or "/games"
DEFAULT_WINDOWS_ROOT = os.environ.get("GAMEVAULT_WINDOWS_ROOT", "Z:\\Game").strip() or "Z:\\Game"

DEFAULTS = {
    "server_name": DEFAULT_SERVER_NAME,
    "library_name": DEFAULT_LIBRARY_NAME,
    "libraries": [{
        "id": "primary",
        "name": DEFAULT_LIBRARY_NAME,
        "source_type": "server",
        "container_path": DEFAULT_GAME_ROOT,
        "windows_path": DEFAULT_WINDOWS_ROOT,
        "linux_path": "",
        "enabled": True,
    }],
    "theme": "mission",
    "background_name": None,
    "background_opacity": 0.28,
    "background_blur": 2,
    "crosshair_cursor": False,
    "scan_exclusions": [],
    "rawg_api_key": "",
    "thegamesdb_api_key": "",
    "favorite_content_language": "de",
    "ui_language": "auto",
    "motion_preference": "auto",
    "translator_url": DEFAULT_TRANSLATOR_URL,
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
        stored = {}
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                values.update(stored)
            else:
                stored = {}
        except (OSError, ValueError, TypeError):
            stored = {}
        # Upgrade older single-library installations without changing their
        # visible archive name or paths. The first library remains "primary"
        # and therefore keeps the historic game IDs and all attached metadata.
        if "libraries" not in stored:
            values["libraries"] = [{
                "id": "primary",
                "name": str(values.get("library_name") or DEFAULT_LIBRARY_NAME),
                "source_type": "server",
                "container_path": DEFAULT_GAME_ROOT,
                "windows_path": DEFAULT_WINDOWS_ROOT,
                "linux_path": "",
                "enabled": True,
            }]
        # 0.3.12+ can manage the local Translator through the Compose
        # environment. Existing installations usually have an explicitly
        # stored empty value from older releases; in that case the managed
        # address must still become active after the upgrade.
        if DEFAULT_TRANSLATOR_URL and not values.get("translator_url"):
            values["translator_url"] = DEFAULT_TRANSLATOR_URL
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

        libraries = values.get("libraries")
        if not isinstance(libraries, list) or not libraries:
            libraries = DEFAULTS["libraries"]
        validated_libraries = []
        seen_ids = set()
        for index, item in enumerate(libraries[:32]):
            if not isinstance(item, dict):
                continue
            raw_id = str(item.get("id") or ("primary" if index == 0 else "")).strip().casefold()
            library_id = re.sub(r"[^a-z0-9_-]+", "-", raw_id).strip("-")[:40]
            if not library_id or library_id in seen_ids:
                continue
            source_type = str(item.get("source_type") or "server").strip().casefold()
            if source_type not in {"server", "windows_local"}:
                continue
            container_path = str(item.get("container_path") or "").strip()
            windows_path = str(item.get("windows_path") or "").strip()
            linux_path = str(item.get("linux_path") or "").strip()
            if source_type == "server":
                if not container_path.startswith("/") or ".." in Path(container_path).parts:
                    continue
            else:
                container_path = ""
                linux_path = ""
            if windows_path and not (
                re.fullmatch(r"[A-Za-z]:\\(?:[^<>:\"|?*]+\\?)*", windows_path)
                or re.fullmatch(r"\\\\[^\\/]+\\[^\\/]+(?:\\[^<>:\"|?*]+)*\\?", windows_path)
            ):
                continue
            if linux_path and (not linux_path.startswith("/") or ".." in Path(linux_path).parts):
                continue
            if source_type == "windows_local" and not windows_path:
                continue
            if source_type == "server" and not windows_path and not linux_path:
                continue
            seen_ids.add(library_id)
            validated_libraries.append({
                "id": library_id,
                "name": str(item.get("name") or library_id).strip()[:120] or library_id,
                "source_type": source_type,
                "container_path": str(Path(container_path)) if container_path else "",
                "windows_path": windows_path.rstrip("\\") or windows_path,
                "linux_path": str(Path(linux_path)) if linux_path else "",
                "enabled": bool(item.get("enabled", True)),
            })
        if not validated_libraries:
            validated_libraries = [dict(DEFAULTS["libraries"][0])]

        return {
            "server_name": server_name or DEFAULT_SERVER_NAME,
            "library_name": library_name or DEFAULT_LIBRARY_NAME,
            "libraries": validated_libraries,
            "theme": theme,
            "background_name": background_name,
            "background_opacity": opacity,
            "background_blur": blur,
            "crosshair_cursor": bool(values.get("crosshair_cursor", False)),
            "scan_exclusions": exclusions,
            "rawg_api_key": str(values.get("rawg_api_key") or "").strip()[:200],
            "thegamesdb_api_key": str(values.get("thegamesdb_api_key") or "").strip()[:200],
            "favorite_content_language": (
                str(values.get("favorite_content_language") or values.get("content_language") or "de").strip().casefold()
                if re.fullmatch(
                    r"[a-z]{2,3}(?:-[a-z]{2})?",
                    str(values.get("favorite_content_language") or values.get("content_language") or "de").strip().casefold(),
                )
                else "de"
            ),
            "ui_language": (
                str(values.get("ui_language") or "auto").strip().casefold()
                if str(values.get("ui_language") or "auto").strip().casefold() in UI_LANGUAGES
                else "auto"
            ),
            "motion_preference": (
                str(values.get("motion_preference") or "auto").strip().casefold()
                if str(values.get("motion_preference") or "auto").strip().casefold()
                in MOTION_PREFERENCES
                else "auto"
            ),
            "translator_url": str(values.get("translator_url") or "").strip().rstrip("/")[:500],
            "translator_api_key": str(values.get("translator_api_key") or "").strip()[:300],
        }
