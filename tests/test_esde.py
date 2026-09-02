import tempfile
import unittest
from pathlib import Path

from companion_esde import ESDEMetadataIndex


class ESDEMetadataTests(unittest.TestCase):
    def test_matches_gamelist_and_scraped_media(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom_root = root / "Emulation" / "roms"
            rom = rom_root / "psx" / "Final Fantasy VII.m3u"
            rom.parent.mkdir(parents=True)
            rom.touch()
            esde = root / ".emulationstation"
            gamelist = esde / "gamelists" / "psx" / "gamelist.xml"
            gamelist.parent.mkdir(parents=True)
            gamelist.write_text(
                "<gameList><game><path>./Final Fantasy VII.m3u</path>"
                "<name>Final Fantasy VII</name><desc>A classic.</desc></game></gameList>",
                encoding="utf-8",
            )
            cover = esde / "downloaded_media" / "psx" / "covers" / "Final Fantasy VII.png"
            cover.parent.mkdir(parents=True)
            cover.touch()

            result = ESDEMetadataIndex(esde, rom_root).lookup(str(rom))
            self.assertEqual(result["name"], "Final Fantasy VII")
            self.assertEqual(result["desc"], "A classic.")
            self.assertEqual(result["image"], str(cover))

    def test_reloads_gamelist_after_mtime_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom_root = root / "roms"
            rom = rom_root / "nes" / "Mario.nes"
            rom.parent.mkdir(parents=True)
            rom.touch()
            esde = root / ".emulationstation"
            gamelist = esde / "gamelists" / "nes" / "gamelist.xml"
            gamelist.parent.mkdir(parents=True)
            gamelist.write_text("<gameList><game><path>./Mario.nes</path><name>Old</name></game></gameList>", encoding="utf-8")
            index = ESDEMetadataIndex(esde, rom_root)
            self.assertEqual(index.lookup(str(rom))["name"], "Old")
            gamelist.write_text("<gameList><game><path>./Mario.nes</path><name>A newer title</name></game></gameList>", encoding="utf-8")
            self.assertEqual(index.lookup(str(rom))["name"], "A newer title")


if __name__ == "__main__":
    unittest.main()
