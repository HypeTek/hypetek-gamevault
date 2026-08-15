from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


RAWG_API_HOST = "api.rawg.io"
RAWG_MEDIA_HOST = "media.rawg.io"
THEGAMESDB_API_HOST = "api.thegamesdb.net"
THEGAMESDB_MEDIA_HOST = "cdn.thegamesdb.net"
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


def suggest_game_title(value: str) -> str:
    return clean_game_title(value)


def game_title_search_queries(value: str) -> list[str]:
    """Build provider queries without maintaining a franchise alias table.

    A short leading acronym is kept for the first attempt. If the provider has
    no exact result, the distinctive remainder is tried as a discovery query;
    the user still selects the authoritative catalogue title.
    """
    title = suggest_game_title(value)
    queries = [title]
    words = title.split()
    if len(words) > 1 and re.fullmatch(r"[A-Z0-9]{2,5}", words[0]):
        remainder = " ".join(words[1:]).strip()
        if len(remainder) >= 3:
            queries.append(remainder)
    return list(dict.fromkeys(queries))


def _get_json(url: str, timeout: int = 12) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "HypeTek-Mission-Control/0.3.14"})
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
    query = suggest_game_title(title)
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


def _get_thegamesdb_json(url: str, timeout: int = 15) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "HypeTek-Mission-Control/0.3.14"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        if error.code == 403:
            raise MetadataError("TheGamesDB-API-Key wurde abgelehnt oder das Anfragelimit ist erreicht") from error
        if error.code == 429:
            raise MetadataError("TheGamesDB-Anfragelimit erreicht; bitte später erneut versuchen") from error
        raise MetadataError(f"TheGamesDB antwortete mit HTTP {error.code}") from error
    except (URLError, TimeoutError, ValueError) as error:
        raise MetadataError("TheGamesDB ist derzeit nicht erreichbar") from error
    if int(payload.get("code", 200)) >= 400:
        raise MetadataError(str(payload.get("status") or "TheGamesDB-Anfrage fehlgeschlagen"))
    return payload


def search_thegamesdb(api_key: str, title: str, limit: int = 8) -> list[dict]:
    key = str(api_key or "").strip()
    if not key:
        raise MetadataError("In den Einstellungen ist kein TheGamesDB-API-Key hinterlegt")
    query = suggest_game_title(title)
    payload = None
    for candidate_query in game_title_search_queries(title):
        parameters = urlencode({
            "apikey": key,
            "name": candidate_query,
            "fields": "platform,overview,rating,players,coop",
            "include": "boxart,platform",
        })
        candidate_payload = _get_thegamesdb_json(
            f"https://{THEGAMESDB_API_HOST}/v1.1/Games/ByGameName?{parameters}"
        )
        payload = candidate_payload
        if ((candidate_payload.get("data") or {}).get("games") or []):
            query = candidate_query
            break
    payload = payload or {}
    include = payload.get("include") or {}
    boxart = (include.get("boxart") or {})
    boxart_data = boxart.get("data") or {}
    base_urls = boxart.get("base_url") or {}
    image_base = str(base_urls.get("original") or "")
    parsed_image_base = urlparse(image_base)
    if parsed_image_base.scheme != "https" or parsed_image_base.hostname != THEGAMESDB_MEDIA_HOST:
        image_base = "https://cdn.thegamesdb.net/images/original/"
    platform_data = ((include.get("platform") or {}).get("data") or {})
    results = []
    for item in (payload.get("data") or {}).get("games") or []:
        game_id = str(item.get("id") or "")
        if not game_id:
            continue
        images = boxart_data.get(game_id) or boxart_data.get(int(game_id)) or []
        front = next(
            (image for image in images if image.get("type") == "boxart" and image.get("side") == "front"),
            next((image for image in images if image.get("type") == "boxart"), None),
        )
        if not front or not front.get("filename"):
            continue
        platform_id = str(item.get("platform") or "")
        platform = platform_data.get(platform_id) or {}
        if not platform and platform_id.isdigit():
            platform = platform_data.get(int(platform_id)) or {}
        results.append({
            "provider": "thegamesdb",
            "provider_id": game_id,
            "name": str(item.get("game_title") or query)[:160],
            "released": str(item.get("release_date") or "")[:10],
            "platform": str(platform.get("name") or "")[:80],
            "overview": str(item.get("overview") or "")[:12000],
            "rating": str(item.get("rating") or "")[:80],
            "players": str(item.get("players") or "")[:40],
            "coop": str(item.get("coop") or "")[:40],
            "image_url": image_base.rstrip("/") + "/" + str(front["filename"]).lstrip("/"),
            "source_url": f"https://thegamesdb.net/game.php?id={game_id}",
        })
    def platform_priority(result: dict) -> tuple[int, str, str]:
        platform_name = str(result.get("platform") or "").casefold()
        priority = 0 if platform_name in {"pc", "windows", "dos"} else 1
        return priority, str(result.get("name") or "").casefold(), str(result.get("released") or "")

    results.sort(key=platform_priority)
    return results[: max(1, min(12, limit))]


def validate_thegamesdb_key(api_key: str) -> None:
    key = str(api_key or "").strip()
    if not key:
        raise MetadataError("TheGamesDB-API-Key ist leer")
    parameters = urlencode({"apikey": key, "name": "Sonic the Hedgehog"})
    _get_thegamesdb_json(
        f"https://{THEGAMESDB_API_HOST}/v1.1/Games/ByGameName?{parameters}"
    )


def fetch_thegamesdb_image(image_url: str) -> tuple[bytes, str]:
    parsed = urlparse(str(image_url or ""))
    if parsed.scheme != "https" or parsed.hostname != THEGAMESDB_MEDIA_HOST:
        raise MetadataError("Ungültige TheGamesDB-Bildadresse")
    request = Request(image_url, headers={"Accept": "image/*", "User-Agent": "HypeTek-Mission-Control/0.3.14"})
    try:
        with urlopen(request, timeout=20) as response:
            content_type = (response.headers.get_content_type() or "").lower()
            if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise MetadataError("TheGamesDB lieferte keine unterstützte Bilddatei")
            data = response.read(MAX_IMAGE_BYTES + 1)
    except HTTPError as error:
        raise MetadataError(f"TheGamesDB-Bildserver antwortete mit HTTP {error.code}") from error
    except (URLError, TimeoutError) as error:
        raise MetadataError("TheGamesDB-Bild konnte nicht heruntergeladen werden") from error
    if len(data) > MAX_IMAGE_BYTES:
        raise MetadataError("TheGamesDB-Bild ist größer als 8 MiB")
    is_jpeg = data.startswith(b"\xff\xd8\xff")
    is_png = data.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        raise MetadataError("TheGamesDB-Bildsignatur ist ungültig")
    return data, content_type


def download_thegamesdb_image(image_url: str, destination: Path) -> str:
    data, content_type = fetch_thegamesdb_image(image_url)
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
    target = destination.with_suffix(extension)
    target.write_bytes(data)
    return target.name


def download_rawg_image(image_url: str, destination: Path) -> str:
    parsed = urlparse(str(image_url or ""))
    if parsed.scheme != "https" or parsed.hostname != RAWG_MEDIA_HOST:
        raise MetadataError("Ungültige RAWG-Bildadresse")
    request = Request(image_url, headers={"Accept": "image/*", "User-Agent": "HypeTek-Mission-Control/0.3.14"})
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
