import unittest

from companion_game_detection import extract_rom, game_name_from_rom


class GameDetectionTests(unittest.TestCase):
    def test_extracts_last_rom_argument(self):
        profile = {"rom_extensions": ["rvz"]}
        argv = ["dolphin-emu", "-b", "-e", "/home/deck/Emulation/roms/gc/Metroid Prime.rvz"]
        self.assertEqual(extract_rom(argv, profile), "/home/deck/Emulation/roms/gc/Metroid Prime.rvz")

    def test_ignores_non_rom_paths(self):
        profile = {"rom_extensions": ["iso"]}
        argv = ["pcsx2-qt", "--cfgpath", "/home/deck/.config/PCSX2", "game.iso"]
        self.assertEqual(extract_rom(argv, profile), "game.iso")

    def test_makes_readable_game_name(self):
        self.assertEqual(game_name_from_rom("/roms/Final_Fantasy_VII (Disc 2).chd"), "Final Fantasy VII")


if __name__ == "__main__":
    unittest.main()
