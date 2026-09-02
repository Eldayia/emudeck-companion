import unittest

from companion_models import ProcessInfo
from companion_process_detection import find_emulator


class ProcessDetectionTests(unittest.TestCase):
    def test_matches_executable_case_insensitively(self):
        profiles = [{"id": "cemu", "processes": ["Cemu"]}]
        processes = [ProcessInfo(44, "cemu", ("/usr/bin/Cemu", "game.wua"), 100)]
        match = find_emulator(profiles, processes)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[1].pid, 44)

    def test_prefers_newest_emulator_process(self):
        profiles = [
            {"id": "retroarch", "processes": ["retroarch"]},
            {"id": "dolphin", "processes": ["dolphin-emu"]},
        ]
        processes = [
            ProcessInfo(10, "retroarch", ("retroarch", "old.sfc"), 100),
            ProcessInfo(20, "dolphin-emu", ("dolphin-emu", "new.rvz"), 200),
        ]
        match = find_emulator(profiles, processes)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[0]["id"], "dolphin")

    def test_es_de_is_not_an_emulator(self):
        profiles = [{"id": "retroarch", "processes": ["retroarch"]}]
        processes = [ProcessInfo(10, "es-de", ("es-de",), 300)]
        self.assertIsNone(find_emulator(profiles, processes))

    def test_matches_flatpak_emulator_processes(self):
        profiles = [
            {"id": "ppsspp", "processes": ["PPSSPPSDL"]},
            {"id": "melonds", "processes": ["melonDS"]},
        ]
        processes = [
            ProcessInfo(30, "PPSSPPSDL", ("PPSSPPSDL", "/roms/game.iso"), 300),
            ProcessInfo(40, "melonDS", ("melonDS", "/roms/game.nds", "-f"), 400),
        ]
        match = find_emulator(profiles, processes)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[0]["id"], "melonds")
        self.assertEqual(match[1].pid, 40)

    def test_matches_azahar_appimage_by_command(self):
        profiles = [{"id": "azahar", "processes": ["azahar", "azahar.AppImage"]}]
        processes = [ProcessInfo(
            50,
            "AppRun",
            ("/home/deck/Applications/azahar.AppImage", "/roms/game.3ds"),
            500,
        )]
        match = find_emulator(profiles, processes)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[0]["id"], "azahar")

    def test_matches_flycast_flatpak_child(self):
        profiles = [{"id": "flycast", "processes": ["flycast"]}]
        processes = [ProcessInfo(
            60,
            "flycast",
            ("flycast", "/home/deck/Emulation/roms/dreamcast/Sonic Adventure.chd"),
            600,
        )]
        match = find_emulator(profiles, processes)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[1].pid, 60)


if __name__ == "__main__":
    unittest.main()
