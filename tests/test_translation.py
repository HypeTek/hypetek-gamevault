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

    def test_mixed_paragraphs_are_translated_separately(self):
        calls = []
        original = translation._json_request

        def fake_request(url, payload=None, timeout=25):
            calls.append((url, payload))
            return {"translatedText": f"DE: {payload['q']}"}

        translation._json_request = fake_request
        try:
            result = translation.translate_text(
                "http://translator:5000",
                "English paragraph.\n\nRequisiti di sistema.",
                "de",
            )
        finally:
            translation._json_request = original
        self.assertEqual(len(calls), 2)
        self.assertEqual(result, "DE: English paragraph.\n\nDE: Requisiti di sistema.")

    def test_validation_returns_normalized_available_language_codes(self):
        original = translation._json_request
        translation._json_request = lambda *args, **kwargs: [
            {"code": "ru", "name": "Russian"},
            {"code": "DE", "name": "German"},
            {"code": "en", "name": "English"},
        ]
        try:
            codes = translation.validate_translator("http://translator:5000")
        finally:
            translation._json_request = original
        self.assertEqual(codes, ["de", "en", "ru"])


if __name__ == "__main__":
    unittest.main()
