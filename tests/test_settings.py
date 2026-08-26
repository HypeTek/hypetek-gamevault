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
                "source_type": "server",
                "container_path": DEFAULT_GAME_ROOT,
                "windows_path": DEFAULT_WINDOWS_ROOT,
                "linux_path": "",
                "enabled": True,
            }])

    def test_windows_local_library_needs_only_a_windows_path(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            store = SettingsStore(path)
            settings = store.update({
                "libraries": [{
                    "id": "local-f",
                    "name": "Lokale F-Platte",
                    "source_type": "windows_local",
                    "container_path": "/libraries/should-not-survive",
                    "windows_path": "F:\\Games",
                    "linux_path": "/mnt/should-not-survive",
                    "enabled": True,
                }],
            })

            self.assertEqual(settings["libraries"], [{
                "id": "local-f",
                "name": "Lokale F-Platte",
                "source_type": "windows_local",
                "container_path": "",
                "windows_path": "F:\\Games",
                "linux_path": "",
                "enabled": True,
            }])


if __name__ == "__main__":
    unittest.main()
