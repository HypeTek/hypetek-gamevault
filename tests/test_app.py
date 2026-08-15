import os
import re
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
import sys


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        games = root / "games"
        config = root / "config"
        game = games / "Test Game"
        game.mkdir(parents=True)
        (game / "setup.exe").write_bytes(b"MZ")
        os.environ.update(
            GAMEVAULT_GAME_ROOT=str(games),
            GAMEVAULT_CONFIG_DIR=str(config),
            GAMEVAULT_ADMIN_PASSWORD="admin-test",
            GAMEVAULT_AGENT_TOKEN="agent-test",
            GAMEVAULT_SECRET_KEY="secret-test",
            GAMEVAULT_AGENT_DIR=str(Path(__file__).parents[1] / "windows-agent"),
        )
        sys.path.insert(0, str(Path(__file__).parents[1] / "server"))
        for module in ("app", "database", "scanner", "settings", "metadata", "translation", "design_profiles"):
            sys.modules.pop(module, None)
        import app
        self.module = app
        self.client = app.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def login(self):
        page = self.client.get("/login")
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
        response = self.client.post(
            "/login", data={"password": "admin-test", "csrf_token": token}
        )
        with self.client.session_transaction() as session:
            self.csrf = session["csrf_token"]
        return response

    def post(self, path: str, **kwargs):
        headers = {**kwargs.pop("headers", {}), "X-CSRF-Token": self.csrf}
        return self.client.post(path, headers=headers, **kwargs)

    def test_scan_ticket_and_one_time_agent_manifest(self):
        self.login()
        response = self.post("/api/scan")
        self.assertEqual(response.status_code, 200)
        games = self.client.get("/api/games").get_json()
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["action"], "direct_setup")

        ticket_response = self.post(f"/api/games/{games[0]['id']}/launch-ticket", json={})
        self.assertEqual(ticket_response.status_code, 200)
        token = ticket_response.get_json()["protocol_url"].split("ticket=", 1)[1]

        unauthorized = self.client.get(f"/api/agent/tickets/{token}")
        self.assertEqual(unauthorized.status_code, 401)
        headers = {"Authorization": "Bearer agent-test"}
        manifest = self.client.get(f"/api/agent/tickets/{token}", headers=headers)
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.get_json()["launcher"], "Test Game/setup.exe")
        self.assertEqual(manifest.get_json()["ui_language"], "auto")
        reused = self.client.get(f"/api/agent/tickets/{token}", headers=headers)
        self.assertEqual(reused.status_code, 404)

        folder_ticket = self.post(
            f"/api/games/{games[0]['id']}/launch-ticket",
            json={"action": "open_folder"},
        )
        token = folder_ticket.get_json()["protocol_url"].split("ticket=", 1)[1]
        manifest = self.client.get(f"/api/agent/tickets/{token}", headers=headers)
        self.assertEqual(manifest.get_json()["action"], "open_folder")
        self.assertEqual(manifest.get_json()["launcher"], "Test Game")

    def test_agent_token_validation_is_unambiguous(self):
        get_is_not_a_validation = self.client.get("/api/agent/validate")
        self.assertEqual(get_is_not_a_validation.status_code, 405)

        missing = self.client.post("/api/agent/validate")
        self.assertEqual(missing.status_code, 401)

        wrong = self.client.post(
            "/api/agent/validate",
            headers={"Authorization": "Bearer definitely-wrong-agent-token"},
        )
        self.assertEqual(wrong.status_code, 401)

        valid = self.client.post(
            "/api/agent/validate",
            headers={"Authorization": "Bearer agent-test"},
        )
        self.assertEqual(valid.status_code, 204)
        self.assertEqual(
            valid.headers.get("X-Mission-Control-Agent"), "authenticated"
        )
        self.assertEqual(valid.headers.get("Cache-Control"), "no-store")

    def test_health_reports_running_version_and_agent_api(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        health = response.get_json()
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["version"], "0.3.14")
        self.assertEqual(health["agent_api"], 3)
        self.assertFalse(health["translator_managed"])

    def test_path_escape_is_rejected(self):
        self.login()
        self.post("/api/scan")
        game = self.client.get("/api/games").get_json()[0]
        response = self.client.patch(
            f"/api/games/{game['id']}",
            json={"launcher_override": "../evil.exe"},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(response.status_code, 400)

    def test_mutation_without_csrf_is_rejected(self):
        self.login()
        response = self.client.post("/api/scan")
        self.assertEqual(response.status_code, 403)

    def test_windows_agent_download(self):
        self.login()
        response = self.client.get("/download/windows-agent.zip")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        with zipfile.ZipFile(BytesIO(response.data)) as archive:
            expected = [
                "Mission-Control-Windows-Agent/GameVaultAgent.ps1",
                "Mission-Control-Windows-Agent/Install-Agent.ps1",
                "Mission-Control-Windows-Agent/README.txt",
                "Mission-Control-Windows-Agent/Uninstall-Agent.ps1",
            ]
            self.assertEqual(sorted(archive.namelist()), expected)
            for name in expected:
                self.assertTrue(archive.read(name).startswith(b"\xef\xbb\xbf"))

        installer = self.client.get("/download/windows-agent.exe")
        self.assertEqual(installer.status_code, 302)
        self.assertEqual(
            installer.headers["Location"],
            "https://github.com/HypeTek/hypetek-gamevault/releases/download/v0.3.14/HypeTek-Mission-Control-Agent-Setup.exe",
        )

    def test_appearance_settings_and_scan_exclusions(self):
        self.login()
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("SMB-/Tailscale-Hilfe", page.get_data(as_text=True))
        self.assertIn("API-/Translator-Hilfe", page.get_data(as_text=True))
        html = page.get_data(as_text=True)
        self.assertIn("/static/app.js?v=0.3.14", html)
        self.assertIn("/static/i18n.js?v=0.3.14", html)
        self.assertIn("/static/app.css?v=0.3.14", html)
        self.assertIn("Windows-Agent einrichten", html)
        self.assertIn("EXE-Agent herunterladen", html)
        self.assertIn("SMB-Netzlaufwerk zuerst", html)
        self.assertIn('id="lcarsSystemClock"', html)
        self.assertIn("Alternative für Experten: PowerShell-Fallback", html)
        self.assertIn("Kartenbild ausrichten", html)
        self.assertNotIn("Cover-Ausschnitt in den Karten", html)
        settings = self.client.get("/api/settings").get_json()
        self.assertEqual(settings["version"], "0.3.14")
        self.assertEqual(settings["theme"], "mission")
        self.assertNotIn("thegamesdb_api_key", settings)
        self.assertFalse(settings["thegamesdb_configured"])
        self.assertEqual(settings["active_design_profile"], "mission")
        self.assertEqual(settings["design_profile"]["style"], "soft")
        response = self.client.patch(
            "/api/settings",
            json={
                "server_name": "TrueTitan",
                "library_name": "HypeTek HQ",
                "theme": "cyberpunk",
                "crosshair_cursor": True,
                "scan_exclusions": ["Test Game"],
                "ui_language": "ru",
            },
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["library_name"], "HypeTek HQ")
        self.assertEqual(response.get_json()["ui_language"], "ru")
        scan = self.post("/api/scan")
        self.assertEqual(scan.get_json()["scanned"], 0)

    def test_design_profiles_are_validated_persistent_and_protected(self):
        self.login()
        overview = self.client.get("/api/design-profiles").get_json()
        self.assertEqual(overview["active"], "mission")
        self.assertEqual(len(overview["profiles"]), 4)
        mission = next(item for item in overview["profiles"] if item["id"] == "mission")
        lcars = next(item for item in overview["profiles"] if item["id"] == "lcars")
        self.assertEqual(lcars["name"], "LCARS Console")
        self.assertEqual(lcars["style"], "lcars")
        created_payload = {
            **mission,
            "name": "HypeTek Test",
            "builtin": False,
            "style": "terminal",
            "font": "mono",
            "colors": {**mission["colors"], "primary": "#112233"},
        }
        created = self.post("/api/design-profiles", json=created_payload)
        self.assertEqual(created.status_code, 201)
        profile_id = created.get_json()["id"]

        activated = self.post(f"/api/design-profiles/{profile_id}/activate", json={})
        self.assertEqual(activated.status_code, 200)
        self.assertEqual(activated.get_json()["active_design_profile"], profile_id)
        self.assertEqual(activated.get_json()["design_profile"]["font"], "mono")

        invalid = self.client.put(
            f"/api/design-profiles/{profile_id}",
            json={**created_payload, "colors": {**mission["colors"], "primary": "red"}},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(invalid.status_code, 400)

        protected = self.client.delete(
            "/api/design-profiles/mission", headers={"X-CSRF-Token": self.csrf}
        )
        self.assertEqual(protected.status_code, 400)
        stored = Path(os.environ["GAMEVAULT_CONFIG_DIR"]) / "mission-control-designs.json"
        self.assertTrue(stored.is_file())
        self.assertEqual(stored.stat().st_mode & 0o777, 0o600)

    def test_design_profile_background_is_checked_before_storage(self):
        self.login()
        invalid = self.post(
            "/api/design-profiles/background",
            data={"background": (BytesIO(b"not an image"), "background.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(invalid.status_code, 400)
        valid = self.post(
            "/api/design-profiles/background",
            data={"background": (BytesIO(b"\x89PNG\r\n\x1a\n" + b"x" * 32), "background.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(valid.status_code, 201)
        name = valid.get_json()["name"]
        self.assertRegex(name, r"^background-[a-f0-9]{24}\.png$")
        self.assertTrue((Path(os.environ["GAMEVAULT_CONFIG_DIR"]) / "backgrounds" / name).is_file())

    def test_thegamesdb_key_is_write_only_and_blank_patch_keeps_it(self):
        self.login()
        original_validate = self.module.validate_thegamesdb_key
        self.module.validate_thegamesdb_key = lambda key: None
        try:
            saved = self.client.patch(
                "/api/settings",
                json={"thegamesdb_api_key": "private-test-key"},
                headers={"X-CSRF-Token": self.csrf},
            )
        finally:
            self.module.validate_thegamesdb_key = original_validate
        self.assertEqual(saved.status_code, 200)
        self.assertTrue(saved.get_json()["thegamesdb_configured"])
        self.assertNotIn("thegamesdb_api_key", saved.get_json())

        unchanged = self.client.patch(
            "/api/settings",
            json={"server_name": "Another Name"},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertTrue(unchanged.get_json()["thegamesdb_configured"])
        self.assertEqual(self.module.settings_store.load()["thegamesdb_api_key"], "private-test-key")

        removed = self.client.patch(
            "/api/settings",
            json={"thegamesdb_api_key": None},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertFalse(removed.get_json()["thegamesdb_configured"])

    def test_invalid_thegamesdb_key_is_not_saved(self):
        self.login()
        original_validate = self.module.validate_thegamesdb_key
        try:
            def reject(_key):
                raise self.module.MetadataError("TheGamesDB-API-Key wurde abgelehnt")

            self.module.validate_thegamesdb_key = reject
            response = self.client.patch(
                "/api/settings",
                json={"thegamesdb_api_key": "wrong-key"},
                headers={"X-CSRF-Token": self.csrf},
            )
        finally:
            self.module.validate_thegamesdb_key = original_validate
        self.assertEqual(response.status_code, 502)
        self.assertFalse(self.module.settings_store.load()["thegamesdb_api_key"])

    def test_manual_thegamesdb_search_and_cover_selection(self):
        self.login()
        self.post("/api/scan")
        game = self.client.get("/api/games").get_json()[0]
        self.module.settings_store.update({"thegamesdb_api_key": "private-test-key"})
        candidate = {
            "provider": "thegamesdb",
            "provider_id": "123",
            "name": "Test Game",
            "released": "2026-08-13",
            "platform": "PC",
            "overview": "A test game overview.",
            "rating": "T - Teen",
            "players": "1",
            "coop": "No",
            "image_url": "https://cdn.thegamesdb.net/images/original/boxart/front/123-1.jpg",
            "source_url": "https://thegamesdb.net/game.php?id=123",
        }
        original_search = self.module.search_thegamesdb
        original_download = self.module.download_thegamesdb_image
        try:
            self.module.search_thegamesdb = lambda key, query: [candidate]
            search = self.post(
                f"/api/games/{game['id']}/metadata/search",
                json={"query": "Test Game"},
            )
            self.assertEqual(search.status_code, 200)
            self.assertEqual(search.get_json()["results"], [candidate])

            def fake_download(_url, destination):
                target = destination.with_suffix(".jpg")
                target.write_bytes(b"\xff\xd8\xfftest")
                return target.name

            self.module.download_thegamesdb_image = fake_download
            applied = self.post(
                f"/api/games/{game['id']}/metadata/apply",
                json=candidate,
            )
            self.assertEqual(applied.status_code, 200)
            updated = applied.get_json()
            self.assertEqual(updated["metadata_provider"], "thegamesdb")
            self.assertEqual(updated["metadata_provider_id"], "123")
            self.assertEqual(updated["metadata_source_url"], candidate["source_url"])
            self.assertEqual(updated["metadata_overview"], "A test game overview.")
            self.assertEqual(updated["metadata_overview_original"], "A test game overview.")
            self.assertEqual(updated["metadata_platform"], "PC")
            self.assertTrue(updated["cover_name"].endswith(".jpg"))
            first_cover = updated["cover_name"]

            replaced = self.post(
                f"/api/games/{game['id']}/metadata/apply",
                json=candidate,
            ).get_json()
            self.assertNotEqual(replaced["cover_name"], first_cover)

            self.module.settings_store.update({
                "translator_url": "http://translator:5000",
                "content_language": "de",
            })
            original_translate = self.module.translate_text
            self.module.translate_text = lambda endpoint, text, target, key="": "Ein Testspiel."
            try:
                translated = self.post(
                    f"/api/games/{game['id']}/metadata/translate",
                    json={},
                )
            finally:
                self.module.translate_text = original_translate
            self.assertEqual(translated.status_code, 200)
            self.assertEqual(translated.get_json()["metadata_overview"], "Ein Testspiel.")
            self.assertEqual(translated.get_json()["metadata_overview_original"], "A test game overview.")
            self.assertEqual(translated.get_json()["metadata_overview_language"], "de")
        finally:
            self.module.search_thegamesdb = original_search
            self.module.download_thegamesdb_image = original_download

    def test_cover_position_is_stored_and_clamped(self):
        self.login()
        self.post("/api/scan")
        game = self.client.get("/api/games").get_json()[0]
        updated = self.client.patch(
            f"/api/games/{game['id']}",
            json={"cover_position_y": 88},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["cover_position_y"], 88)
        clamped = self.client.patch(
            f"/api/games/{game['id']}",
            json={"cover_position_y": 999},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(clamped.get_json()["cover_position_y"], 100)

    def test_favorite_survives_rescan_and_rejects_invalid_values(self):
        self.login()
        self.post("/api/scan")
        game = self.client.get("/api/games").get_json()[0]
        marked = self.client.patch(
            f"/api/games/{game['id']}",
            json={"favorite": True},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(marked.status_code, 200)
        self.assertTrue(marked.get_json()["favorite"])

        self.post("/api/scan")
        rescanned = next(
            candidate for candidate in self.client.get("/api/games").get_json()
            if candidate["id"] == game["id"]
        )
        self.assertTrue(rescanned["favorite"])

        invalid = self.client.patch(
            f"/api/games/{game['id']}",
            json={"favorite": "yes"},
            headers={"X-CSRF-Token": self.csrf},
        )
        self.assertEqual(invalid.status_code, 400)

    def test_games_include_clean_suggested_search_title(self):
        self.login()
        noisy = Path(os.environ["GAMEVAULT_GAME_ROOT"]) / "AC Valhalla -- fitgirl-repacks site"
        noisy.mkdir()
        (noisy / "setup.exe").write_bytes(b"MZ")
        self.post("/api/scan")
        games = self.client.get("/api/games").get_json()
        candidate = next(game for game in games if game["relative_path"].startswith("AC Valhalla"))
        self.assertEqual(candidate["metadata_search_title"], "AC Valhalla")

    def test_agent_probe_requires_real_agent_confirmation(self):
        self.login()
        created = self.post("/api/agent/probes", json={})
        self.assertEqual(created.status_code, 200)
        probe = created.get_json()
        self.assertIn("hypetek-gamevault://probe?token=", probe["protocol_url"])

        pending = self.client.get(f"/api/agent/probes/{probe['token']}")
        self.assertFalse(pending.get_json()["confirmed"])

        unauthorized = self.client.post(f"/api/agent/probes/{probe['token']}/confirm")
        self.assertEqual(unauthorized.status_code, 401)
        confirmed = self.client.post(
            f"/api/agent/probes/{probe['token']}/confirm",
            headers={"Authorization": "Bearer agent-test"},
        )
        self.assertEqual(confirmed.status_code, 204)
        status = self.client.get(f"/api/agent/probes/{probe['token']}").get_json()
        self.assertTrue(status["confirmed"])

    def test_api_translator_pdf_is_downloadable(self):
        self.login()
        response = self.client.get("/download/api-and-translator-guide.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF-"))
        response.close()
        qr = self.client.get("/help/api-and-translator-guide/qr.svg")
        self.assertEqual(qr.status_code, 200)
        self.assertEqual(qr.mimetype, "image/svg+xml")
        self.assertIn(b"<svg", qr.data)

    def test_translator_is_validated_and_secret_is_write_only(self):
        self.login()
        original_validate = self.module.validate_translator
        self.module.validate_translator = lambda url, key="": ["de", "en", "ru"]
        try:
            saved = self.client.patch(
                "/api/settings",
                json={
                    "translator_url": "http://translator:5000/",
                    "translator_api_key": "translator-secret",
                    "content_language": "ru",
                },
                headers={"X-CSRF-Token": self.csrf},
            )
        finally:
            self.module.validate_translator = original_validate
        self.assertEqual(saved.status_code, 200)
        public = saved.get_json()
        self.assertEqual(public["translator_url"], "http://translator:5000")
        self.assertEqual(public["content_language"], "ru")
        self.assertTrue(public["translator_configured"])
        self.assertNotIn("translator_api_key", public)

    def test_translator_status_uses_stored_server_side_credentials(self):
        self.login()
        original_validate = self.module.validate_translator
        calls = []
        self.module.validate_translator = lambda url, key="": (calls.append((url, key)) or ["de", "en", "ru"])
        try:
            self.client.patch(
                "/api/settings",
                json={
                    "translator_url": "http://translator:5000",
                    "translator_api_key": "translator-secret",
                },
                headers={"X-CSRF-Token": self.csrf},
            )
            calls.clear()
            response = self.client.get("/api/translator/status")
        finally:
            self.module.validate_translator = original_validate
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"configured": True, "reachable": True, "languages": ["de", "en", "ru"]})
        self.assertEqual(calls, [("http://translator:5000", "translator-secret")])
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_translator_status_reports_missing_configuration(self):
        self.login()
        response = self.client.get("/api/translator/status")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["configured"])
        self.assertFalse(response.get_json()["reachable"])

    def test_managed_translator_migrates_an_existing_empty_setting(self):
        import settings

        original = settings.DEFAULT_TRANSLATOR_URL
        self.module.settings_store.update({"translator_url": ""})
        settings.DEFAULT_TRANSLATOR_URL = "http://translator:5000"
        try:
            values = self.module.settings_store.load()
        finally:
            settings.DEFAULT_TRANSLATOR_URL = original
        self.assertEqual(values["translator_url"], "http://translator:5000")

    def test_translator_test_accepts_unsaved_address_without_persisting_it(self):
        self.login()
        calls = []
        original_validate = self.module.validate_translator
        self.module.validate_translator = lambda url, key="": (calls.append((url, key)) or ["de", "en"])
        try:
            response = self.client.post(
                "/api/translator/test",
                json={"translator_url": "http://translator-preview:5000/", "translator_api_key": "preview-secret"},
                headers={"X-CSRF-Token": self.csrf},
            )
        finally:
            self.module.validate_translator = original_validate
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"configured": True, "reachable": True, "languages": ["de", "en"]})
        self.assertEqual(calls, [("http://translator-preview:5000", "preview-secret")])
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertFalse(self.module.settings_store.load()["translator_url"])


if __name__ == "__main__":
    unittest.main()
