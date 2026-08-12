import os
import re
import tempfile
import unittest
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
        )
        sys.path.insert(0, str(Path(__file__).parents[1] / "server"))
        for module in ("app", "database", "scanner"):
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


if __name__ == "__main__":
    unittest.main()
