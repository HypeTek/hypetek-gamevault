import tempfile
import unittest
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "server"))
from scanner import scan_library


class ScannerTests(unittest.TestCase):
    def test_classification_and_redist_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            direct = root / "Direct Game"
            direct.mkdir()
            (direct / "setup.exe").write_bytes(b"MZ")
            (direct / "data.bin").write_bytes(b"data")

            iso = root / "ISO Game"
            iso.mkdir()
            (iso / "game.iso").write_bytes(b"iso")

            manual = root / "Manual Game"
            manual.mkdir()
            (manual / "game.cue").write_text('FILE "game.bin" BINARY')
            (manual / "game.bin").write_bytes(b"bin")

            redist = root / "Only Redist"
            (redist / "DirectX").mkdir(parents=True)
            (redist / "DirectX" / "setup.exe").write_bytes(b"MZ")

            result = {item.relative_path: item for item in scan_library(root)}
            self.assertEqual(result["Direct Game"].detected_type, "direct_setup")
            self.assertEqual(result["Direct Game"].launcher_relative_path, "Direct Game/setup.exe")
            self.assertEqual(result["ISO Game"].detected_type, "iso")
            self.assertEqual(result["Manual Game"].detected_type, "manual_image")
            self.assertEqual(result["Only Redist"].detected_type, "manual")

    def test_single_iso_and_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Game.iso").write_bytes(b"iso")
            (root / "Old Game.rar").write_bytes(b"rar")
            result = {item.relative_path: item for item in scan_library(root)}
            self.assertEqual(result["Game.iso"].detected_type, "iso")
            self.assertEqual(result["Old Game.rar"].detected_type, "archive")

    def test_explicit_top_level_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            excluded = root / "hadmin"
            excluded.mkdir()
            (excluded / "private.exe").write_bytes(b"MZ")
            included = root / "Game"
            included.mkdir()
            (included / "setup.exe").write_bytes(b"MZ")
            result = scan_library(root, {"HADMIN"})
            self.assertEqual([item.relative_path for item in result], ["Game"])

    def test_ids_are_scoped_to_library(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "Same Game"
            game.mkdir()
            (game / "setup.exe").write_bytes(b"MZ")
            primary = scan_library(root, library_id="primary")[0]
            archive = scan_library(root, library_id="archive")[0]
            self.assertEqual(primary.relative_path, archive.relative_path)
            self.assertNotEqual(primary.game_id, archive.game_id)
            self.assertEqual(
                primary.game_id,
                hashlib.sha256(b"Same Game").hexdigest()[:20],
                "the primary library must keep pre-0.5 game IDs",
            )


if __name__ == "__main__":
    unittest.main()
