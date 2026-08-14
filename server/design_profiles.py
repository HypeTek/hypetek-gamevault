"""Validated, persistent appearance profiles for Mission Control."""

from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from pathlib import Path
from uuid import uuid4


COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
PROFILE_NAME_PATTERN = re.compile(r"^[\w .()\-]{1,48}$", re.UNICODE)
PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9-]{1,64}$")
STYLES = {"soft", "angular", "glass", "terminal", "pill", "frame"}
FONTS = {"system", "technical", "rounded", "mono", "compact"}
COLOR_KEYS = {"background", "panel", "panel_alt", "text", "muted", "primary", "secondary", "line"}


def _profile(name: str, style: str, font: str, colors: dict[str, str]) -> dict:
    return {
        "name": name,
        "builtin": True,
        "style": style,
        "font": font,
        "colors": colors,
        "background_name": None,
        "background_opacity": 0.28,
        "background_blur": 2,
    }


BUILTIN_PROFILES = {
    "mission": _profile("Mission", "soft", "technical", {
        "background": "#061117", "panel": "#0d1d25", "panel_alt": "#142832",
        "text": "#e8f3f4", "muted": "#8ca5aa", "primary": "#00d1c7",
        "secondary": "#f28c28", "line": "#24434c",
    }),
    "cyberpunk": _profile("Cyberpunk", "angular", "technical", {
        "background": "#090516", "panel": "#171027", "panel_alt": "#21163a",
        "text": "#f5efff", "muted": "#b7a8cf", "primary": "#00f6ff",
        "secondary": "#ff3cac", "line": "#52356f",
    }),
    "lcars": _profile("LCARS", "pill", "rounded", {
        "background": "#090b18", "panel": "#15172b", "panel_alt": "#25223b",
        "text": "#fff7e8", "muted": "#c8b9d9", "primary": "#cc99ff",
        "secondary": "#ff9f5a", "line": "#6b4f92",
    }),
    "midnight": _profile("Midnight", "glass", "system", {
        "background": "#05070c", "panel": "#0c111b", "panel_alt": "#141d2b",
        "text": "#e7edf7", "muted": "#8794a8", "primary": "#70a5ff",
        "secondary": "#a78bfa", "line": "#26374e",
    }),
}


class DesignProfileStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self, legacy_theme: str = "mission") -> dict:
        stored = {}
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            pass
        profiles = deepcopy(BUILTIN_PROFILES)
        raw_profiles = stored.get("profiles", {}) if isinstance(stored, dict) else {}
        if isinstance(raw_profiles, dict):
            for profile_id, profile in raw_profiles.items():
                if PROFILE_ID_PATTERN.fullmatch(str(profile_id)) and isinstance(profile, dict):
                    profiles[profile_id] = self.normalize(profile, builtin=False)
        requested = stored.get("active") if isinstance(stored, dict) else None
        active = requested if requested in profiles else legacy_theme if legacy_theme in profiles else "mission"
        return {"active": active, "profiles": profiles}

    def list_public(self, legacy_theme: str = "mission") -> dict:
        return self.load(legacy_theme)

    def create(self, profile: dict, legacy_theme: str = "mission") -> dict:
        store = self.load(legacy_theme)
        normalized = self.normalize(profile, builtin=False)
        if any(item["name"].casefold() == normalized["name"].casefold() for item in store["profiles"].values()):
            raise ValueError("Ein Designprofil mit diesem Namen existiert bereits.")
        profile_id = self._new_id(normalized["name"], store["profiles"])
        store["profiles"][profile_id] = normalized
        self.save(store)
        return {"id": profile_id, **normalized}

    def update(self, profile_id: str, profile: dict, legacy_theme: str = "mission") -> dict:
        store = self.load(legacy_theme)
        if profile_id not in store["profiles"]:
            raise KeyError("Unbekanntes Designprofil.")
        if store["profiles"][profile_id].get("builtin"):
            raise ValueError("Integrierte Profile können dupliziert, aber nicht verändert werden.")
        normalized = self.normalize(profile, builtin=False)
        if any(key != profile_id and item["name"].casefold() == normalized["name"].casefold() for key, item in store["profiles"].items()):
            raise ValueError("Ein Designprofil mit diesem Namen existiert bereits.")
        store["profiles"][profile_id] = normalized
        self.save(store)
        return {"id": profile_id, **normalized}

    def activate(self, profile_id: str, legacy_theme: str = "mission") -> dict:
        store = self.load(legacy_theme)
        if profile_id not in store["profiles"]:
            raise KeyError("Unbekanntes Designprofil.")
        store["active"] = profile_id
        self.save(store)
        return store

    def delete(self, profile_id: str, legacy_theme: str = "mission") -> dict:
        store = self.load(legacy_theme)
        profile = store["profiles"].get(profile_id)
        if not profile:
            raise KeyError("Unbekanntes Designprofil.")
        if profile.get("builtin"):
            raise ValueError("Integrierte Profile können nicht gelöscht werden.")
        del store["profiles"][profile_id]
        if store["active"] == profile_id:
            store["active"] = "mission"
        self.save(store)
        return store

    @staticmethod
    def normalize(profile: dict, builtin: bool = False) -> dict:
        name = str(profile.get("name") or "").strip()
        if not PROFILE_NAME_PATTERN.fullmatch(name):
            raise ValueError("Der Profilname darf maximal 48 normale Zeichen enthalten.")
        style = str(profile.get("style") or "soft")
        font = str(profile.get("font") or "system")
        if style not in STYLES:
            raise ValueError("Unbekannter Oberflächenstil.")
        if font not in FONTS:
            raise ValueError("Unbekannte Schriftart-Gruppe.")
        source_colors = profile.get("colors") if isinstance(profile.get("colors"), dict) else {}
        fallback = BUILTIN_PROFILES["mission"]["colors"]
        colors = {}
        for key in COLOR_KEYS:
            value = str(source_colors.get(key) or fallback[key])
            if not COLOR_PATTERN.fullmatch(value):
                raise ValueError(f"Ungültiger Farbwert für {key}.")
            colors[key] = value.lower()
        try:
            opacity = min(0.85, max(0.0, float(profile.get("background_opacity", 0.28))))
            blur = min(20, max(0, int(profile.get("background_blur", 2))))
        except (TypeError, ValueError) as error:
            raise ValueError("Ungültiger Hintergrundeffekt.") from error
        background_name = profile.get("background_name")
        if background_name is not None:
            background_name = Path(str(background_name)).name
            if not re.fullmatch(r"(?:background-[a-f0-9]{24}|custom-background)\.(?:jpg|jpeg|png|webp)", background_name):
                raise ValueError("Ungültige Hintergrundreferenz.")
        return {"name": name, "builtin": builtin, "style": style, "font": font, "colors": colors, "background_name": background_name, "background_opacity": opacity, "background_blur": blur}

    def save(self, store: dict) -> None:
        custom = {key: value for key, value in store["profiles"].items() if not value.get("builtin")}
        rendered = json.dumps({"active": store["active"], "profiles": custom}, ensure_ascii=False, indent=2) + "\n"
        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp", delete=False) as temporary:
                temporary_name = temporary.name
                temporary.write(rendered)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, self.path)
        finally:
            if temporary_name and Path(temporary_name).exists():
                Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _new_id(name: str, profiles: dict) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")[:40] or "profil"
        candidate = base
        while candidate in profiles:
            candidate = f"{base[:32]}-{uuid4().hex[:7]}"
        return candidate
