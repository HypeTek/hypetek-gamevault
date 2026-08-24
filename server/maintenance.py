from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path


FORMAT = "hypetek-mission-control-backup"
SAFE_FILES = {
    "mission-control-settings.json",
    "mission-control-designs.json",
    "gamevault.sqlite3",
}
SECRET_KEYS = {"thegamesdb_api_key", "translator_api_key", "rawg_api_key"}


def _install_file(source: Path, target: Path) -> None:
    """Install a restored file atomically on the target filesystem.

    Restore archives are extracted below /tmp while TrueNAS normally mounts
    /config from a dataset. os.replace() cannot cross that filesystem boundary
    (EXDEV), so first copy into a sibling temporary file and only then replace
    the live file.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-restore-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _install_directory(source: Path, target: Path) -> None:
    """Replace a restored directory using staging on the target filesystem."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}-restore-{uuid.uuid4().hex}"
    previous = target.parent / f".{target.name}-previous-{uuid.uuid4().hex}"
    shutil.copytree(source, temporary)
    had_previous = target.exists()
    try:
        if had_previous:
            os.replace(target, previous)
        os.replace(temporary, target)
    except Exception:
        if had_previous and previous.exists() and not target.exists():
            os.replace(previous, target)
        raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
        shutil.rmtree(previous, ignore_errors=True)


def _safe_settings(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    for key in SECRET_KEYS:
        data.pop(key, None)
    return data


def create_backup(config_dir: Path, version: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mission-control-backup-") as temporary:
        stage = Path(temporary)
        database = config_dir / "gamevault.sqlite3"
        if database.exists():
            source = sqlite3.connect(database)
            target = sqlite3.connect(stage / "gamevault.sqlite3")
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
        (stage / "mission-control-settings.json").write_text(
            json.dumps(_safe_settings(config_dir / "mission-control-settings.json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        designs = config_dir / "mission-control-designs.json"
        if designs.exists():
            shutil.copy2(designs, stage / designs.name)
        manifest = {
            "format": FORMAT,
            "format_version": 1,
            "application_version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "secrets_included": False,
            "note": "API keys and authentication secrets are intentionally excluded.",
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in sorted(stage.iterdir()):
                archive.write(item, item.name)
            for folder in ("covers", "backgrounds"):
                root = config_dir / folder
                if root.is_dir():
                    for item in root.rglob("*"):
                        if item.is_file() and not item.is_symlink():
                            archive.write(item, item.relative_to(config_dir).as_posix())
    return destination


def validate_backup(archive_path: Path) -> dict:
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) > 5000:
            raise ValueError("Sicherung enthält zu viele Dateien.")
        if sum(entry.file_size for entry in entries) > 1024 * 1024 * 1024:
            raise ValueError("Sicherung ist entpackt zu groß.")
        for name in names:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Sicherung enthält einen unsicheren Pfad.")
            if name not in SAFE_FILES | {"manifest.json"} and not name.startswith(("covers/", "backgrounds/")):
                raise ValueError(f"Unbekannter Eintrag in der Sicherung: {name}")
        try:
            manifest = json.loads(archive.read("manifest.json"))
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError("Ungültiges Sicherungsmanifest.") from error
        if manifest.get("format") != FORMAT or manifest.get("format_version") != 1:
            raise ValueError("Nicht unterstütztes Sicherungsformat.")
    return manifest


def restore_backup(archive_path: Path, config_dir: Path) -> None:
    validate_backup(archive_path)
    config_dir.mkdir(parents=True, exist_ok=True)
    preserved = _safe_settings(config_dir / "mission-control-settings.json")
    try:
        existing = json.loads((config_dir / "mission-control-settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        existing = {}
    with tempfile.TemporaryDirectory(prefix="mission-control-restore-") as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(stage)
        database = stage / "gamevault.sqlite3"
        if database.exists():
            connection = sqlite3.connect(database)
            try:
                if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Die Datenbank der Sicherung ist beschädigt.")
                connection.execute("SELECT 1 FROM games LIMIT 1")
            finally:
                connection.close()
        settings_file = stage / "mission-control-settings.json"
        restored = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else preserved
        if not isinstance(restored, dict):
            raise ValueError("Ungültige Einstellungen in der Sicherung.")
        for key in SECRET_KEYS:
            if isinstance(existing, dict) and existing.get(key):
                restored[key] = existing[key]
        settings_file.write_text(json.dumps(restored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name in SAFE_FILES:
            source = stage / name
            if source.exists():
                _install_file(source, config_dir / name)
        for folder in ("covers", "backgrounds"):
            source = stage / folder
            if source.exists():
                _install_directory(source, config_dir / folder)


def rotate_backups(directory: Path, keep: int = 5) -> None:
    backups = sorted(directory.glob("mission-control-auto-*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old.unlink(missing_ok=True)
