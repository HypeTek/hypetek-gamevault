import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
