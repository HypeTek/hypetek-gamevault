import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "server"))

from maintenance import create_backup, restore_backup, validate_backup


class MaintenanceTests(unittest.TestCase):
    def test_backup_excludes_secrets_and_restore_preserves_local_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config"
            config.mkdir()
            settings = {
                "server_name": "Before",
                "thegamesdb_api_key": "games-secret",
                "translator_api_key": "translator-secret",
            }
            (config / "mission-control-settings.json").write_text(json.dumps(settings), encoding="utf-8")
            backup = create_backup(config, "0.4.0", root / "backup.zip")
            with zipfile.ZipFile(backup) as archive:
                archived = json.loads(archive.read("mission-control-settings.json"))
                self.assertNotIn("thegamesdb_api_key", archived)
                self.assertNotIn("translator_api_key", archived)
                self.assertFalse(json.loads(archive.read("manifest.json"))["secrets_included"])
            archived["server_name"] = "Restored"
            replacement = root / "replacement.zip"
            with zipfile.ZipFile(backup) as source, zipfile.ZipFile(replacement, "w") as target:
                for entry in source.infolist():
                    payload = source.read(entry)
                    if entry.filename == "mission-control-settings.json":
                        payload = json.dumps(archived).encode()
                    target.writestr(entry, payload)
            restore_backup(replacement, config)
            restored = json.loads((config / "mission-control-settings.json").read_text(encoding="utf-8"))
            self.assertEqual(restored["server_name"], "Restored")
            self.assertEqual(restored["thegamesdb_api_key"], "games-secret")
            self.assertEqual(restored["translator_api_key"], "translator-secret")

    def test_unsafe_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../escape", b"no")
                output.writestr("manifest.json", json.dumps({"format": "hypetek-mission-control-backup", "format_version": 1}))
            with self.assertRaises(ValueError):
                validate_backup(archive)


if __name__ == "__main__":
    unittest.main()
