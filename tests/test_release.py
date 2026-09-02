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
        stylesheet = (ROOT / "server" / "static" / "app.css").read_text(encoding="utf-8")
        translations = (ROOT / "server" / "static" / "i18n.js").read_text(encoding="utf-8")
        template = (ROOT / "server" / "templates" / "index.html").read_text(encoding="utf-8")

        installer_version = re.search(
            r'^#define MyAppVersion "([^"]+)"$', installer, re.MULTILINE
        )
        self.assertIsNotNone(installer_version)
        self.assertEqual(installer_version.group(1), version)
        numeric_version = version.split('-', 1)[0]
        self.assertIn(f'VersionInfoVersion={numeric_version}.0', installer)
        self.assertIn(f'org.opencontainers.image.version="{version}"', dockerfile)
        self.assertIn(f"## {version}", changelog)
        self.assertIn(f"Version {version} aktualisieren", translations)
        self.assertIn('id="appVersion"', template)
        self.assertIn('id="pagination"', template)
        self.assertIn('id="viewListButton"', template)
        self.assertIn('id="designProfilesDialog"', template)
        self.assertIn('id="designProfilePreview"', template)
        self.assertIn('value="favorites"', template)
        self.assertIn('data-profile-color="energy_start"', template)
        self.assertIn('id="designProfileSaveStatus"', template)
        self.assertIn('id="settingUiLanguage"', template)
        self.assertIn('id="settingMotionPreference"', template)
        self.assertIn('id="librarySettingsRows"', template)
        self.assertIn('id="libraryTypeDialog"', template)
        self.assertIn('id="addServerLibrary"', template)
        self.assertIn('id="addWindowsLibrary"', template)
        self.assertIn('id="libraryFilter"', template)
        self.assertIn('libraries: collectLibrarySettings()', javascript)
        self.assertIn('source_type: row.querySelector', javascript)
        self.assertIn('appendLibrary("windows_local")', javascript)
        self.assertIn('result.agent_scans || []', javascript)
        self.assertIn('result.agent_protocol_url || result.agent_scans[0].protocol_url', javascript)
        self.assertEqual(javascript.count('window.location.href = request.protocol_url'), 0)
        self.assertIn('.metadata-api-keys{display:grid;gap:12px}', stylesheet)
        self.assertIn('function readableAccentColor', javascript)
        self.assertIn('`--${prefix}primary-on-${name}`', javascript)
        self.assertIn('`--${prefix}secondary-on-${name}`', javascript)
        self.assertIn('body[data-auto-contrast="true"]', stylesheet)
        self.assertIn('color:var(--accessible-primary)', stylesheet)
        self.assertIn('body[data-style="lcars"] .topbar{', stylesheet)
        self.assertIn('body[data-style="lcars"] .topbar nav button,body[data-style="lcars"] .topbar nav .button-link{background:var(--bg);color:var(--on-bg,var(--text))', stylesheet)
        self.assertIn('id="skipToMain"', template)
        self.assertIn('id="cancelEditorButton" type="button"', template)
        self.assertIn('type="button" data-close-settings class="ghost"', template)
        self.assertIn('type="button" data-close-settings class="secondary"', template)
        self.assertIn('class="secondary browse-library-path" type="button"', javascript)
        self.assertIn("position:sticky;bottom:0", stylesheet)
        self.assertIn('id="closeEditorButton" type="button"', template)
        self.assertIn('id="designProfilesBackButton"', template)
        self.assertIn('id="importDesignProfileButton"', template)
        self.assertIn('id="importDesignProfileFile"', template)
        self.assertIn('id="lcarsSystemClock"', template)
        self.assertNotIn('onclick="probeWindowsAgent()"', template)
        self.assertIn("filename='app.js', v=asset_version", template)
        self.assertIn("SMB-Netzlaufwerk zuerst", template)
        self.assertIn('ru: {', translations)
        self.assertTrue(translations.startswith("(() => {"))
        self.assertTrue(translations.rstrip().endswith("})();"))
        self.assertIn('applyUiLanguage', translations)
        self.assertIn('PROFILE_TRANSFER_PACKS', translations)
        self.assertIn('"profiles.import":"Importer un profil"', translations)
        self.assertIn('resolveUiLanguage', translations)
        self.assertIn('"settings.auto": "Automatic (browser)"', translations)
        self.assertIn('"translator.reachable": "Translator is reachable and ready."', translations)
        self.assertIn('"translator.reachableLanguages": "Translator ready · Languages: {languages}"', translations)
        self.assertIn('id="testTranslatorButton"', template)
        self.assertIn('id="translationLanguageSelect"', template)
        self.assertIn('id="startTranslationButton"', template)
        self.assertIn('addEventListener("keydown", (event) => {', javascript)
        self.assertIn('event.key !== "Enter"', javascript)
        self.assertIn('searchTheGamesDbMetadata()', javascript)
        self.assertIn('class="button-spinner"', javascript)
        self.assertIn('tr("info.translating", {seconds})', javascript)
        self.assertIn('trForLanguage', translations)
        self.assertIn('CONTENT_LANGUAGE_PACKS', translations)
        self.assertIn('"info.overview": "Contenuto del gioco"', translations)
        self.assertIn('const contentLanguage = String(game.metadata_overview_language', javascript)
        self.assertIn('infoTr("info.overview")', javascript)
        self.assertIn('tr("common.back")', javascript)
        self.assertIn('actionLabel(game, tr)', javascript)
        self.assertNotIn('actionLabel(game, infoTr)', javascript)
        self.assertNotIn('infoTr("game.folder")', javascript)
        self.assertIn('"info.overview": "Description du jeu"', translations)
        self.assertIn('"info.overview": "Contenido del juego"', translations)
        for language in ("it", "fr", "es", "pt", "pl", "nl", "tr"):
            self.assertIn(f"  {language}: {{", translations)
            self.assertIn(f'<option value="{language}">', template)
        self.assertIn('UI_PACKS.ar = {', translations)
        self.assertIn('<option value="ar">العربية</option>', template)
        self.assertIn('UI_PACKS.zh = {', translations)
        self.assertIn('UI_PACKS.tlh = Object.assign({}, UI_PACKS.en', translations)
        self.assertIn('UI_PACKS.sjn = Object.assign({}, UI_PACKS.en', translations)
        self.assertIn('<option value="zh">简体中文</option>', template)
        self.assertIn('<option value="tlh">Klingon (Beta)</option>', template)
        self.assertIn('<option value="sjn">Elvish / Sindarin (Beta)</option>', template)
        self.assertIn('tlh: "Klingon (Beta)"', javascript)
        self.assertIn('sjn: "Elvish / Sindarin (Beta)"', javascript)
        self.assertIn('"ar", "zh", "tlh", "sjn"', javascript)
        self.assertIn('displayTranslationLanguageLabel(code)', javascript)
        self.assertIn('currentUiLanguage === "ar" ? "rtl" : "ltr"', translations)
        self.assertIn('html[dir="rtl"]', stylesheet)
        self.assertIn('unicode-bidi:isolate', stylesheet)
        self.assertIn('html[dir="rtl"] .brand{padding-left:0;padding-right:64px', stylesheet)
        self.assertIn('const rtl = document.documentElement.dir === "rtl"', javascript)
        self.assertIn('const ADDITIONAL_UI_PACKS = {', translations)
        self.assertIn('UI_PACKS[language] = Object.assign({}, UI_PACKS.en', translations)
        additional_packs = translations.split("const ADDITIONAL_UI_PACKS = {", 1)[1].split(
            "\n};", 1
        )[0]
        required_localized_settings = (
            "settings.translatorHint",
            "settings.translatorManaged",
            "settings.keysNote",
            "settings.exclusionNote",
            "settings.removeGamesDb",
            "settings.removeTranslator",
        )
        for index, language in enumerate(("it", "fr", "es", "pt", "pl", "nl", "tr")):
            next_language = ("fr", "es", "pt", "pl", "nl", "tr", None)[index]
            language_pack = additional_packs.split(f"  {language}: {{", 1)[1]
            if next_language:
                language_pack = language_pack.split(f"  {next_language}: {{", 1)[0]
            for key in required_localized_settings:
                self.assertIn(f'"{key}"', language_pack, f"{language} is missing {key}")
        self.assertNotIn('  uk: {', translations)
        self.assertNotIn('if (status) status.textContent = label;', javascript)
        self.assertIn('scrollGameInfoToTranslationMenu(menu)', javascript)
        self.assertIn('behavior: preferredScrollBehavior()', javascript)
        self.assertIn('function closeEditor()', javascript)
        self.assertIn('resetEditorCoverSelection()', javascript)
        self.assertIn('motion_preference: document.querySelector("#settingMotionPreference").value', javascript)
        self.assertIn('aria-keyshortcuts="Alt+ArrowRight"', javascript)
        self.assertIn('data-page="first"', javascript)
        self.assertIn('data-page="last"', javascript)
        self.assertIn('function paginationPageItems', javascript)
        self.assertIn('event.altKey && event.key.toLowerCase() === "k"', javascript)
        self.assertIn('aria-keyshortcuts="Alt+K"', template)
        self.assertNotIn('function animateEnergyColor', javascript)
        self.assertIn('color:var(--energy-end)', stylesheet)
        self.assertIn('rel="manifest"', template)
        self.assertIn('navigator.serviceWorker.register("/service-worker.js")', javascript)
        manifest = (ROOT / "server" / "static" / "manifest.webmanifest").read_text(encoding="utf-8")
        self.assertIn('"client_mode":"focus-existing"', manifest.replace(" ", ""))
        self.assertIn('id="maintenanceStatus"', template)
        self.assertIn('/api/maintenance/restore', javascript)
        self.assertIn('id="restoreBackupDialog"', template)
        self.assertIn('/api/maintenance/backup/inspect', javascript)
        self.assertNotIn('confirm(tr("maintenance.restoreConfirm"))', javascript)
        self.assertIn('SKIP_WAITING', (ROOT / "server" / "static" / "service-worker.js").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "server" / "static" / "manifest.webmanifest").is_file())
        self.assertTrue((ROOT / "server" / "static" / "service-worker.js").is_file())
        self.assertIn('body[data-motion="reduce"]', stylesheet)
        self.assertIn(':focus-visible', stylesheet)
        self.assertIn('"accessibility.skipToMain":"Skip to main content"', translations)
        self.assertIn('id="agentSetupBackButton"', template)
        self.assertIn('addEventListener("click", closeAgentSetup)', javascript)
        self.assertIn('"agent.back": "Back"', translations)
        self.assertIn('id="testTranslatorButton" type="button" class="secondary" data-i18n="translator.test" disabled', template)
        self.assertIn('/api/translator/test', javascript)
        self.assertIn('result.languages.join(", ")', javascript)
        self.assertIn('body[data-style="lcars"] .agent-note-content', stylesheet)
        self.assertIn('grid-template-columns:repeat(3,minmax(0,1fr))', stylesheet)
        self.assertIn('addEventListener("click", probeWindowsAgent)', javascript)
        self.assertIn('applySettings(settings);\n    render();', javascript)
        self.assertIn('/api/design-profiles/import', javascript)
        self.assertIn('data-profile-export=', javascript)
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
        for language in ("de", "en", "ru", "it", "fr", "es", "pt", "pl", "nl", "tr"):
            self.assertIn(f'Name: "{language}"; MessagesFile:', installer)
            self.assertIn(f'{language}.ServerTitle=', installer)
            self.assertIn(f'{language}.LibraryDescription=', installer)
            self.assertIn(f'{language}.TokenHelpText=', installer)
        self.assertIn("CustomMessage('ServerTitle')", installer)
        self.assertIn("CustomMessage('LibraryDescription')", installer)
        self.assertIn("CustomMessage('TokenRejected')", installer)
        self.assertIn('"installer_language": "', installer)
        agent = (ROOT / "windows-agent" / "GameVaultAgent.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("$manifest.ui_language", agent)
        self.assertIn("$scanManifest.ui_language", agent)
        self.assertIn("$pickerManifest.ui_language", agent)
        self.assertIn('Confirmation', agent)
        self.assertIn('"it", "fr", "es", "pt", "pl", "nl", "tr"', agent)
        self.assertIn('caption = "Conferma"', agent)
        self.assertIn('caption = "Confirmation"', agent)
        self.assertIn('caption = "Confirmación"', agent)
        self.assertIn('caption = "Potwierdzenie"', agent)
        self.assertIn('caption = "Bevestiging"', agent)
        self.assertIn('caption = "Onay"', agent)
        self.assertIn('caption = "تأكيد"', agent)
        self.assertIn('caption = "确认"', agent)
        self.assertIn('tlh = @{ direct_setup', agent)
        self.assertIn('sjn = @{ direct_setup', agent)
        self.assertIn('function Show-ConfirmationDialog', agent)
        self.assertIn('$form.CancelButton = $noButton', agent)
        self.assertIn('$noButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel', agent)
        self.assertIn('return ($result -eq [System.Windows.Forms.DialogResult]::Yes)', agent)
        self.assertIn('Show-ConfirmationDialog $message $confirmationTitle', agent)
        self.assertNotIn('[System.Windows.MessageBoxButton]::YesNo', agent)
        self.assertIn('html[lang="tlh"]', stylesheet)
        self.assertIn('html[lang="sjn"]', stylesheet)

        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("libretranslate/libretranslate:v1.9.6", compose)
        self.assertIn("MISSION_CONTROL_TRANSLATOR_URL: http://translator:5000", compose)
        self.assertIn("LT_LOAD_ONLY: en,de,ru,it,fr,es,pt,pl,nl,tr,ar,zh", compose)
        self.assertIn(f'com.hypetek.mission-control.deployment: "{version}"', compose)
        self.assertNotIn('"5000:5000"', compose)

        app_source = (ROOT / "server" / "app.py").read_text(encoding="utf-8")
        translation_source = (ROOT / "server" / "translation.py").read_text(encoding="utf-8")
        self.assertIn('content_target_languages(languages or [])', app_source)
        self.assertIn('AGENT_INSTALLER_ASSET = "HypeTek-Mission-Control-Agent-Setup.exe"', app_source)
        self.assertIn('download_windows_agent_exe', app_source)
        self.assertIn('download_windows_agent', app_source)
        self.assertIn('EXPERIMENTAL_CONTENT_LANGUAGES = {"tlh", "sjn"}', translation_source)
        self.assertIn('"ar", "zh", "tlh", "sjn"', translation_source)

        notice = (ROOT / "NOTICE.txt").read_text(encoding="utf-8")
        self.assertIn("LibreTranslate 1.9.6", notice)
        self.assertIn("GNU Affero General Public License v3.0", notice)

        workflow = (ROOT / ".github" / "workflows" / "container.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('version=$(tr -d', workflow)
        self.assertIn('gh release upload $tag', workflow)
        self.assertIn('catch {', workflow)
        self.assertIn('if (-not $releaseExists)', workflow)
        self.assertIn('type=raw,value=${{ steps.version.outputs.version }}', workflow)
        self.assertIn("!contains(steps.version.outputs.version, '-')", workflow)
        self.assertIn('Get-ChildItem -LiteralPath "windows-agent" -Filter "*.ps1"', workflow)
        self.assertIn('--prerelease', workflow)
        self.assertIn('digest: ${{ steps.build.outputs.digest }}', workflow)
        self.assertIn('IMAGE_DIGEST: ${{ needs.container.outputs.digest }}', workflow)
        self.assertIn('release-manifest.txt', workflow)
        self.assertIn('installer_sha256=', workflow)
        self.assertIn('HypeTek-Mission-Control-Agent-Setup.exe', workflow)

        # Windows PowerShell 5.1 treats typographic double quotes as string delimiters.
        # Keep them out of executable PowerShell source so translated copy cannot
        # accidentally break the parser again.
        for powershell_file in (ROOT / "windows-agent").glob("*.ps1"):
            source = powershell_file.read_text(encoding="utf-8-sig")
            for quote in ("“", "”", "„"):
                self.assertNotIn(quote, source, f"Smart quote {quote!r} in {powershell_file.name}")

        catalog_root = ROOT / "truenas-catalog" / "ix-dev" / "community" / "hypetek-mission-control"
        for relative in (
            "app.yaml",
            "ix_values.yaml",
            "questions.yaml",
            "README.md",
            "templates/docker-compose.yaml",
            "templates/test_values/basic-values.yaml",
        ):
            self.assertTrue((catalog_root / relative).is_file(), relative)
        app_yaml = (catalog_root / "app.yaml").read_text(encoding="utf-8")
        ix_values = (catalog_root / "ix_values.yaml").read_text(encoding="utf-8")
        catalog_template = (catalog_root / "templates" / "docker-compose.yaml").read_text(encoding="utf-8")
        self.assertIn(f"app_version: {version}", app_yaml)
        self.assertIn("lib_version: 2.3.11", app_yaml)
        self.assertIn("version: 1.0.2", app_yaml)
        self.assertIn(f"tag: {version}", ix_values)
        self.assertIn('{"container_port": values.consts.web_port}', catalog_template)
        self.assertIn('healthcheck.set_test("curl"', catalog_template)

    def test_line_endings_are_declared_for_cross_platform_builds(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("*.py text eol=lf", attributes)
        self.assertIn("*.ps1 text eol=crlf", attributes)
        self.assertIn("*.iss text eol=crlf", attributes)


if __name__ == "__main__":
    unittest.main()
