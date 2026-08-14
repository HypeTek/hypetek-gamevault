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
        javascript = (ROOT / "server" / "static" / "app.js").read_text(encoding="utf-8")
        translations = (ROOT / "server" / "static" / "i18n.js").read_text(encoding="utf-8")
        translations = (ROOT / "server" / "static" / "i18n.js").read_text(encoding="utf-8")
        template = (ROOT / "server" / "templates" / "index.html").read_text(encoding="utf-8")

        installer_version = re.search(
            r'^#define MyAppVersion "([^"]+)"$', installer, re.MULTILINE
        )
        self.assertIsNotNone(installer_version)
        self.assertEqual(installer_version.group(1), version)
        self.assertIn(f'VersionInfoVersion={version}.0', installer)
        self.assertIn(f'org.opencontainers.image.version="{version}"', dockerfile)
        self.assertIn(f"## {version}", changelog)
        self.assertIn(f"Version {version} aktualisieren", javascript)
        self.assertIn('id="appVersion"', template)
        self.assertIn('id="pagination"', template)
        self.assertIn('id="viewListButton"', template)
        self.assertIn('id="designProfilesDialog"', template)
        self.assertIn('id="designProfilePreview"', template)
        self.assertIn('value="favorites"', template)
        self.assertIn('data-profile-color="energy_start"', template)
        self.assertIn('id="designProfileSaveStatus"', template)
        self.assertIn('id="settingUiLanguage"', template)
        self.assertIn('id="designProfilesBackButton"', template)
        self.assertIn('id="lcarsSystemClock"', template)
        self.assertNotIn('onclick="probeWindowsAgent()"', template)
        self.assertIn("filename='app.js', v=asset_version", template)
        self.assertIn("SMB-Netzlaufwerk zuerst", template)
        self.assertIn('ru: {', translations)
        self.assertTrue(translations.startswith("(() => {"))
        self.assertTrue(translations.rstrip().endswith("})();"))
        self.assertIn('applyUiLanguage', translations)
        self.assertIn('addEventListener("click", probeWindowsAgent)', javascript)
        self.assertIn('applySettings(settings);\n    render();', javascript)
        self.assertIn('"stats.entries": "Entries"', translations)
        self.assertIn('"game.install": "Установить"', translations)
        self.assertIn('if (isNew) applySettings(await api(', javascript)
        self.assertIn("Michael Härtwig", template)
        self.assertIn('class="floating-brand-logo"', template)
        self.assertLess(template.index('class="floating-brand-logo"'), template.index('class="topbar"'))
        self.assertTrue((ROOT / "server" / "design_profiles.py").is_file())
        license_text = (ROOT / "LICENSE.md").read_text(encoding="utf-8")
        self.assertIn("Source-Available Notice", license_text)
        self.assertIn("Michael Härtwig / HypeTek", license_text)
        self.assertIn("No open-source license is granted", license_text)
        self.assertIn(
            "CreateInputDirPage",
            (ROOT / "windows-installer" / "MissionControlAgent.iss").read_text(encoding="utf-8"),
        )
        self.assertIn("Verbinde das SMB-Netzlaufwerk zuerst", installer)

        workflow = (ROOT / ".github" / "workflows" / "container.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('version=$(tr -d', workflow)
        self.assertIn('gh release upload $tag', workflow)
        self.assertIn('catch {', workflow)
        self.assertIn('if (-not $releaseExists)', workflow)
        self.assertIn('type=raw,value=${{ steps.version.outputs.version }}', workflow)

    def test_line_endings_are_declared_for_cross_platform_builds(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("*.py text eol=lf", attributes)
        self.assertIn("*.ps1 text eol=crlf", attributes)
        self.assertIn("*.iss text eol=crlf", attributes)


if __name__ == "__main__":
    unittest.main()
