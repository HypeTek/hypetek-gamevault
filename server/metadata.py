from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


RAWG_API_HOST = "api.rawg.io"
RAWG_MEDIA_HOST = "media.rawg.io"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class MetadataError(RuntimeError):
    pass


def clean_game_title(value: str) -> str:
    title = str(value or "")
    title = re.sub(r"[\[\(].*?(fitgirl|repack|site|edition|release).*?[\]\)]", " ", title, flags=re.I)
    title = re.sub(r"\b(fitgirl(?:-repacks?)?|repack|reloaded|prophet|codex|gog)\b", " ", title, flags=re.I)
    title = re.sub(r"\b(site|incl(?:uding)?|dlc)\b", " ", title, flags=re.I)
    title = re.sub(r"[-_.]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip(" -_")
    return title or str(value or "").strip()


def _get_json(url: str, timeout: int = 12) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "HypeTek-Mission-Control/0.2.2"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code in {401, 403}:
            raise MetadataError("RAWG-API-Key wurde abgelehnt") from error
        if error.code == 429:
            raise MetadataError("RAWG-Anfragelimit erreicht; bitte später erneut versuchen") from error
        raise MetadataError(f"RAWG antwortete mit HTTP {error.code}") from error
    except (URLError, TimeoutError, ValueError) as error:
        raise MetadataError("RAWG ist derzeit nicht erreichbar") from error


def search_rawg(api_key: str, title: str, limit: int = 6) -> list[dict]:
    key = str(api_key or "").strip()
    if not key:
        raise MetadataError("In den Einstellungen ist kein RAWG-API-Key hinterlegt")
    query = clean_game_title(title)
    parameters = urlencode({"key": key, "search": query, "search_precise": "true", "page_size": min(10, max(1, limit))})
    payload = _get_json(f"https://{RAWG_API_HOST}/api/games?{parameters}")
    results = []
    for item in payload.get("results", []):
        image_url = item.get("background_image")
        game_id = item.get("id")
        slug = item.get("slug")
        if not image_url or not game_id or not slug:
            continue
        results.append({
            "provider": "rawg",
            "provider_id": str(game_id),
            "name": str(item.get("name") or query)[:160],
            "released": str(item.get("released") or "")[:10],
            "image_url": image_url,
            "source_url": f"https://rawg.io/games/{slug}",
        })
    return results[:limit]


def validate_rawg_key(api_key: str) -> None:
    key = str(api_key or "").strip()
    if not key:
        raise MetadataError("RAWG-API-Key ist leer")
    parameters = urlencode({"key": key, "page_size": 1})
    _get_json(f"https://{RAWG_API_HOST}/api/games?{parameters}")


def download_rawg_image(image_url: str, destination: Path) -> str:
    parsed = urlparse(str(image_url or ""))
    if parsed.scheme != "https" or parsed.hostname != RAWG_MEDIA_HOST:
        raise MetadataError("Ungültige RAWG-Bildadresse")
    request = Request(image_url, headers={"Accept": "image/*", "User-Agent": "HypeTek-Mission-Control/0.2.2"})
    try:
        with urlopen(request, timeout=20) as response:
            content_type = (response.headers.get_content_type() or "").lower()
            if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise MetadataError("RAWG lieferte keine unterstützte Bilddatei")
            data = response.read(MAX_IMAGE_BYTES + 1)
    except HTTPError as error:
        raise MetadataError(f"RAWG-Bildserver antwortete mit HTTP {error.code}") from error
    except (URLError, TimeoutError) as error:
        raise MetadataError("RAWG-Bild konnte nicht heruntergeladen werden") from error
    if len(data) > MAX_IMAGE_BYTES:
        raise MetadataError("RAWG-Bild ist größer als 8 MiB")
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
    is_jpeg = data.startswith(b"\xff\xd8\xff")
    is_png = data.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        raise MetadataError("RAWG-Bildsignatur ist ungültig")
    target = destination.with_suffix(extension)
    target.write_bytes(data)
    return target.name
