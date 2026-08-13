from __future__ import annotations

import os
import secrets
import time
import zipfile
from io import BytesIO
from functools import wraps
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

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
from scanner import scan_library
from settings import SettingsStore, THEMES
from metadata import MetadataError, download_rawg_image, search_rawg, validate_rawg_key


GAME_ROOT = Path(os.environ.get("GAMEVAULT_GAME_ROOT", "/games")).resolve()
CONFIG_DIR = Path(os.environ.get("GAMEVAULT_CONFIG_DIR", "/config")).resolve()
AGENT_DIR = Path(os.environ.get("GAMEVAULT_AGENT_DIR", "/app/windows-agent")).resolve()
COVER_DIR = CONFIG_DIR / "covers"
BACKGROUND_DIR = CONFIG_DIR / "backgrounds"
ADMIN_PASSWORD = os.environ.get("GAMEVAULT_ADMIN_PASSWORD", "")
AGENT_TOKEN = os.environ.get("GAMEVAULT_AGENT_TOKEN", "")
SECRET_KEY = os.environ.get("GAMEVAULT_SECRET_KEY", "")
AGENT_INSTALLER_URL = os.environ.get(
    "MISSION_CONTROL_AGENT_INSTALLER_URL",
    "https://github.com/HypeTek/hypetek-gamevault/releases/latest/download/HypeTek-Mission-Control-Agent-Setup.exe",
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


@app.get("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION, agent_api=2, game_root=str(GAME_ROOT))


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
    return render_template("login.html", error=error, appearance=settings_store.load())


@app.post("/logout")
@csrf_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    return render_template("index.html")


def public_settings() -> dict:
    values = settings_store.load()
    values["rawg_configured"] = bool(values.get("rawg_api_key"))
    values.pop("rawg_api_key", None)
    values["background_url"] = (
        url_for("background", name=values["background_name"])
        if values.get("background_name")
        else None
    )
    return values


@app.get("/api/settings")
@login_required
def get_settings():
    return jsonify(public_settings())


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
        "rawg_api_key",
    }
    changes = {key: payload[key] for key in allowed if key in payload}
    if "theme" in changes and changes["theme"] not in THEMES:
        return jsonify(error="Unbekanntes Design"), 400
    if changes.get("rawg_api_key"):
        try:
            validate_rawg_key(str(changes["rawg_api_key"]))
        except MetadataError as error:
            return jsonify(error=f"RAWG-Key wurde nicht gespeichert: {error}"), 502
    settings_store.update(changes)
    return jsonify(public_settings())


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
    required = ("GameVaultAgent.ps1", "Install-Agent.ps1", "Uninstall-Agent.ps1")
    missing = [name for name in required if not (AGENT_DIR / name).is_file()]
    if missing:
        return jsonify(error="Windows-Agent ist im Container unvollständig"), 503
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name in required:
            content = (AGENT_DIR / name).read_bytes()
            # Windows PowerShell 5 treats UTF-8 without a BOM as an ANSI
            # codepage. Ship unambiguous UTF-8 so German punctuation cannot
            # corrupt the downloaded script during parsing.
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
    return redirect(AGENT_INSTALLER_URL)


@app.get("/api/games")
@login_required
def games():
    return jsonify(database.list_games())


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
    query = str(payload.get("query") or game["title"]).strip()[:160]
    try:
        results = search_rawg(settings_store.load().get("rawg_api_key", ""), query)
    except MetadataError as error:
        return jsonify(error=str(error)), 502
    return jsonify(query=query, results=results)


@app.post("/api/games/<game_id>/metadata/apply")
@login_required
@csrf_required
def apply_game_metadata(game_id: str):
    game = database.get_game(game_id)
    if not game:
        abort(404)
    payload = request.get_json(force=True)
    if payload.get("provider") != "rawg":
        return jsonify(error="Unbekannter Metadatenanbieter"), 400
    source_url = str(payload.get("source_url") or "")
    parsed_source = urlparse(source_url)
    if parsed_source.scheme != "https" or parsed_source.hostname != "rawg.io" or not parsed_source.path.startswith("/games/"):
        return jsonify(error="Ungültiger RAWG-Quellenlink"), 400
    for old in COVER_DIR.glob(f"{game_id}.*"):
        old.unlink(missing_ok=True)
    try:
        name = download_rawg_image(str(payload.get("image_url") or ""), COVER_DIR / game_id)
    except MetadataError as error:
        return jsonify(error=str(error)), 502
    database.update_game(game_id, {
        "cover_name": name,
        "metadata_provider": "rawg",
        "metadata_provider_id": str(payload.get("provider_id") or "")[:80],
        "metadata_source_url": source_url[:500],
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
    name = f"{game_id}{extension}"
    for old in COVER_DIR.glob(f"{game_id}.*"):
        old.unlink(missing_ok=True)
    upload.save(COVER_DIR / name)
    database.update_game(game_id, {
        "cover_name": name,
        "metadata_provider": None,
        "metadata_provider_id": None,
        "metadata_source_url": None,
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
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
