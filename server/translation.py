from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class TranslationError(RuntimeError):
    pass


def normalize_translator_url(value: str) -> str:
    url = str(value or "").strip().rstrip("/")
    if not url:
        return ""
    parsed = urlparse(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise TranslationError("Ungültige Translator-Adresse")
    return url


def _json_request(url: str, payload: dict | None = None, timeout: int = 25):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="GET" if payload is None else "POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HypeTek-Mission-Control/0.3.2",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code in {401, 403}:
            raise TranslationError("Translator-API-Key wurde abgelehnt") from error
        raise TranslationError(f"Translator antwortete mit HTTP {error.code}") from error
    except (URLError, TimeoutError, ValueError) as error:
        raise TranslationError("Translator ist derzeit nicht erreichbar") from error


def validate_translator(endpoint: str, api_key: str = "") -> None:
    base = normalize_translator_url(endpoint)
    if not base:
        raise TranslationError("Translator-Adresse ist leer")
    languages = _json_request(f"{base}/languages", timeout=12)
    if not isinstance(languages, list):
        raise TranslationError("Translator lieferte keine gültige Sprachliste")


def translate_text(
    endpoint: str,
    text: str,
    target_language: str,
    api_key: str = "",
) -> str:
    base = normalize_translator_url(endpoint)
    source_text = str(text or "").strip()
    target = str(target_language or "de").strip().casefold()
    if not source_text:
        return ""
    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", target):
        raise TranslationError("Ungültige Zielsprache")

    # TheGamesDB overviews can contain English prose and, in the same entry,
    # requirements copied from another language. Detect each paragraph rather
    # than treating the whole mixed document as a single source language.
    parts = re.split(r"(\n\s*\n)", source_text)
    translated: list[str] = []
    for part in parts:
        if not part.strip() or re.fullmatch(r"\n\s*\n", part):
            translated.append(part)
            continue
        payload = {
            "q": part.strip(),
            "source": "auto",
            "target": target,
            "format": "text",
        }
        if api_key:
            payload["api_key"] = api_key
        result = _json_request(f"{base}/translate", payload=payload)
        value = result.get("translatedText") if isinstance(result, dict) else None
        if not isinstance(value, str) or not value.strip():
            raise TranslationError("Translator lieferte keinen übersetzten Text")
        translated.append(value.strip())
    return "".join(translated).strip()
