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
            "User-Agent": "HypeTek-Mission-Control/0.3.16",
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


def validate_translator(endpoint: str, api_key: str = "") -> list[str]:
    base = normalize_translator_url(endpoint)
    if not base:
        raise TranslationError("Translator-Adresse ist leer")
    languages = _json_request(f"{base}/languages", timeout=12)
    if not isinstance(languages, list):
        raise TranslationError("Translator lieferte keine gültige Sprachliste")
    codes = sorted(
        {
            str(item.get("code") or "").strip().casefold()
            for item in languages
            if isinstance(item, dict) and item.get("code")
        }
    )
    if not codes:
        raise TranslationError("Translator meldete keine verfügbaren Sprachen")
    return codes


def _detected_languages(base: str, text: str, api_key: str = "") -> list[str]:
    payload = {"q": text}
    if api_key:
        payload["api_key"] = api_key
    result = _json_request(f"{base}/detect", payload=payload)
    if not isinstance(result, list):
        return []
    ranked = sorted(
        (item for item in result if isinstance(item, dict)),
        key=lambda item: float(item.get("confidence") or 0),
        reverse=True,
    )
    return [
        str(item.get("language") or "").strip().casefold()
        for item in ranked
        if item.get("language")
    ]


def _translate_fragment(base: str, text: str, source: str, target: str, api_key: str) -> str:
    payload = {"q": text, "source": source, "target": target, "format": "text"}
    if api_key:
        payload["api_key"] = api_key
    result = _json_request(f"{base}/translate", payload=payload)
    value = result.get("translatedText") if isinstance(result, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise TranslationError("Translator lieferte keinen übersetzten Text")
    return value.strip()


def translate_text(
    endpoint: str,
    text: str,
    target_language: str,
    api_key: str = "",
    available_languages: list[str] | None = None,
) -> str:
    base = normalize_translator_url(endpoint)
    source_text = str(text or "").strip()
    target = str(target_language or "de").strip().casefold()
    if not source_text:
        return ""
    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", target):
        raise TranslationError("Ungültige Zielsprache")

    available = {
        str(code).strip().casefold()
        for code in (available_languages or [])
        if re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", str(code).strip().casefold())
    }

    # TheGamesDB descriptions can contain any number of source languages, even
    # within one line. Translate logical fragments independently and repeat
    # detection after every pass. Once the dominant language was translated,
    # a previously hidden second language can be detected on the next pass.
    # No source language is hard-coded here; the Translator decides dynamically.
    parts = re.split(r"(\r?\n+)", source_text)
    translated: list[str] = []
    for part in parts:
        if not part.strip() or re.fullmatch(r"\r?\n+", part):
            translated.append(part)
            continue
        # Pure numbers and separators do not need language detection and can
        # make short-text detectors unreliable.
        if not any(character.isalpha() for character in part) or re.fullmatch(
            r"[\d\s.,:/()+\-x×%]+(?:[kmgt]i?b)?", part.strip(), re.IGNORECASE
        ):
            translated.append(part)
            continue
        fragments = re.split(r"([:;.!?]+\s*)", part.strip())
        line: list[str] = []
        for fragment in fragments:
            if not fragment or not any(character.isalpha() for character in fragment):
                line.append(fragment)
                continue
            current = fragment.strip()
            for _ in range(4):
                detected = _detected_languages(base, current, api_key)
                candidates = [code for code in detected if code != target and (not available or code in available)]
                if not candidates:
                    break
                updated = _translate_fragment(base, current, candidates[0], target, api_key)
                if updated.casefold() == current.casefold():
                    break
                current = updated
            line.append(current)
        translated.append("".join(line).strip())
    return "".join(translated).strip()
