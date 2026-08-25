import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "server"))
from settings import DEFAULT_GAME_ROOT, DEFAULT_WINDOWS_ROOT, SettingsStore


class SettingsMigrationTests(unittest.TestCase):
    def test_single_library_settings_are_upgraded_without_renaming_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            path.write_text(
                json.dumps({"library_name": "TrueTitan Archive", "theme": "midnight"}),
                encoding="utf-8",
            )
            settings = SettingsStore(path).load()
            self.assertEqual(settings["theme"], "midnight")
            self.assertEqual(settings["libraries"], [{
                "id": "primary",
                "name": "TrueTitan Archive",
                "container_path": DEFAULT_GAME_ROOT,
                "windows_path": DEFAULT_WINDOWS_ROOT,
                "linux_path": "",
                "enabled": True,
            }])


if __name__ == "__main__":
    unittest.main()
