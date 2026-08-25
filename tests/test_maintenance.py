import json
import errno
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "server"))

from maintenance import create_backup, inspect_backup, restore_backup, validate_backup


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
            backup = create_backup(config, "0.5.0", root / "backup.zip")
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

    def test_restore_does_not_replace_files_across_filesystems(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config"
            config.mkdir()
            (config / "mission-control-settings.json").write_text(
                json.dumps({"server_name": "Before"}), encoding="utf-8"
            )
            (config / "covers").mkdir()
            (config / "covers" / "example.webp").write_bytes(b"restored-cover")
            backup = create_backup(config, "0.5.0", root / "backup.zip")
            (config / "covers" / "example.webp").write_bytes(b"changed-cover")
            real_replace = os.replace

            def reject_cross_device(source, target):
                source_path = Path(source)
                target_path = Path(target)
                if source_path.parent != target_path.parent:
                    raise OSError(errno.EXDEV, "Invalid cross-device link")
                return real_replace(source, target)

            with patch("maintenance.os.replace", side_effect=reject_cross_device):
                restore_backup(backup, config)

            restored = json.loads((config / "mission-control-settings.json").read_text(encoding="utf-8"))
            self.assertEqual(restored["server_name"], "Before")
            self.assertEqual((config / "covers" / "example.webp").read_bytes(), b"restored-cover")

    def test_backup_preview_contains_safe_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config"
            (config / "covers").mkdir(parents=True)
            (config / "backgrounds").mkdir()
            (config / "mission-control-settings.json").write_text("{}", encoding="utf-8")
            (config / "covers" / "one.webp").write_bytes(b"cover")
            (config / "backgrounds" / "one.webp").write_bytes(b"background")
            backup = create_backup(config, "0.5.0", root / "backup.zip")
            summary = inspect_backup(backup)
            self.assertEqual(summary["application_version"], "0.5.0")
            self.assertEqual(summary["cover_count"], 1)
            self.assertEqual(summary["background_count"], 1)
            self.assertGreaterEqual(summary["file_count"], 3)
            self.assertFalse(summary["secrets_included"])


if __name__ == "__main__":
    unittest.main()
