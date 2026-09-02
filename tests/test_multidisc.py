import tempfile
import unittest
from pathlib import Path

from companion_multidisc import playlist_discs


class MultidiscTests(unittest.TestCase):
    def test_reads_relative_m3u_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            playlist = root / "Game.m3u"
            playlist.write_text("# comment\nGame (Disc 1).chd\n./Game (Disc 2).chd\n", encoding="utf-8")
            self.assertEqual(
                playlist_discs(str(playlist)),
                [str(root / "Game (Disc 1).chd"), str(root / "Game (Disc 2).chd")],
            )

    def test_ignores_non_playlists(self):
        self.assertEqual(playlist_discs("Game.chd"), [])


if __name__ == "__main__":
    unittest.main()
