from __future__ import annotations

import os
import secrets
import time
import zipfile
from io import BytesIO
from functools import wraps
from pathlib import Path, PurePosixPath

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


GAME_ROOT = Path(os.environ.get("GAMEVAULT_GAME_ROOT", "/games")).resolve()
CONFIG_DIR = Path(os.environ.get("GAMEVAULT_CONFIG_DIR", "/config")).resolve()
AGENT_DIR = Path(os.environ.get("GAMEVAULT_AGENT_DIR", "/app/windows-agent")).resolve()
COVER_DIR = CONFIG_DIR / "covers"
ADMIN_PASSWORD = os.environ.get("GAMEVAULT_ADMIN_PASSWORD", "")
AGENT_TOKEN = os.environ.get("GAMEVAULT_AGENT_TOKEN", "")
SECRET_KEY = os.environ.get("GAMEVAULT_SECRET_KEY", "")

if not ADMIN_PASSWORD or not AGENT_TOKEN or not SECRET_KEY:
    raise RuntimeError(
        "GAMEVAULT_ADMIN_PASSWORD, GAMEVAULT_AGENT_TOKEN und "
        "GAMEVAULT_SECRET_KEY müssen gesetzt sein."
    )

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
COVER_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=os.environ.get("GAMEVAULT_HTTPS", "0") == "1",
)
database = Database(CONFIG_DIR / "gamevault.sqlite3")


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
    return jsonify(status="ok", game_root=str(GAME_ROOT))


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
    return render_template("login.html", error=error)


@app.post("/logout")
@csrf_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    return render_template("index.html")


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
            output.write(AGENT_DIR / name, arcname=f"GameVault-Windows-Agent/{name}")
    archive.seek(0)
    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        download_name="HypeTek-GameVault-Windows-Agent.zip",
    )


@app.get("/api/games")
@login_required
def games():
    return jsonify(database.list_games())


@app.post("/api/scan")
@login_required
@csrf_required
def scan():
    results = scan_library(GAME_ROOT)
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
    database.update_game(game_id, {"cover_name": name})
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
