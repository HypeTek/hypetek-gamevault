import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "server"))
import metadata


class MetadataTests(unittest.TestCase):
    def test_clean_game_title_removes_release_noise(self):
        self.assertEqual(
            metadata.clean_game_title("A Plague Tale - Requiem [FitGirl Repack]"),
            "A Plague Tale Requiem",
        )
        self.assertEqual(
            metadata.suggest_game_title("AC Valhalla -- fitgirl-repacks site"),
            "AC Valhalla",
        )
        self.assertEqual(
            metadata.game_title_search_queries("AC Valhalla -- fitgirl-repacks site"),
            ["AC Valhalla", "Valhalla"],
        )

    def test_acronym_search_retries_with_distinctive_title(self):
        calls = []
        empty = {"code": 200, "data": {"games": []}, "include": {}}
        hit = {
            "code": 200,
            "data": {"games": [{"id": 77, "game_title": "Assassin's Creed Valhalla", "platform": 1}]},
            "include": {
                "boxart": {"base_url": {"original": "https://cdn.thegamesdb.net/images/original/"}, "data": {"77": [{"type": "boxart", "side": "front", "filename": "77.jpg"}]}},
                "platform": {"data": {"1": {"name": "PC"}}},
            },
        }
        original = metadata._get_thegamesdb_json

        def fake_get(url):
            calls.append(url)
            return empty if len(calls) == 1 else hit

        metadata._get_thegamesdb_json = fake_get
        try:
            result = metadata.search_thegamesdb("test-key", "AC Valhalla")
        finally:
            metadata._get_thegamesdb_json = original
        self.assertEqual(len(calls), 2)
        self.assertIn("name=Valhalla", calls[1])
        self.assertEqual(result[0]["name"], "Assassin's Creed Valhalla")

    def test_thegamesdb_response_becomes_safe_candidates(self):
        payload = {
            "code": 200,
            "data": {"games": [{"id": 53, "game_title": "Sonic", "release_date": "1991-06-23", "platform": 1, "overview": "Fast blue hedgehog"}]},
            "include": {
                "boxart": {
                    "base_url": {"original": "https://cdn.thegamesdb.net/images/original/"},
                    "data": {"53": [{"type": "boxart", "side": "front", "filename": "boxart/front/53-1.jpg"}]},
                },
                "platform": {"data": {"1": {"name": "PC"}}},
            },
        }
        original = metadata._get_thegamesdb_json
        metadata._get_thegamesdb_json = lambda _url: payload
        try:
            result = metadata.search_thegamesdb("test-key", "Sonic")
        finally:
            metadata._get_thegamesdb_json = original
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["provider"], "thegamesdb")
        self.assertEqual(result[0]["platform"], "PC")
        self.assertEqual(result[0]["overview"], "Fast blue hedgehog")
        self.assertEqual(result[0]["source_url"], "https://thegamesdb.net/game.php?id=53")
        self.assertEqual(
            result[0]["image_url"],
            "https://cdn.thegamesdb.net/images/original/boxart/front/53-1.jpg",
        )

    def test_pc_results_are_sorted_first(self):
        payload = {
            "code": 200,
            "data": {"games": [
                {"id": 1, "game_title": "Same", "platform": 2},
                {"id": 2, "game_title": "Same", "platform": 1},
            ]},
            "include": {
                "boxart": {"base_url": {"original": "https://cdn.thegamesdb.net/images/original/"}, "data": {
                    "1": [{"type": "boxart", "side": "front", "filename": "one.jpg"}],
                    "2": [{"type": "boxart", "side": "front", "filename": "two.jpg"}],
                }},
                "platform": {"data": {"1": {"name": "PC"}, "2": {"name": "Sony Playstation 5"}}},
            },
        }
        original = metadata._get_thegamesdb_json
        metadata._get_thegamesdb_json = lambda _url: payload
        try:
            result = metadata.search_thegamesdb("test-key", "Same")
        finally:
            metadata._get_thegamesdb_json = original
        self.assertEqual(result[0]["platform"], "PC")

    def test_thegamesdb_results_without_boxart_are_skipped(self):
        payload = {"code": 200, "data": {"games": [{"id": 1, "game_title": "No Art"}]}, "include": {}}
        original = metadata._get_thegamesdb_json
        metadata._get_thegamesdb_json = lambda _url: payload
        try:
            self.assertEqual(metadata.search_thegamesdb("test-key", "No Art"), [])
        finally:
            metadata._get_thegamesdb_json = original

    def test_untrusted_image_base_is_replaced_with_official_cdn(self):
        payload = {
            "code": 200,
            "data": {"games": [{"id": 7, "game_title": "Safe", "platform": 1}]},
            "include": {
                "boxart": {
                    "base_url": {"original": "https://example.invalid/tracker/"},
                    "data": {"7": [{"type": "boxart", "side": "front", "filename": "boxart/front/7.jpg"}]},
                },
                "platform": {"data": {}},
            },
        }
        original = metadata._get_thegamesdb_json
        metadata._get_thegamesdb_json = lambda _url: payload
        try:
            result = metadata.search_thegamesdb("test-key", "Safe")
        finally:
            metadata._get_thegamesdb_json = original
        self.assertEqual(
            result[0]["image_url"],
            "https://cdn.thegamesdb.net/images/original/boxart/front/7.jpg",
        )


if __name__ == "__main__":
    unittest.main()
