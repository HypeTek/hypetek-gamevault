import json
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "server"))

import translation


class TranslationTests(unittest.TestCase):
    def test_url_validation_accepts_local_service_and_rejects_credentials(self):
        self.assertEqual(
            translation.normalize_translator_url("http://translator:5000/"),
            "http://translator:5000",
        )
        with self.assertRaises(translation.TranslationError):
            translation.normalize_translator_url("http://user:pass@translator:5000")

    def test_mixed_languages_are_detected_dynamically_and_keep_line_breaks(self):
        calls = []
        original = translation._json_request

        def fake_request(url, payload=None, timeout=25):
            calls.append((url, payload))
            if url.endswith("/detect"):
                text = payload["q"]
                language = "de" if text.startswith("DE:") else ("it" if "Requisiti" in text else "en")
                return [{"language": language, "confidence": 99}]
            return {"translatedText": f"DE: {payload['q']}"}

        translation._json_request = fake_request
        try:
            result = translation.translate_text(
                "http://translator:5000",
                "English paragraph.\nRequisiti di sistema.\n\n64 GB\n---",
                "de",
                available_languages=["de", "en", "it"],
            )
        finally:
            translation._json_request = original
        self.assertIn("DE: English paragraph", result)
        self.assertIn("DE: Requisiti di sistema", result)
        self.assertIn("\n\n64 GB\n---", result)
        sources = [payload["source"] for url, payload in calls if url.endswith("/translate")]
        self.assertIn("en", sources)
        self.assertIn("it", sources)

    def test_validation_returns_normalized_available_language_codes(self):
        original = translation._json_request
        translation._json_request = lambda *args, **kwargs: [
            {"code": "ru", "name": "Russian"},
            {"code": "DE", "name": "German"},
            {"code": "en", "name": "English"},
            {"code": "it", "name": "Italian"},
        ]
        try:
            codes = translation.validate_translator("http://translator:5000")
        finally:
            translation._json_request = original
        self.assertEqual(codes, ["de", "en", "it", "ru"])


    def test_content_targets_include_beta_languages_when_english_is_available(self):
        self.assertEqual(
            translation.content_target_languages(["de", "en", "ar", "zh"]),
            ["de", "en", "ar", "zh", "tlh", "sjn"],
        )
        self.assertEqual(translation.content_target_languages(["de", "ar"]), ["de", "ar"])

    def test_beta_klingon_and_sindarin_render_from_english_intermediate(self):
        original = translation._json_request

        def fake_request(url, payload=None, timeout=25):
            if url.endswith("/detect"):
                return [{"language": "en", "confidence": 99}]
            return {"translatedText": payload["q"]}

        translation._json_request = fake_request
        try:
            klingon = translation.translate_text(
                "http://translator:5000",
                "A new game and world battle.",
                "tlh",
                available_languages=["de", "en", "ar", "zh"],
            )
            sindarin = translation.translate_text(
                "http://translator:5000",
                "A dark world and forest battle.",
                "sjn",
                available_languages=["de", "en", "ar", "zh"],
            )
        finally:
            translation._json_request = original

        self.assertIn("Quj", klingon)
        self.assertIn("qo'", klingon)
        self.assertIn("may'", klingon)
        self.assertIn("amar", sindarin)
        self.assertIn("taur", sindarin)
        self.assertIn("dagor", sindarin)

    def test_source_languages_are_not_hard_coded(self):
        calls = []
        original = translation._json_request

        def fake_request(url, payload=None, timeout=25):
            calls.append(payload)
            if url.endswith("/detect"):
                language = "de" if payload["q"].startswith("DE:") else ("es" if "Requisitos" in payload["q"] else "fr")
                return [{"language": language, "confidence": 95}]
            return {"translatedText": f"DE: {payload['q']}"}

        translation._json_request = fake_request
        try:
            translation.translate_text(
                "http://translator:5000",
                "Requisitos del sistema\nConfiguration recommandée",
                "de",
                available_languages=["de", "es", "fr"],
            )
        finally:
            translation._json_request = original

        sources = [call["source"] for call in calls if call and "source" in call]
        self.assertEqual(sources, ["es", "fr"])


if __name__ == "__main__":
    unittest.main()
