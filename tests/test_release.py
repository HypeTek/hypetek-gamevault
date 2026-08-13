import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_release_versions_are_consistent(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        installer = (ROOT / "windows-installer" / "MissionControlAgent.iss").read_text(
            encoding="utf-8"
        )
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        installer_version = re.search(
            r'^#define MyAppVersion "([^"]+)"$', installer, re.MULTILINE
        )
        self.assertIsNotNone(installer_version)
        self.assertEqual(installer_version.group(1), version)
        self.assertIn(f'VersionInfoVersion={version}.0', installer)
        self.assertIn(f'org.opencontainers.image.version="{version}"', dockerfile)
        self.assertIn(f"## {version}", changelog)

    def test_line_endings_are_declared_for_cross_platform_builds(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("*.py text eol=lf", attributes)
        self.assertIn("*.ps1 text eol=crlf", attributes)
        self.assertIn("*.iss text eol=crlf", attributes)


if __name__ == "__main__":
    unittest.main()
