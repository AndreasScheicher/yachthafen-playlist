import unittest
from pathlib import Path

from UpdatePlaylist.superfly import parse_superfly_html


FIXTURE_GRID = Path(__file__).parent / "fixtures" / "superfly_playlist_grid.html"


class TestSuperflyParser(unittest.TestCase):
    def test_parses_grid_fixture(self):
        html = FIXTURE_GRID.read_bytes()
        tracks = parse_superfly_html(html)
        self.assertIsInstance(tracks, list)
        # Multiple artists separated by ";" are reduced to the first one
        self.assertEqual(
            tracks,
            [
                "phoenix - too young",
                "free nationals - beauty & essex",
                "bruno mars - after last night",
            ],
        )

    def test_missing_heading_returns_empty(self):
        html = b"<html><body><p>Too Young</p><p>- Phoenix</p></body></html>"
        self.assertEqual(parse_superfly_html(html), [])


if __name__ == "__main__":
    unittest.main()
