import json
import tempfile
import unittest
from pathlib import Path

from server.design_profiles import DesignProfileStore


class DesignProfileStoreTests(unittest.TestCase):
    def test_corrupt_store_falls_back_and_atomic_save_keeps_only_custom_profiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "designs.json"
            path.write_text("{broken", encoding="utf-8")
            store = DesignProfileStore(path)
            self.assertEqual(store.load()["active"], "mission")
            mission = store.load()["profiles"]["mission"]
            custom = store.create({**mission, "name": "Mein Profil", "builtin": False})
            rendered = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(list(rendered["profiles"]), [custom["id"]])
            self.assertNotIn("mission", rendered["profiles"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_legacy_and_profile_background_names_are_validated(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = DesignProfileStore(Path(temporary) / "designs.json")
            mission = store.load()["profiles"]["mission"]
            legacy = {**mission, "name": "Legacy Copy", "background_name": "custom-background.webp"}
            self.assertEqual(store.create(legacy)["background_name"], "custom-background.webp")
            invalid = {**mission, "name": "Unsafe", "background_name": "../outside.png"}
            with self.assertRaises(ValueError):
                store.create(invalid)


if __name__ == "__main__":
    unittest.main()
