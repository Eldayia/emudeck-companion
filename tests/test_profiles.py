import tempfile
import unittest
from pathlib import Path

from companion_profiles import ProfileError, ProfileStore


ROOT = Path(__file__).resolve().parents[1]


class ProfileStoreTests(unittest.TestCase):
    def test_loads_all_bundled_profiles(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        self.assertEqual({profile["id"] for profile in store.profiles}, {
            "cemu", "duckstation", "pcsx2", "dolphin", "retroarch",
            "ppsspp", "melonds", "azahar", "flycast", "mame", "fbneo",
            "rpcs3", "ryujinx", "xemu"
        })

    def test_phase_two_profiles_use_emudeck_hotkeys(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        ppsspp = store.get("ppsspp")
        melonds = store.get("melonds")
        azahar = store.get("azahar")
        flycast = store.get("flycast")
        mame = store.get("mame")
        fbneo = store.get("fbneo")
        assert ppsspp is not None and melonds is not None
        assert azahar is not None and flycast is not None
        assert mame is not None and fbneo is not None
        self.assertEqual(ppsspp["actions"]["save_state"]["keys"], ["f2"])
        self.assertEqual(ppsspp["actions"]["load_state"]["keys"], ["f3"])
        self.assertEqual(melonds["actions"]["save_state"]["keys"], ["leftshift", "f{slot}"])
        self.assertEqual(melonds["actions"]["fast_forward"]["keys"], ["end"])
        self.assertEqual(azahar["actions"]["save_state"]["keys"], ["leftshift", "f1"])
        self.assertEqual(azahar["actions"]["swap_screen"]["keys"], ["leftctrl", "tab"])
        self.assertEqual(flycast["actions"]["emulator_menu"]["keys"], ["tab"])
        self.assertEqual(mame["actions"]["emulator_menu"]["keys"], ["tab"])
        self.assertNotIn("save_state", mame["capabilities"])
        self.assertEqual(fbneo["argv_contains"], ["fbneo_libretro"])

    def test_cemu_has_no_savestate_capability(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        cemu = store.get("cemu")
        assert cemu is not None
        self.assertNotIn("save_state", cemu["capabilities"])
        self.assertNotIn("load_state", cemu["capabilities"])

    def test_duckstation_matches_current_emudeck_appimage(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        duckstation = store.get("duckstation")
        assert duckstation is not None
        self.assertIn("DuckStation.AppImage", duckstation["processes"])
        self.assertIn("DuckStation.App", duckstation["processes"])

    def test_phase_three_profiles_use_supported_hotkeys_only(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        rpcs3 = store.get("rpcs3")
        ryujinx = store.get("ryujinx")
        xemu = store.get("xemu")
        assert rpcs3 is not None and ryujinx is not None and xemu is not None
        self.assertEqual(rpcs3["actions"]["save_state"]["keys"], ["leftctrl", "s"])
        self.assertEqual(rpcs3["actions"]["load_state"]["keys"], ["leftalt", "leftctrl", "{slot}"])
        self.assertEqual(ryujinx["actions"]["docked_mode"]["keys"], ["f9"])
        self.assertEqual(ryujinx["actions"]["quit"]["keys"], ["esc"])
        self.assertEqual(xemu["capabilities"], [])
        self.assertEqual(xemu["actions"], {})

    def test_retroarch_does_not_expose_unusable_keyboard_menu(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        retroarch = store.get("retroarch")
        self.assertIsNotNone(retroarch)
        assert retroarch is not None
        self.assertNotIn("emulator_menu", retroarch["capabilities"])
        self.assertNotIn("emulator_menu", retroarch["actions"])

    def test_rejects_incomplete_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "broken.json").write_text('{"id": "broken"}', encoding="utf-8")
            with self.assertRaises(ProfileError):
                ProfileStore(Path(directory)).load()

    def test_rejects_invalid_core_matcher(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "broken.json").write_text(
                '{"id":"broken","name":"Broken","profile_version":1,'
                '"processes":["retroarch"],"argv_contains":"core",'
                '"capabilities":[],"actions":{}}',
                encoding="utf-8",
            )
            with self.assertRaises(ProfileError):
                ProfileStore(Path(directory)).load()


if __name__ == "__main__":
    unittest.main()
