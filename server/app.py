from __future__ import annotations

import os
import re
import secrets
import time
import zipfile
import base64
import json
import platform
import sqlite3
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from functools import wraps
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from database import Database
from design_profiles import DesignProfileStore
from scanner import ScanResult, scan_library, stable_id
from settings import DEFAULT_TRANSLATOR_URL, SettingsStore, THEMES
from translation import (
    TranslationError,
    normalize_translator_url,
    translate_text,
    validate_translator,
)
from metadata import (
    MetadataError,
    download_rawg_image,
    download_thegamesdb_image,
    fetch_rawg_game,
    fetch_rawg_image,
    fetch_thegamesdb_image,
    search_rawg,
    search_thegamesdb,
    suggest_game_title,
    validate_rawg_key,
    validate_thegamesdb_key,
)
from maintenance import create_backup, inspect_backup, restore_backup, rotate_backups, validate_backup


GAME_ROOT = Path(os.environ.get("GAMEVAULT_GAME_ROOT", "/games")).resolve()
ALLOWED_LIBRARY_ROOTS = tuple(dict.fromkeys(
    [GAME_ROOT]
    + [
        Path(value.strip()).resolve()
        for value in os.environ.get("GAMEVAULT_ALLOWED_LIBRARY_ROOTS", "/games,/libraries").split(",")
        if value.strip()
    ]
))
CONFIG_DIR = Path(os.environ.get("GAMEVAULT_CONFIG_DIR", "/config")).resolve()
AGENT_DIR = Path(os.environ.get("GAMEVAULT_AGENT_DIR", "/app/windows-agent")).resolve()
COVER_DIR = CONFIG_DIR / "covers"
BACKGROUND_DIR = CONFIG_DIR / "backgrounds"
BACKUP_DIR = CONFIG_DIR / "backups"
GUIDE_DIR = Path(__file__).with_name("static") / "docs"
ADMIN_PASSWORD = os.environ.get("GAMEVAULT_ADMIN_PASSWORD", "")
AGENT_TOKEN = os.environ.get("GAMEVAULT_AGENT_TOKEN", "")
SECRET_KEY = os.environ.get("GAMEVAULT_SECRET_KEY", "")
AGENT_INSTALLER_URL = os.environ.get(
    "MISSION_CONTROL_AGENT_INSTALLER_URL",
    "",
)


def load_version() -> str:
    candidates = (Path(__file__).with_name("VERSION"), Path(__file__).parent.parent / "VERSION")
    for candidate in candidates:
        try:
            value = candidate.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            return value
    return "development"


APP_VERSION = load_version()

if not ADMIN_PASSWORD or not AGENT_TOKEN or not SECRET_KEY:
    raise RuntimeError(
        "GAMEVAULT_ADMIN_PASSWORD, GAMEVAULT_AGENT_TOKEN und "
        "GAMEVAULT_SECRET_KEY müssen gesetzt sein."
    )

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
COVER_DIR.mkdir(parents=True, exist_ok=True)
BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(
    MAX_CONTENT_LENGTH=256 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=os.environ.get("GAMEVAULT_HTTPS", "0") == "1",
)

IMAGE_UPLOAD_LIMIT = 8 * 1024 * 1024


def image_upload_too_large() -> bool:
    return bool(request.content_length and request.content_length > IMAGE_UPLOAD_LIMIT)
database = Database(CONFIG_DIR / "gamevault.sqlite3")
settings_store = SettingsStore(CONFIG_DIR / "mission-control-settings.json")
design_profiles = DesignProfileStore(CONFIG_DIR / "mission-control-designs.json")


def login_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return function(*args, **kwargs)

    return wrapped


def csrf_token() -> str:
    return session.setdefault("csrf_token", secrets.token_urlsafe(32))


def csrf_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        submitted = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(submitted, expected):
            return jsonify(error="Ungültiger Sicherheitstoken; Seite bitte neu laden"), 403
        return function(*args, **kwargs)

    return wrapped


app.jinja_env.globals["csrf_token"] = csrf_token


def configured_libraries() -> list[dict]:
    return settings_store.load().get("libraries", [])


def library_by_id(library_id: str | None) -> dict:
    candidate = str(library_id or "primary").strip().casefold()
    for library in configured_libraries():
        if library["id"] == candidate and library.get("enabled", True):
            return library
    raise ValueError("Unbekannte oder deaktivierte Bibliothek")


def validate_library_definitions(libraries: object) -> list[dict]:
    if not isinstance(libraries, list) or not libraries:
        raise ValueError("Mindestens eine Bibliothek ist erforderlich")
    if len(libraries) > 32:
        raise ValueError("Es sind höchstens 32 Bibliotheken möglich")
    candidate = SettingsStore.validate({**settings_store.load(), "libraries": libraries})["libraries"]
    if len(candidate) != len(libraries):
        raise ValueError("Mindestens eine Bibliothek enthält eine ungültige ID oder einen ungültigen Pfad")
    resolved_paths: list[Path] = []
    for library in candidate:
        if library.get("source_type") == "windows_local":
            continue
        root = Path(library["container_path"]).resolve()
        if not root.is_dir():
            raise ValueError(f"Bibliothek '{library['name']}' ist im Container nicht erreichbar: {root}")
        if not any(root == allowed or allowed in root.parents for allowed in ALLOWED_LIBRARY_ROOTS):
            raise ValueError(
                f"Bibliothek '{library['name']}' liegt außerhalb der erlaubten Containerpfade"
            )
        if any(root == other or root in other.parents or other in root.parents for other in resolved_paths):
            raise ValueError("Bibliothekspfade dürfen nicht identisch oder ineinander verschachtelt sein")
        resolved_paths.append(root)
    return candidate


def safe_relative_path(value: str | None, library_id: str = "primary") -> str | None:
    if not value:
        return None
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Ungültiger relativer Pfad")
    library = library_by_id(library_id)
    if library.get("source_type") == "windows_local":
        return path.as_posix()
    root = Path(library["container_path"]).resolve()
    resolved = (root / Path(*path.parts)).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("Pfad verlässt das Games-Verzeichnis")
    if not resolved.exists():
        raise ValueError("Pfad existiert nicht")
    return path.as_posix()


def delete_game_covers(game_id: str, keep_name: str | None = None) -> None:
    for pattern in (f"{game_id}.*", f"{game_id}-*.*"):
        for old in COVER_DIR.glob(pattern):
            if old.name != keep_name:
                old.unlink(missing_ok=True)


@app.get("/health")
def health():
    return jsonify(
        status="ok",
        version=APP_VERSION,
        agent_api=3,
        game_root=str(GAME_ROOT),
        libraries=[{"id": item["id"], "name": item["name"], "container_path": item["container_path"]} for item in configured_libraries()],
        translator_managed=bool(DEFAULT_TRANSLATOR_URL),
    )


@app.get("/service-worker.js")
def service_worker():
    response = send_from_directory(app.static_folder, "service-worker.js")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        submitted = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        valid_csrf = expected and secrets.compare_digest(submitted, expected)
        if valid_csrf and secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session.clear()
            session["authenticated"] = True
            csrf_token()
            return redirect(request.args.get("next") or url_for("index"))
        error = "Anmeldung fehlgeschlagen"
    appearance = public_settings()
    login_language = appearance.get("ui_language", "auto")
    if login_language == "auto":
        login_language = request.accept_languages.best_match(
            ["ar", "de", "en", "ru", "it", "fr", "es", "pt", "pl", "nl", "tr"],
            default="de",
        )
    return render_template(
        "login.html", error=error, appearance=appearance,
        login_language=login_language,
    )


@app.post("/logout")
@csrf_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    # The release version is part of the static asset URLs. This prevents a
    # browser from combining a freshly updated template with an older cached
    # app.js/i18n.js file after a container upgrade.
    return render_template("index.html", asset_version=APP_VERSION)


def public_settings() -> dict:
    values = settings_store.load()
    profile_store = design_profiles.load(values.get("theme", "mission"))
    active_profile = profile_store["profiles"][profile_store["active"]]
    values["version"] = APP_VERSION
    values["libraries"] = [dict(item) for item in values.get("libraries", [])]
    values["active_design_profile"] = profile_store["active"]
    active_profile = dict(active_profile)
    if active_profile.get("builtin"):
        active_profile["background_name"] = active_profile.get("background_name") or values.get("background_name")
    values["design_profile"] = active_profile
    values["thegamesdb_configured"] = bool(values.get("thegamesdb_api_key"))
    values["rawg_configured"] = bool(values.get("rawg_api_key"))
    values["translator_configured"] = bool(values.get("translator_url"))
    values["translator_managed"] = bool(DEFAULT_TRANSLATOR_URL)
    values["translator_api_key_configured"] = bool(values.get("translator_api_key"))
    values.pop("rawg_api_key", None)
    values.pop("thegamesdb_api_key", None)
    values.pop("translator_api_key", None)
    values["background_url"] = (
        url_for("background", name=active_profile["background_name"])
        if active_profile.get("background_name")
        else None
    )
    return values


@app.get("/api/settings")
@login_required
def get_settings():
    return jsonify(public_settings())


@app.get("/api/translator/status")
@login_required
def translator_status():
    settings = settings_store.load()
    endpoint = settings.get("translator_url", "")
    if not endpoint:
        return jsonify(configured=False, reachable=False, error="Translator ist nicht eingerichtet")
    try:
        languages = validate_translator(endpoint, settings.get("translator_api_key", ""))
    except TranslationError as error:
        return jsonify(configured=True, reachable=False, error=str(error)), 502
    response = jsonify(configured=True, reachable=True, languages=languages or [])
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/translator/test")
@login_required
def test_translator():
    payload = request.get_json(silent=True) or {}
    settings = settings_store.load()
    raw_endpoint = payload.get("translator_url") or settings.get("translator_url", "")
    try:
        endpoint = normalize_translator_url(raw_endpoint)
    except TranslationError as error:
        return jsonify(configured=False, reachable=False, error=str(error)), 400
    if not endpoint:
        return jsonify(configured=False, reachable=False, error="Translator ist nicht eingerichtet"), 400

    supplied_key = str(payload.get("translator_api_key") or "")
    stored_endpoint = normalize_translator_url(settings.get("translator_url", ""))
    api_key = supplied_key
    if not api_key and endpoint == stored_endpoint:
        api_key = settings.get("translator_api_key", "")
    try:
        languages = validate_translator(endpoint, api_key)
    except TranslationError as error:
        response = jsonify(configured=True, reachable=False, error=str(error))
        response.headers["Cache-Control"] = "no-store"
        return response, 502
    response = jsonify(configured=True, reachable=True, languages=languages or [])
    response.headers["Cache-Control"] = "no-store"
    return response


@app.patch("/api/settings")
@login_required
@csrf_required
def update_settings():
    payload = request.get_json(force=True)
    allowed = {
        "server_name",
        "library_name",
        "libraries",
        "theme",
        "background_opacity",
        "background_blur",
        "crosshair_cursor",
        "scan_exclusions",
        "thegamesdb_api_key",
        "rawg_api_key",
        "favorite_content_language",
        "ui_language",
        "motion_preference",
        "translator_url",
        "translator_api_key",
    }
    changes = {key: payload[key] for key in allowed if key in payload}
    if "libraries" in changes:
        try:
            changes["libraries"] = validate_library_definitions(changes["libraries"])
        except ValueError as error:
            return jsonify(error=str(error)), 400
    if "theme" in changes and changes["theme"] not in THEMES:
        return jsonify(error="Unbekanntes Design"), 400
    if changes.get("thegamesdb_api_key"):
        try:
            validate_thegamesdb_key(str(changes["thegamesdb_api_key"]))
        except MetadataError as error:
            return jsonify(error=f"TheGamesDB-Key wurde nicht gespeichert: {error}"), 502
    if changes.get("rawg_api_key"):
        try:
            validate_rawg_key(str(changes["rawg_api_key"]))
        except MetadataError as error:
            return jsonify(error=f"RAWG-Key wurde nicht gespeichert: {error}"), 502
    if "translator_url" in changes:
        try:
            changes["translator_url"] = normalize_translator_url(changes["translator_url"])
        except TranslationError as error:
            return jsonify(error=f"Translator wurde nicht gespeichert: {error}"), 400
    if {"translator_url", "translator_api_key"} & changes.keys():
        current = settings_store.load()
        candidate_url = changes.get("translator_url", current.get("translator_url", ""))
        candidate_key = changes.get("translator_api_key", current.get("translator_api_key", ""))
        if candidate_url:
            try:
                validate_translator(candidate_url, candidate_key or "")
            except TranslationError as error:
                return jsonify(error=f"Translator wurde nicht gespeichert: {error}"), 502
    removed_library_ids: set[str] = set()
    if "libraries" in changes:
        old_library_ids = {item["id"] for item in configured_libraries()}
        new_library_ids = {item["id"] for item in changes["libraries"]}
        removed_library_ids = old_library_ids - new_library_ids
    settings_store.update(changes)
    for library_id in removed_library_ids:
        database.remove_library(library_id)
    return jsonify(public_settings())


def public_profiles() -> dict:
    settings = settings_store.load()
    store = design_profiles.list_public(settings.get("theme", "mission"))
    legacy_background = settings.get("background_name")
    profiles = []
    for key, profile in store["profiles"].items():
        visible = dict(profile)
        if visible.get("builtin"):
            visible["background_name"] = visible.get("background_name") or legacy_background
        profiles.append({"id": key, **visible})
    return {
        "active": store["active"],
        "profiles": profiles,
    }


@app.get("/api/design-profiles")
@login_required
def get_design_profiles():
    return jsonify(public_profiles())


@app.post("/api/design-profiles")
@login_required
@csrf_required
def create_design_profile():
    try:
        profile = design_profiles.create(request.get_json(force=True), settings_store.load().get("theme", "mission"))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(profile), 201


@app.put("/api/design-profiles/<profile_id>")
@login_required
@csrf_required
def update_design_profile(profile_id: str):
    try:
        profile = design_profiles.update(profile_id, request.get_json(force=True), settings_store.load().get("theme", "mission"))
    except KeyError as error:
        return jsonify(error=str(error.args[0])), 404
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(profile)


@app.post("/api/design-profiles/<profile_id>/activate")
@login_required
@csrf_required
def activate_design_profile(profile_id: str):
    try:
        design_profiles.activate(profile_id, settings_store.load().get("theme", "mission"))
    except KeyError as error:
        return jsonify(error=str(error.args[0])), 404
    return jsonify(public_settings())


@app.delete("/api/design-profiles/<profile_id>")
@login_required
@csrf_required
def delete_design_profile(profile_id: str):
    try:
        design_profiles.delete(profile_id, settings_store.load().get("theme", "mission"))
    except KeyError as error:
        return jsonify(error=str(error.args[0])), 404
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(public_profiles())


def _profile_background_payload(name: str | None) -> dict | None:
    if not name:
        return None
    path = BACKGROUND_DIR / Path(name).name
    if not path.is_file():
        return None
    data = path.read_bytes()
    # Base64 adds roughly one third. Keeping the raw image at 5 MiB leaves
    # enough room for the JSON envelope below Flask's 8 MiB request limit.
    if len(data) > 5 * 1024 * 1024:
        return None
    extension = path.suffix.casefold()
    media_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(extension)
    if not media_type:
        return None
    return {
        "filename": f"background{extension}",
        "media_type": media_type,
        "data": base64.b64encode(data).decode("ascii"),
    }


def _decode_profile_background(value: object) -> tuple[bytes, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"filename", "media_type", "data"}:
        raise ValueError("Ungültiger Hintergrund im Designpaket.")
    extension = Path(secure_filename(str(value["filename"]))).suffix.casefold()
    expected_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(extension)
    if not expected_type or value["media_type"] != expected_type:
        raise ValueError("Nicht unterstütztes Hintergrundformat im Designpaket.")
    try:
        data = base64.b64decode(str(value["data"]), validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("Beschädigte Hintergrunddaten im Designpaket.") from error
    if not data or len(data) > 5 * 1024 * 1024:
        raise ValueError("Der Profilhintergrund ist leer oder größer als 5 MiB.")
    valid = (
        data.startswith(b"\xff\xd8\xff")
        or data.startswith(b"\x89PNG\r\n\x1a\n")
        or (data.startswith(b"RIFF") and data[8:12] == b"WEBP")
    )
    if not valid:
        raise ValueError("Der Profilhintergrund ist keine gültige Bilddatei.")
    return data, extension


@app.get("/api/design-profiles/<profile_id>/export")
@login_required
def export_design_profile(profile_id: str):
    store = design_profiles.load(settings_store.load().get("theme", "mission"))
    profile = store["profiles"].get(profile_id)
    if not profile:
        return jsonify(error="Unbekanntes Designprofil."), 404
    portable = dict(profile)
    portable.pop("builtin", None)
    portable["background_name"] = None
    package = {
        "format": "hypetek-mission-control-design",
        "format_version": 1,
        "application_version": APP_VERSION,
        "profile": portable,
        "background": _profile_background_payload(profile.get("background_name")),
    }
    rendered = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", profile["name"]).strip("-") or "mission-control-design"
    return send_file(
        BytesIO(rendered),
        mimetype="application/json",
        as_attachment=True,
        download_name=f"{filename}.mcdesign.json",
    )


@app.post("/api/design-profiles/import")
@login_required
@csrf_required
def import_design_profile():
    package = request.get_json(force=True, silent=True)
    if not isinstance(package, dict):
        return jsonify(error="Das Designpaket enthält kein gültiges JSON."), 400
    if package.get("format") != "hypetek-mission-control-design" or package.get("format_version") != 1:
        return jsonify(error="Unbekanntes oder nicht unterstütztes Designpaket."), 400
    if not isinstance(package.get("profile"), dict):
        return jsonify(error="Im Designpaket fehlt das Profil."), 400
    stored_background = None
    try:
        background = _decode_profile_background(package.get("background"))
        profile = dict(package["profile"])
        profile["builtin"] = False
        if background:
            data, extension = background
            stored_background = f"background-{secrets.token_hex(12)}{extension}"
            background_path = BACKGROUND_DIR / stored_background
            background_path.write_bytes(data)
            os.chmod(background_path, 0o600)
            profile["background_name"] = stored_background
        else:
            profile["background_name"] = None
        # Imports never overwrite an existing profile. This also makes an
        # exported built-in profile portable, since every installation already
        # contains a profile named e.g. "Mission".
        existing = design_profiles.load(settings_store.load().get("theme", "mission"))["profiles"]
        existing_names = {item["name"].casefold() for item in existing.values()}
        original_name = str(profile.get("name") or "").strip()
        candidate = original_name
        counter = 1
        while candidate.casefold() in existing_names:
            suffix = " (Import)" if counter == 1 else f" (Import {counter})"
            candidate = f"{original_name[:48 - len(suffix)].rstrip()}{suffix}"
            counter += 1
        profile["name"] = candidate
        created = design_profiles.create(profile, settings_store.load().get("theme", "mission"))
    except ValueError as error:
        if stored_background:
            (BACKGROUND_DIR / stored_background).unlink(missing_ok=True)
        return jsonify(error=str(error)), 400
    return jsonify(created), 201


@app.post("/api/design-profiles/background")
@login_required
@csrf_required
def upload_design_profile_background():
    if image_upload_too_large():
        return jsonify(error="Bilddatei ist größer als 8 MiB"), 413
    upload = request.files.get("background")
    if not upload or not upload.filename:
        return jsonify(error="Keine Hintergrunddatei empfangen"), 400
    extension = Path(secure_filename(upload.filename)).suffix.casefold()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify(error="Erlaubt sind JPG, PNG und WEBP"), 400
    signature = upload.stream.read(16)
    upload.stream.seek(0)
    valid = (
        signature.startswith(b"\xff\xd8\xff")
        or signature.startswith(b"\x89PNG\r\n\x1a\n")
        or (signature.startswith(b"RIFF") and signature[8:12] == b"WEBP")
    )
    if not valid:
        return jsonify(error="Dateiinhalt ist kein unterstütztes Bild"), 400
    name = f"background-{secrets.token_hex(12)}{extension}"
    upload.save(BACKGROUND_DIR / name)
    return jsonify(name=name, url=url_for("background", name=name)), 201


@app.post("/api/settings/background")
@login_required
@csrf_required
def upload_background():
    if image_upload_too_large():
        return jsonify(error="Bilddatei ist größer als 8 MiB"), 413
    upload = request.files.get("background")
    if not upload or not upload.filename:
        return jsonify(error="Keine Hintergrunddatei empfangen"), 400
    extension = Path(secure_filename(upload.filename)).suffix.casefold()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify(error="Erlaubt sind JPG, PNG und WEBP"), 400
    signature = upload.stream.read(16)
    upload.stream.seek(0)
    is_jpeg = signature.startswith(b"\xff\xd8\xff")
    is_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = signature.startswith(b"RIFF") and signature[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        return jsonify(error="Dateiinhalt ist kein unterstütztes Bild"), 400
    name = f"custom-background{extension}"
    for old in BACKGROUND_DIR.glob("custom-background.*"):
        old.unlink(missing_ok=True)
    upload.save(BACKGROUND_DIR / name)
    settings_store.update({"background_name": name})
    return jsonify(public_settings())


@app.delete("/api/settings/background")
@login_required
@csrf_required
def delete_background():
    for old in BACKGROUND_DIR.glob("custom-background.*"):
        old.unlink(missing_ok=True)
    settings_store.update({"background_name": None})
    return jsonify(public_settings())


@app.get("/backgrounds/<name>")
@login_required
def background(name: str):
    return send_from_directory(BACKGROUND_DIR, secure_filename(name))


@app.get("/download/windows-agent.zip")
@login_required
def download_windows_agent():
    required = (
        "GameVaultAgent.ps1",
        "Install-Agent.ps1",
        "Uninstall-Agent.ps1",
        "README.txt",
    )
    missing = [name for name in required if not (AGENT_DIR / name).is_file()]
    if missing:
        return jsonify(error="Windows-Agent ist im Container unvollständig"), 503
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name in required:
            content = (AGENT_DIR / name).read_bytes()
            # Windows PowerShell 5 treats UTF-8 scripts without a BOM as an
            # ANSI codepage. Text instructions benefit from the same clear
            # encoding when opened in classic Windows editors.
            if not content.startswith(b"\xef\xbb\xbf"):
                content = b"\xef\xbb\xbf" + content
            output.writestr(f"Mission-Control-Windows-Agent/{name}", content)
    archive.seek(0)
    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        download_name="HypeTek-Mission-Control-Windows-Agent.zip",
    )


@app.get("/download/windows-agent.exe")
@login_required
def download_windows_agent_exe():
    installer_url = AGENT_INSTALLER_URL or (
        "https://github.com/HypeTek/hypetek-gamevault/releases/download/"
        f"v{APP_VERSION}/HypeTek-Mission-Control-Agent-Setup.exe"
    )
    return redirect(installer_url)


@app.get("/download/api-and-translator-guide.pdf")
@login_required
def download_api_and_translator_guide():
    return send_from_directory(
        GUIDE_DIR,
        "HypeTek-Mission-Control-API-und-Translator-Anleitung.pdf",
        as_attachment=True,
        download_name="HypeTek-Mission-Control-API-und-Translator-Anleitung.pdf",
    )


@app.get("/help/api-and-translator-guide/qr.svg")
@login_required
def api_and_translator_guide_qr():
    import qrcode
    from qrcode.image.svg import SvgPathImage

    target = url_for("download_api_and_translator_guide", _external=True)
    image = qrcode.make(target, image_factory=SvgPathImage, box_size=8, border=2)
    output = BytesIO()
    image.save(output)
    output.seek(0)
    return send_file(output, mimetype="image/svg+xml", max_age=300)


@app.get("/api/games")
@login_required
def games():
    requested_library = request.args.get("library") or None
    if requested_library:
        try:
            library_by_id(requested_library)
        except ValueError as error:
            return jsonify(error=str(error)), 400
    items = database.list_games(library_id=requested_library)
    libraries = {item["id"]: item for item in configured_libraries()}
    for game in items:
        library = libraries.get(game.get("library_id"), {})
        game["library_name"] = library.get("name", game.get("library_id", "primary"))
        game["metadata_search_title"] = suggest_game_title(game["title"])
    return jsonify(items)


@app.post("/api/scan")
@login_required
@csrf_required
def scan():
    automatic_backup()
    database.remove_unconfigured_libraries({item["id"] for item in configured_libraries()})
    exclusions = set(settings_store.load().get("scan_exclusions", []))
    payload = request.get_json(silent=True) or {}
    requested = payload.get("library_id")
    try:
        libraries = [library_by_id(requested)] if requested else [item for item in configured_libraries() if item.get("enabled", True)]
    except ValueError as error:
        return jsonify(error=str(error)), 400
    counts = {}
    agent_scans = []
    for library in libraries:
        if library.get("source_type") == "windows_local":
            token = secrets.token_urlsafe(32)
            database.create_agent_scan(token, library["id"], int(time.time()) + 900)
            agent_scans.append({
                "token": token,
                "library_id": library["id"],
                "library_name": library["name"],
                "protocol_url": f"hypetek-gamevault://scan?token={token}",
                "expires_in": 900,
            })
            continue
        root = Path(library["container_path"]).resolve()
        results = scan_library(root, exclusions, library["id"])
        database.apply_scan(results, library["id"])
        counts[library["id"]] = len(results)
    agent_protocol_url = None
    if agent_scans:
        tokens = ",".join(item["token"] for item in agent_scans)
        agent_protocol_url = f"hypetek-gamevault://scan?tokens={tokens}"
    return jsonify(
        scanned=sum(counts.values()), libraries=counts,
        agent_scans=agent_scans, agent_protocol_url=agent_protocol_url,
    )


def automatic_backup(force: bool = False) -> Path:
    latest = max(BACKUP_DIR.glob("mission-control-auto-*.zip"), key=lambda item: item.stat().st_mtime, default=None)
    if not force and latest and time.time() - latest.stat().st_mtime < 300:
        return latest
    name = f"mission-control-auto-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000:06d}.zip"
    result = create_backup(CONFIG_DIR, APP_VERSION, BACKUP_DIR / name)
    rotate_backups(BACKUP_DIR)
    return result


@app.get("/api/maintenance/backup")
@login_required
def download_backup():
    name = time.strftime("HypeTek-Mission-Control-backup-%Y%m%d-%H%M%S.zip")
    path = create_backup(CONFIG_DIR, APP_VERSION, BACKUP_DIR / name)
    return send_file(path, as_attachment=True, download_name=name, mimetype="application/zip")


@app.post("/api/maintenance/restore")
@login_required
@csrf_required
def restore_configuration():
    uploaded = request.files.get("backup")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Keine Sicherungsdatei ausgewählt."), 400
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(prefix="mission-control-restore-", suffix=".zip", delete=False) as temporary:
            temporary_name = temporary.name
            uploaded.save(temporary)
        validate_backup(Path(temporary_name))
        automatic_backup(force=True)
        restore_backup(Path(temporary_name), CONFIG_DIR)
        settings_store.load()
        design_profiles.load(settings_store.load().get("theme", "mission"))
    except (ValueError, zipfile.BadZipFile, OSError, sqlite3.DatabaseError) as error:
        return jsonify(error=str(error), message_key="maintenance.restoreFailed"), 400
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
    return jsonify(ok=True, settings=public_settings())


@app.post("/api/maintenance/backup/inspect")
@login_required
@csrf_required
def inspect_configuration_backup():
    uploaded = request.files.get("backup")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Keine Sicherungsdatei ausgewählt.", message_key="maintenance.invalidBackup"), 400
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(prefix="mission-control-inspect-", suffix=".zip", delete=False) as temporary:
            temporary_name = temporary.name
            uploaded.save(temporary)
        return jsonify(ok=True, summary=inspect_backup(Path(temporary_name)))
    except (ValueError, zipfile.BadZipFile, OSError) as error:
        return jsonify(error=str(error), message_key="maintenance.invalidBackup"), 400
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


@app.get("/api/maintenance/status")
@login_required
def maintenance_status():
    latest = max(BACKUP_DIR.glob("mission-control-auto-*.zip"), key=lambda item: item.stat().st_mtime, default=None)
    return jsonify(
        current=APP_VERSION,
        last_automatic_backup=(datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc).isoformat() if latest else None),
    )


@app.get("/api/maintenance/diagnostics")
@login_required
def download_diagnostics():
    settings = settings_store.load().copy()
    for key in ("thegamesdb_api_key", "translator_api_key", "rawg_api_key"):
        settings.pop(key, None)
    integrity = "unavailable"
    try:
        with database.connect() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError:
        integrity = "error"
    report = {
        "application": "HypeTek Mission Control",
        "version": APP_VERSION,
        "generated_at": int(time.time()),
        "python": platform.python_version(),
        "database_integrity": integrity,
        "game_count": len(database.list_games()),
        "game_root_exists": GAME_ROOT.is_dir(),
        "translator_managed": bool(DEFAULT_TRANSLATOR_URL),
        "settings_without_secrets": settings,
        "secrets_included": False,
    }
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics.json", json.dumps(report, ensure_ascii=False, indent=2))
        archive.writestr("README.txt", "HypeTek Mission Control diagnostics\nNo passwords, tokens or API keys are included.\n")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"mission-control-diagnostics-{APP_VERSION}.zip", mimetype="application/zip")


@app.get("/api/maintenance/update")
@login_required
def check_for_update():
    try:
        query = Request(
            "https://api.github.com/repos/HypeTek/hypetek-gamevault/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": f"HypeTek-Mission-Control/{APP_VERSION}"},
        )
        with urlopen(query, timeout=6) as response:
            release = json.loads(response.read().decode("utf-8"))
        latest = str(release.get("tag_name") or "").lstrip("v")
        def version_tuple(value: str) -> tuple[int, ...]:
            return tuple(int(part) for part in re.findall(r"\d+", value)[:3])
        return jsonify(current=APP_VERSION, latest=latest, update_available=version_tuple(latest) > version_tuple(APP_VERSION), url=release.get("html_url"), name=release.get("name"), published_at=release.get("published_at"))
    except Exception as error:
        return jsonify(current=APP_VERSION, reachable=False, error=str(error)), 502


@app.patch("/api/games/<game_id>")
@login_required
@csrf_required
def update_game(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    payload = request.get_json(force=True)
    action = payload.get("action_override")
    if action not in {None, "", "direct_setup", "iso", "manual", "archive", "manual_image", "ignore"}:
        return jsonify(error="Ungültige Aktion"), 400
    try:
        if "launcher_override" in payload:
            payload["launcher_override"] = safe_relative_path(payload.get("launcher_override"), game["library_id"])
    except ValueError as error:
        return jsonify(error=str(error)), 400
    if "cover_position_y" in payload:
        try:
            payload["cover_position_y"] = max(0, min(100, int(payload["cover_position_y"])))
        except (TypeError, ValueError):
            return jsonify(error="Ungültige Coverposition"), 400
    if "favorite" in payload:
        if not isinstance(payload["favorite"], bool):
            return jsonify(error="Ungültiger Favoritenstatus"), 400
        payload["favorite"] = 1 if payload["favorite"] else 0
    database.update_game(game_id, payload)
    return jsonify(database.get_game(game_id))


@app.post("/api/games/<game_id>/metadata/search")
@login_required
@csrf_required
def search_game_metadata(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    payload = request.get_json(silent=True) or {}
    query = suggest_game_title(str(payload.get("query") or game["title"]).strip()[:160])
    settings = settings_store.load()
    providers = (
        ("TheGamesDB", settings.get("thegamesdb_api_key", ""), search_thegamesdb),
        ("RAWG", settings.get("rawg_api_key", ""), search_rawg),
    )
    results, warnings, attempted = [], [], 0
    for provider_name, api_key, search_function in providers:
        if not api_key:
            continue
        attempted += 1
        try:
            # Provider order is intentional: TheGamesDB first, RAWG directly
            # below it in the same result list.
            results.extend(search_function(api_key, query))
        except MetadataError as error:
            warnings.append(f"{provider_name}: {error}")
    if not attempted:
        return jsonify(error="Bitte zuerst einen TheGamesDB- oder RAWG-API-Key hinterlegen"), 409
    if not results and warnings:
        return jsonify(error=" · ".join(warnings)), 502
    for result in results:
        result["preview_url"] = url_for(
            "metadata_preview", provider=result["provider"], url=result["image_url"]
        )
    return jsonify(query=query, results=results, warnings=warnings)


@app.get("/api/metadata/preview")
@login_required
def metadata_preview():
    try:
        provider = request.args.get("provider", "thegamesdb")
        fetcher = fetch_rawg_image if provider == "rawg" else fetch_thegamesdb_image
        if provider not in {"rawg", "thegamesdb"}:
            return jsonify(error="Unbekannter Metadatenanbieter"), 400
        data, content_type = fetcher(request.args.get("url", ""))
    except MetadataError as error:
        return jsonify(error=str(error)), 502
    response = send_file(BytesIO(data), mimetype=content_type, max_age=14400)
    response.headers["Cache-Control"] = "private, max-age=14400"
    return response


@app.post("/api/games/<game_id>/metadata/apply")
@login_required
@csrf_required
def apply_game_metadata(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    payload = request.get_json(force=True)
    provider = str(payload.get("provider") or "")
    if provider not in {"thegamesdb", "rawg"}:
        return jsonify(error="Unbekannter Metadatenanbieter"), 400
    source_url = str(payload.get("source_url") or "")
    parsed_source = urlparse(source_url)
    provider_id = str(payload.get("provider_id") or "")[:80]
    if not provider_id.isdigit():
        return jsonify(error="Ungültige Anbieter-ID"), 400
    if provider == "thegamesdb":
        source_id = (parse_qs(parsed_source.query).get("id") or [""])[0]
        if parsed_source.scheme != "https" or parsed_source.hostname != "thegamesdb.net" or parsed_source.path != "/game.php" or source_id != provider_id:
            return jsonify(error="Ungültiger TheGamesDB-Quellenlink"), 400
        authoritative = payload
        downloader = download_thegamesdb_image
    else:
        if parsed_source.scheme != "https" or parsed_source.hostname != "rawg.io" or not parsed_source.path.startswith("/games/"):
            return jsonify(error="Ungültiger RAWG-Quellenlink"), 400
        try:
            authoritative = fetch_rawg_game(settings_store.load().get("rawg_api_key", ""), provider_id)
        except MetadataError as error:
            return jsonify(error=str(error)), 502
        if authoritative["source_url"] != source_url:
            return jsonify(error="RAWG-Datensatz und Quellenlink stimmen nicht überein"), 400
        downloader = download_rawg_image
    try:
        name = downloader(
            str(authoritative.get("image_url") or ""),
            COVER_DIR / f"{game_id}-{secrets.token_hex(5)}",
        )
    except MetadataError as error:
        return jsonify(error=str(error)), 502
    delete_game_covers(game_id, keep_name=name)
    database.update_game(game_id, {
        "cover_name": name,
        "metadata_provider": provider,
        "metadata_provider_id": provider_id,
        "metadata_source_url": source_url[:500],
        "metadata_title": str(authoritative.get("name") or "")[:160],
        "metadata_overview": str(authoritative.get("overview") or "")[:12000],
        "metadata_overview_original": str(authoritative.get("overview") or "")[:12000],
        "metadata_overview_language": "original",
        "metadata_release_date": str(authoritative.get("released") or "")[:10],
        "metadata_platform": str(authoritative.get("platform") or "")[:80],
        "metadata_rating": str(authoritative.get("rating") or "")[:80],
        "metadata_players": str(authoritative.get("players") or "")[:40],
        "metadata_coop": str(authoritative.get("coop") or "")[:40],
    })
    return jsonify(database.get_game(game_id))


@app.post("/api/games/<game_id>/metadata/translate")
@login_required
@csrf_required
def translate_game_metadata(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    source = str(game.get("metadata_overview_original") or game.get("metadata_overview") or "").strip()
    if not source:
        return jsonify(error="Für diesen Eintrag ist kein Spielinhalt vorhanden"), 409
    settings = settings_store.load()
    endpoint = settings.get("translator_url", "")
    if not endpoint:
        return jsonify(error="In den Einstellungen ist kein Mission Control Translator eingerichtet"), 409
    payload = request.get_json(silent=True) or {}
    target = str(payload.get("target_language") or settings.get("favorite_content_language") or "de").strip().casefold()
    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", target):
        return jsonify(error="Ungültige Zielsprache"), 400
    try:
        languages = validate_translator(endpoint, settings.get("translator_api_key", ""))
        if target not in languages:
            return jsonify(error="Diese Zielsprache ist im Translator nicht installiert"), 409
        translated = translate_text(
            endpoint,
            source,
            target,
            settings.get("translator_api_key", ""),
            available_languages=languages,
        )
    except TranslationError as error:
        return jsonify(error=str(error)), 502
    database.update_game(game_id, {
        "metadata_overview_original": source[:12000],
        "metadata_overview": translated[:12000],
        "metadata_overview_language": target,
    })
    return jsonify(database.get_game(game_id))


@app.post("/api/games/<game_id>/cover")
@login_required
@csrf_required
def upload_cover(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    if image_upload_too_large():
        return jsonify(error="Bilddatei ist größer als 8 MiB"), 413
    upload = request.files.get("cover")
    if not upload or not upload.filename:
        return jsonify(error="Keine Bilddatei empfangen"), 400
    extension = Path(secure_filename(upload.filename)).suffix.casefold()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify(error="Erlaubt sind JPG, PNG und WEBP"), 400
    signature = upload.stream.read(16)
    upload.stream.seek(0)
    is_jpeg = signature.startswith(b"\xff\xd8\xff")
    is_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = signature.startswith(b"RIFF") and signature[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        return jsonify(error="Dateiinhalt ist kein unterstütztes Bild"), 400
    name = f"{game_id}-{secrets.token_hex(5)}{extension}"
    upload.save(COVER_DIR / name)
    delete_game_covers(game_id, keep_name=name)
    database.update_game(game_id, {
        "cover_name": name,
        "metadata_provider": None,
        "metadata_provider_id": None,
        "metadata_source_url": None,
        "metadata_title": None,
        "metadata_overview": None,
        "metadata_overview_original": None,
        "metadata_overview_language": None,
        "metadata_release_date": None,
        "metadata_platform": None,
        "metadata_rating": None,
        "metadata_players": None,
        "metadata_coop": None,
    })
    return jsonify(cover_url=url_for("cover", name=name))


@app.get("/covers/<name>")
@login_required
def cover(name: str):
    return send_from_directory(COVER_DIR, secure_filename(name))


@app.post("/api/games/<game_id>/launch-ticket")
@login_required
@csrf_required
def launch_ticket(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    payload = request.get_json(silent=True) or {}
    requested_action = payload.get("action") or game["action"]
    if requested_action == "open_folder":
        launcher = game["relative_path"]
    elif requested_action in {"direct_setup", "iso"} and game["launcher"]:
        launcher = game["launcher"]
    else:
        return jsonify(error="Für diesen Eintrag ist keine automatische Aktion freigegeben"), 409
    try:
        safe_relative_path(launcher, game["library_id"])
    except ValueError as error:
        return jsonify(error=str(error)), 409
    token = secrets.token_urlsafe(32)
    database.create_ticket(token, game_id, requested_action, int(time.time()) + 120)
    return jsonify(protocol_url=f"hypetek-gamevault://launch?ticket={token}", expires_in=120)


@app.post("/api/agent/probes")
@login_required
@csrf_required
def create_agent_probe():
    token = secrets.token_urlsafe(32)
    database.create_agent_probe(token, int(time.time()) + 45)
    return jsonify(
        token=token,
        protocol_url=f"hypetek-gamevault://probe?token={token}",
        expires_in=45,
    )


@app.get("/api/agent/probes/<token>")
@login_required
def agent_probe_status(token: str):
    probe = database.get_agent_probe(token)
    if not probe:
        abort(404)
    return jsonify(
        confirmed=bool(probe.get("confirmed_at")),
        expired=int(probe["expires_at"]) < int(time.time()),
    )


@app.post("/api/agent/probes/<token>/confirm")
def confirm_agent_probe(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    if not database.confirm_agent_probe(token):
        return jsonify(error="Prüfung ungültig, abgelaufen oder bereits bestätigt"), 404
    response = app.response_class(status=204)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/agent/folder-pickers")
@login_required
@csrf_required
def create_folder_picker():
    token = secrets.token_urlsafe(32)
    database.create_folder_picker(token, int(time.time()) + 120)
    return jsonify(
        token=token,
        protocol_url=f"hypetek-gamevault://browse?token={token}",
        expires_in=120,
    )


@app.get("/api/agent/folder-pickers/<token>")
@login_required
def folder_picker_status(token: str):
    picker = database.get_folder_picker(token)
    if not picker:
        abort(404)
    return jsonify(
        completed=bool(picker.get("confirmed_at")),
        selected_path=picker.get("selected_path"),
        expired=int(picker["expires_at"]) < int(time.time()),
    )


@app.post("/api/agent/folder-pickers/<token>/complete")
def complete_folder_picker(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    payload = request.get_json(silent=True) or {}
    cancelled = payload.get("cancelled") is True
    selected_path = str(payload.get("selected_path", "")).strip()
    if (not cancelled and not selected_path) or len(selected_path) > 1024:
        return jsonify(error="Ungültiger Windows-Pfad"), 400
    if not database.complete_folder_picker(token, selected_path):
        return jsonify(error="Ordnerauswahl ungültig, abgelaufen oder bereits bestätigt"), 404
    response = app.response_class(status=204)
    response.headers["Cache-Control"] = "no-store"
    return response


def _agent_scan_results(payload: object, library_id: str) -> list[ScanResult]:
    if not isinstance(payload, list) or len(payload) > 10000:
        raise ValueError("Ungültige Scan-Ergebnisse")
    allowed_types = {"direct_setup", "iso", "manual"}
    results: list[ScanResult] = []
    seen_paths: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Ungültiger Bibliothekseintrag")
        relative_path = safe_relative_path(str(item.get("relative_path") or ""), library_id)
        if not relative_path or relative_path.casefold() in seen_paths:
            raise ValueError("Doppelter oder leerer relativer Pfad")
        seen_paths.add(relative_path.casefold())
        launcher = item.get("launcher_relative_path")
        launcher_path = safe_relative_path(str(launcher), library_id) if launcher else None
        detected_type = str(item.get("detected_type") or "manual")
        if detected_type not in allowed_types:
            raise ValueError("Unbekannter Eintragstyp")
        try:
            file_count = min(10_000_000, max(0, int(item.get("file_count") or 0)))
            logical_size = min(2**63 - 1, max(0, int(item.get("logical_size") or 0)))
        except (TypeError, ValueError):
            raise ValueError("Ungültige Dateistatistik") from None
        title = str(item.get("title") or Path(relative_path).name).strip()[:300]
        if not title:
            raise ValueError("Leerer Titel")
        results.append(ScanResult(
            game_id=stable_id(relative_path, library_id),
            relative_path=relative_path,
            title=title,
            detected_type=detected_type,
            launcher_relative_path=launcher_path,
            file_count=file_count,
            logical_size=logical_size,
            detection_note=str(item.get("detection_note") or "Vom Windows-Agent erkannt")[:500],
        ))
    return results


@app.get("/api/agent/scans/<token>")
def agent_scan_manifest(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    scan_request = database.get_agent_scan(token)
    if not scan_request or scan_request.get("completed_at") or int(scan_request["expires_at"]) < int(time.time()):
        return jsonify(error="Scan-Auftrag ungültig, abgelaufen oder bereits verwendet"), 404
    try:
        library = library_by_id(scan_request["library_id"])
    except ValueError as error:
        return jsonify(error=str(error)), 409
    if library.get("source_type") != "windows_local":
        return jsonify(error="Bibliothek ist keine lokale Windows-Bibliothek"), 409
    return jsonify(
        library_id=library["id"],
        library_name=library["name"],
        windows_path_hint=library["windows_path"],
        scan_exclusions=settings_store.load().get("scan_exclusions", []),
    )


@app.post("/api/agent/scans/<token>/start")
def start_agent_scan(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    if not database.start_agent_scan(token):
        return jsonify(error="Scan-Auftrag ungültig, abgelaufen oder bereits verwendet"), 404
    return jsonify(ok=True)


@app.post("/api/agent/scans/<token>/complete")
def complete_agent_scan(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    scan_request = database.get_agent_scan(token)
    if not scan_request or scan_request.get("completed_at") or int(scan_request["expires_at"]) < int(time.time()):
        return jsonify(error="Scan-Auftrag ungültig, abgelaufen oder bereits verwendet"), 404
    try:
        results = _agent_scan_results((request.get_json(silent=True) or {}).get("results"), scan_request["library_id"])
        database.apply_scan(results, scan_request["library_id"])
        database.complete_agent_scan(token, len(results))
    except ValueError as error:
        database.complete_agent_scan(token, 0, str(error))
        return jsonify(error=str(error)), 400
    return jsonify(ok=True, scanned=len(results))


@app.post("/api/agent/scans/<token>/fail")
def fail_agent_scan(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    scan_request = database.get_agent_scan(token)
    if not scan_request or scan_request.get("completed_at") or int(scan_request["expires_at"]) < int(time.time()):
        return jsonify(error="Scan-Auftrag ungültig, abgelaufen oder bereits verwendet"), 404
    message = str((request.get_json(silent=True) or {}).get("error") or "Windows-Agent hat den Scan abgebrochen")[:500]
    database.complete_agent_scan(token, 0, message)
    return jsonify(ok=True)


@app.get("/api/agent/scans/<token>/status")
@login_required
def agent_scan_status(token: str):
    scan_request = database.get_agent_scan(token)
    if not scan_request:
        abort(404)
    return jsonify(
        started=bool(scan_request.get("started_at")),
        completed=bool(scan_request.get("completed_at")),
        expired=int(scan_request["expires_at"]) < int(time.time()),
        scanned=scan_request.get("result_count") or 0,
        error=scan_request.get("error"),
    )


@app.post("/api/agent/validate")
def validate_agent_token():
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    response = app.response_class(status=204)
    response.headers["X-Mission-Control-Agent"] = "authenticated"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/agent/tickets/<token>")
def agent_ticket(token: str):
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization, f"Bearer {AGENT_TOKEN}"):
        return jsonify(error="Nicht autorisiert"), 401
    game = database.consume_ticket(token)
    if not game:
        return jsonify(error="Ticket ungültig, abgelaufen oder bereits verwendet"), 404
    requested_action = game["requested_action"]
    if requested_action == "open_folder":
        launcher_value = game["relative_path"]
    elif requested_action in {"direct_setup", "iso"} and game["launcher"]:
        launcher_value = game["launcher"]
    else:
        return jsonify(error="Aktion nicht freigegeben"), 409
    try:
        launcher = safe_relative_path(launcher_value, game["library_id"])
    except ValueError as error:
        return jsonify(error=str(error)), 409
    return jsonify(
        game_id=game["id"],
        title=game["title"],
        action=requested_action,
        relative_path=game["relative_path"],
        launcher=launcher,
        library_id=game["library_id"],
        library_name=library_by_id(game["library_id"])["name"],
        windows_path_hint=library_by_id(game["library_id"])["windows_path"],
        linux_path_hint=library_by_id(game["library_id"]).get("linux_path", ""),
        ui_language=settings_store.load().get("ui_language", "auto"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
