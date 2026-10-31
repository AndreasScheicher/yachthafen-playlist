import unittest
from pathlib import Path

from UpdatePlaylist.superfly import parse_superfly_html


FIXTURE = Path(__file__).parent / "fixtures" / "superfly_playlist_basic.html"
FIXTURE_TEXT = Path(__file__).parent / "fixtures" / "superfly_playlist_textlines.html"
FIXTURE_GRID = Path(__file__).parent / "fixtures" / "superfly_playlist_grid.html"


class TestSuperflyParser(unittest.TestCase):
    def test_parses_basic_fixture(self):
        html = FIXTURE.read_bytes()
        tracks = parse_superfly_html(html)
        self.assertIsInstance(tracks, list)
        # Expect normalized "artist - title" in lowercase
        self.assertEqual(
            tracks,
            [
                "flo naegeli & august charles - changes",
                "george duke - reach out",
                "fred kingdom - close that door",
            ],
        )

    def test_parses_textlines_fixture(self):
        html = FIXTURE_TEXT.read_bytes()
        tracks = parse_superfly_html(html)
        self.assertIsInstance(tracks, list)
        # Expect the same normalized output from the text-lines format
        self.assertEqual(
            tracks,
            [
                "flo naegeli & august charles - changes",
                "george duke - reach out",
                "fred kingdom - close that door",
            ],
        )

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


if __name__ == "__main__":
    unittest.main()
