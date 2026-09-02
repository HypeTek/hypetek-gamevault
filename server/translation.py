from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class TranslationError(RuntimeError):
    pass


EXPERIMENTAL_CONTENT_LANGUAGES = {"tlh", "sjn"}
CONTENT_LANGUAGE_ORDER = (
    "de", "en", "fr", "it", "nl", "pl", "pt", "ru", "es", "tr", "ar", "zh", "tlh", "sjn"
)


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
            "User-Agent": "HypeTek-Mission-Control/0.9.0-rc.5",
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


def content_target_languages(native_languages: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    """Return user-selectable content languages for the connected translator.

    LibreTranslate provides the real models. Klingon and Sindarin are deliberately
    marked as Beta and are generated locally from an English intermediate text;
    they are only offered when the translator can supply English.
    """
    native = {
        str(code).strip().casefold()
        for code in native_languages
        if re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", str(code).strip().casefold())
    }
    selectable = set(native)
    if "en" in native:
        selectable.update(EXPERIMENTAL_CONTENT_LANGUAGES)
    ordered = [code for code in CONTENT_LANGUAGE_ORDER if code in selectable]
    ordered.extend(sorted(selectable.difference(ordered)))
    return ordered


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


def _translate_standard_text(
    base: str,
    source_text: str,
    target: str,
    api_key: str,
    available: set[str],
) -> str:
    # TheGamesDB descriptions can contain any number of source languages, even
    # within one line. Translate logical fragments independently and repeat
    # detection after every pass. Once the dominant language was translated,
    # a previously hidden second language can be detected on the next pass.
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


_KLINGON_WORDS = {
    "game": "Quj", "games": "Qujmey", "player": "QujwI'", "players": "QujwI'pu'",
    "world": "qo'", "worlds": "qo'mey", "story": "lut", "stories": "lutmey",
    "mission": "Qu'", "missions": "Qu'mey", "battle": "may'", "battles": "may'mey",
    "war": "veS", "enemy": "jagh", "enemies": "jaghpu'", "friend": "jup", "friends": "jupmey",
    "weapon": "nuH", "weapons": "nuHmey", "ship": "Duj", "ships": "Dujmey",
    "power": "HoS", "honor": "batlh", "victory": "yay", "death": "Hegh", "life": "yIn",
    "fight": "Suv", "fights": "Suv", "fighting": "Suv", "attack": "HIv", "attacks": "HIv",
    "defend": "Hub", "defense": "Hub", "discover": "tu'", "explore": "nej", "explores": "nej",
    "open": "poS", "dark": "Hurgh", "light": "wov", "strong": "HoSghaj", "new": "chu'",
    "old": "ngo'", "great": "Dun", "small": "mach", "large": "tIn", "city": "veng",
    "cities": "vengmey", "planet": "yuQ", "planets": "yuQmey", "space": "logh",
    "character": "nuv", "characters": "nuvpu'", "hero": "SuvwI'", "heroes": "SuvwI'pu'",
    "action": "vang", "adventure": "Qob", "adventures": "Qobmey", "strategy": "Dup",
    "survival": "yIntaH", "team": "ghom", "teams": "ghommey", "campaign": "Qu'mey",
    "online": "rar", "single": "wa'", "multiple": "law'", "multiplayer": "QujwI'pu' law'",
    "with": "tlhej", "without": "Hutlh", "and": "'ej", "or": "ghap", "from": "vo'",
    "for": "vaD", "in": "Daq", "on": "Daq", "through": "vegh", "against": "qaD",
    "you": "SoH", "your": "lIj", "yourself": "SoH'e'", "we": "maH", "our": "maj",
    "they": "chaH", "their": "chaj", "it": "'oH", "is": "'oH", "are": "bIH",
    "must": "nIS", "can": "laH", "will": "-", "the": "", "a": "", "an": "",
}

_SINDARIN_WORDS = {
    "world": "amar", "worlds": "emyr", "friend": "mellon", "friends": "mellyn",
    "king": "aran", "queen": "bereth", "star": "gil", "stars": "giliath", "moon": "ithil",
    "sun": "anor", "dark": "morn", "darkness": "dû", "light": "calad", "war": "dagor",
    "battle": "dagor", "battles": "degyr", "sword": "megil", "swords": "megilath",
    "forest": "taur", "forests": "eryn", "mountain": "orod", "mountains": "ered",
    "city": "minas", "cities": "minas", "river": "duin", "sea": "gaear", "land": "dor",
    "lands": "dôr", "road": "men", "path": "râd", "paths": "raid", "gate": "annon",
    "gates": "ennyn", "tower": "barad", "towers": "beraid", "shadow": "gwath",
    "fire": "naur", "water": "nen", "earth": "ceven", "air": "gwaew", "tree": "galadh",
    "trees": "gelaidh", "stone": "gond", "stones": "gondrim", "hero": "thalion",
    "heroes": "thelyn", "enemy": "coth", "enemies": "cothrim", "story": "pennas",
    "stories": "pennas", "song": "linnod", "songs": "lind", "new": "cîr", "old": "iaur",
    "great": "beleg", "small": "pîn", "beautiful": "bain", "hidden": "dolen", "open": "edro",
    "power": "tûr", "victory": "tûr", "death": "gurth", "life": "cuil", "heart": "gûr",
    "with": "ah", "without": "ú", "and": "a", "or": "egor", "from": "o", "to": "na",
    "in": "mi", "on": "or", "through": "trî", "against": "dan", "the": "i", "a": "min",
    "an": "min", "you": "le", "your": "lín", "we": "me", "our": "mín",
}


def _preserve_word_case(original: str, replacement: str) -> str:
    if not replacement:
        return ""
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper() and replacement[:1].isalpha():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _experimental_lexical_render(text: str, target: str) -> str:
    words = _KLINGON_WORDS if target == "tlh" else _SINDARIN_WORDS
    pieces = re.split(r"([A-Za-z]+(?:'[A-Za-z]+)?)", text)
    rendered: list[str] = []
    for piece in pieces:
        if not piece or not re.fullmatch(r"[A-Za-z]+(?:'[A-Za-z]+)?", piece):
            rendered.append(piece)
            continue
        replacement = words.get(piece.casefold())
        if replacement is None:
            # Beta packs deliberately keep unknown proper names and technical
            # vocabulary intact instead of fabricating a false canonical word.
            rendered.append(piece)
        else:
            rendered.append(_preserve_word_case(piece, replacement))
    value = "".join(rendered)
    value = re.sub(r"[ \t]{2,}", " ", value)
    value = re.sub(r" +([,.;:!?])", r"\1", value)
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

    if target in EXPERIMENTAL_CONTENT_LANGUAGES:
        if available and "en" not in available:
            raise TranslationError("Die Beta-Übersetzung benötigt das englische Translator-Modell")
        english = _translate_standard_text(base, source_text, "en", api_key, available)
        return _experimental_lexical_render(english, target)

    return _translate_standard_text(base, source_text, target, api_key, available)
