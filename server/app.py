from __future__ import annotations

import os
import re
import secrets
import time
import zipfile
import base64
import json
from io import BytesIO
from functools import wraps
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlparse

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
from scanner import scan_library
from settings import DEFAULT_TRANSLATOR_URL, SettingsStore, THEMES
from translation import (
    TranslationError,
    normalize_translator_url,
    translate_text,
    validate_translator,
)
from metadata import (
    MetadataError,
    download_thegamesdb_image,
    fetch_thegamesdb_image,
    search_thegamesdb,
    suggest_game_title,
    validate_thegamesdb_key,
)


GAME_ROOT = Path(os.environ.get("GAMEVAULT_GAME_ROOT", "/games")).resolve()
CONFIG_DIR = Path(os.environ.get("GAMEVAULT_CONFIG_DIR", "/config")).resolve()
AGENT_DIR = Path(os.environ.get("GAMEVAULT_AGENT_DIR", "/app/windows-agent")).resolve()
COVER_DIR = CONFIG_DIR / "covers"
BACKGROUND_DIR = CONFIG_DIR / "backgrounds"
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

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=os.environ.get("GAMEVAULT_HTTPS", "0") == "1",
)
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


def safe_relative_path(value: str | None) -> str | None:
    if not value:
        return None
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Ungültiger relativer Pfad")
    resolved = (GAME_ROOT / Path(*path.parts)).resolve()
    if resolved != GAME_ROOT and GAME_ROOT not in resolved.parents:
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
    return render_template("login.html", error=error, appearance=public_settings())


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
    values["active_design_profile"] = profile_store["active"]
    active_profile = dict(active_profile)
    if active_profile.get("builtin"):
        active_profile["background_name"] = active_profile.get("background_name") or values.get("background_name")
    values["design_profile"] = active_profile
    values["thegamesdb_configured"] = bool(values.get("thegamesdb_api_key"))
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
        "theme",
        "background_opacity",
        "background_blur",
        "crosshair_cursor",
        "scan_exclusions",
        "thegamesdb_api_key",
        "favorite_content_language",
        "ui_language",
        "motion_preference",
        "translator_url",
        "translator_api_key",
    }
    changes = {key: payload[key] for key in allowed if key in payload}
    if "theme" in changes and changes["theme"] not in THEMES:
        return jsonify(error="Unbekanntes Design"), 400
    if changes.get("thegamesdb_api_key"):
        try:
            validate_thegamesdb_key(str(changes["thegamesdb_api_key"]))
        except MetadataError as error:
            return jsonify(error=f"TheGamesDB-Key wurde nicht gespeichert: {error}"), 502
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
    settings_store.update(changes)
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
    items = database.list_games()
    for game in items:
        game["metadata_search_title"] = suggest_game_title(game["title"])
    return jsonify(items)


@app.post("/api/scan")
@login_required
@csrf_required
def scan():
    exclusions = set(settings_store.load().get("scan_exclusions", []))
    results = scan_library(GAME_ROOT, exclusions)
    database.apply_scan(results)
    return jsonify(scanned=len(results))


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
            payload["launcher_override"] = safe_relative_path(payload.get("launcher_override"))
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
    try:
        results = search_thegamesdb(
            settings_store.load().get("thegamesdb_api_key", ""), query
        )
    except MetadataError as error:
        return jsonify(error=str(error)), 502
    for result in results:
        result["preview_url"] = url_for(
            "metadata_preview", url=result["image_url"]
        )
    return jsonify(query=query, results=results)


@app.get("/api/metadata/preview")
@login_required
def metadata_preview():
    try:
        data, content_type = fetch_thegamesdb_image(request.args.get("url", ""))
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
    if payload.get("provider") != "thegamesdb":
        return jsonify(error="Unbekannter Metadatenanbieter"), 400
    source_url = str(payload.get("source_url") or "")
    parsed_source = urlparse(source_url)
    provider_id = str(payload.get("provider_id") or "")[:80]
    source_id = (parse_qs(parsed_source.query).get("id") or [""])[0]
    if (
        parsed_source.scheme != "https"
        or parsed_source.hostname != "thegamesdb.net"
        or parsed_source.path != "/game.php"
        or not provider_id.isdigit()
        or source_id != provider_id
    ):
        return jsonify(error="Ungültiger TheGamesDB-Quellenlink"), 400
    try:
        name = download_thegamesdb_image(
            str(payload.get("image_url") or ""),
            COVER_DIR / f"{game_id}-{secrets.token_hex(5)}",
        )
    except MetadataError as error:
        return jsonify(error=str(error)), 502
    delete_game_covers(game_id, keep_name=name)
    database.update_game(game_id, {
        "cover_name": name,
        "metadata_provider": "thegamesdb",
        "metadata_provider_id": provider_id,
        "metadata_source_url": source_url[:500],
        "metadata_title": str(payload.get("name") or "")[:160],
        "metadata_overview": str(payload.get("overview") or "")[:12000],
        "metadata_overview_original": str(payload.get("overview") or "")[:12000],
        "metadata_overview_language": "original",
        "metadata_release_date": str(payload.get("released") or "")[:10],
        "metadata_platform": str(payload.get("platform") or "")[:80],
        "metadata_rating": str(payload.get("rating") or "")[:80],
        "metadata_players": str(payload.get("players") or "")[:40],
        "metadata_coop": str(payload.get("coop") or "")[:40],
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
        safe_relative_path(launcher)
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
        launcher = safe_relative_path(launcher_value)
    except ValueError as error:
        return jsonify(error=str(error)), 409
    return jsonify(
        game_id=game["id"],
        title=game["title"],
        action=requested_action,
        relative_path=game["relative_path"],
        launcher=launcher,
        ui_language=settings_store.load().get("ui_language", "auto"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
