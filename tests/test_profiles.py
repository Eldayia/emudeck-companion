import tempfile
import unittest
from pathlib import Path

from companion_profiles import ProfileError, ProfileStore


ROOT = Path(__file__).resolve().parents[1]


class ProfileStoreTests(unittest.TestCase):
    def test_loads_all_mvp_profiles(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        self.assertEqual({profile["id"] for profile in store.profiles}, {
            "cemu", "duckstation", "pcsx2", "dolphin", "retroarch"
        })

    def test_cemu_has_no_savestate_capability(self):
        store = ProfileStore(ROOT / "defaults" / "emulators")
        store.load()
        cemu = store.get("cemu")
        assert cemu is not None
        self.assertNotIn("save_state", cemu["capabilities"])
        self.assertNotIn("load_state", cemu["capabilities"])

    def test_rejects_incomplete_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "broken.json").write_text('{"id": "broken"}', encoding="utf-8")
            with self.assertRaises(ProfileError):
                ProfileStore(Path(directory)).load()


if __name__ == "__main__":
    unittest.main()
