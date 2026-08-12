from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path


INSTALLER_PATTERNS = (
    re.compile(r"^setup(?:[-_. ].*)?\.exe$", re.I),
    re.compile(r"^install(?:er)?(?:[-_. ].*)?\.exe$", re.I),
    re.compile(r"^autorun\.exe$", re.I),
)

EXCLUDED_DIRS = {
    "_commonredist",
    "redist",
    "redistributable",
    "directx",
    "vcredist",
    "support",
    "prerequisites",
    "prereqs",
    "python",
    "dotnet",
    "physx",
    "md5",
}

ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar"}
NATIVE_IMAGE_EXTENSIONS = {".iso"}
MANUAL_IMAGE_EXTENSIONS = {".cue", ".bin", ".img", ".mdf", ".mds"}


@dataclass(frozen=True)
class ScanResult:
    game_id: str
    relative_path: str
    title: str
    detected_type: str
    launcher_relative_path: str | None
    file_count: int
    logical_size: int
    detection_note: str


def stable_id(relative_path: str) -> str:
    return hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:20]


def clean_title(name: str) -> str:
    title = Path(name).stem if Path(name).suffix.lower() in (
        NATIVE_IMAGE_EXTENSIONS | ARCHIVE_EXTENSIONS
    ) else name
    title = re.sub(r"\s*\[(?:fitgirl(?: repack)?|repack)\]\s*", " ", title, flags=re.I)
    title = re.sub(r"\s*--[_ ]*fitgirl-repacks(?:\.site)?[_ ]*--\s*", " ", title, flags=re.I)
    title = re.sub(r"[._]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip(" -_")
    return title or name


def _is_excluded(file: Path, entry: Path) -> bool:
    try:
        parent_parts = file.relative_to(entry).parts[:-1]
    except ValueError:
        return False
    return any(part.casefold() in EXCLUDED_DIRS for part in parent_parts)


def _installer_score(file: Path, entry: Path) -> int:
    if _is_excluded(file, entry):
        return -1
    try:
        depth = len(file.relative_to(entry).parts) - 1
    except ValueError:
        depth = 0
    if any(pattern.match(file.name) for pattern in INSTALLER_PATTERNS):
        return 100 - min(depth, 12) * 4
    if depth == 0 and file.suffix.casefold() == ".exe" and "setup" in file.name.casefold():
        return 85
    return -1


def _collect_files(entry: Path) -> list[Path]:
    if entry.is_file():
        return [entry]
    files: list[Path] = []
    for base, dirs, names in os.walk(entry, followlinks=False):
        dirs[:] = [d for d in dirs if d.casefold() not in EXCLUDED_DIRS]
        files.extend(Path(base) / name for name in names)
    return files


def scan_entry(root: Path, entry: Path) -> ScanResult:
    files = _collect_files(entry)
    file_count = len(files)
    logical_size = 0
    for file in files:
        try:
            logical_size += file.stat().st_size
        except OSError:
            pass

    scored_installers = sorted(
        (
            (_installer_score(file, entry), file)
            for file in files
            if file.suffix.casefold() == ".exe"
        ),
        key=lambda item: (-item[0], len(str(item[1]))),
    )
    scored_installers = [item for item in scored_installers if item[0] >= 0]
    iso_files = [file for file in files if file.suffix.casefold() in NATIVE_IMAGE_EXTENSIONS]
    archives = [file for file in files if file.suffix.casefold() in ARCHIVE_EXTENSIONS]
    manual_images = [file for file in files if file.suffix.casefold() in MANUAL_IMAGE_EXTENSIONS]

    launcher: Path | None = None
    if entry.is_file() and entry.suffix.casefold() == ".iso":
        detected_type = "iso"
        launcher = entry
        note = "Einzelnes Windows-nativ mountbares ISO-Abbild"
    elif scored_installers:
        detected_type = "direct_setup"
        launcher = scored_installers[0][1]
        note = "Setup-Programm automatisch erkannt"
    elif iso_files:
        detected_type = "iso"
        launcher = iso_files[0]
        note = "Windows-nativ mountbares ISO-Abbild erkannt"
    elif manual_images:
        detected_type = "manual_image"
        note = "Abbildformat benötigt manuelle Installation oder spätere Erweiterung"
    elif entry.is_file() and entry.suffix.casefold() in ARCHIVE_EXTENSIONS:
        detected_type = "archive"
        note = "Archiv wird angezeigt, aber nicht automatisch ausgeführt"
    elif archives:
        detected_type = "archive"
        note = "Archiv im Eintrag erkannt; manuelle Installation erforderlich"
    else:
        detected_type = "manual"
        note = "Keine sichere Installationsaktion erkannt"

    relative_path = entry.relative_to(root).as_posix()
    launcher_relative = launcher.relative_to(root).as_posix() if launcher else None
    return ScanResult(
        game_id=stable_id(relative_path),
        relative_path=relative_path,
        title=clean_title(entry.name),
        detected_type=detected_type,
        launcher_relative_path=launcher_relative,
        file_count=file_count,
        logical_size=logical_size,
        detection_note=note,
    )


def scan_library(root: Path) -> list[ScanResult]:
    if not root.is_dir():
        raise FileNotFoundError(f"Games-Verzeichnis nicht gefunden: {root}")
    return [
        scan_entry(root, entry)
        for entry in sorted(root.iterdir(), key=lambda path: path.name.casefold())
        if entry.is_file() or entry.is_dir()
    ]
