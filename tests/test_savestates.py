import os
import tempfile
import unittest
from pathlib import Path

from companion_savestates import SavestateIndex


class SavestateIndexTests(unittest.TestCase):
    def test_returns_only_states_matching_active_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            states = root / "saves" / "retroarch" / "states"
            states.mkdir(parents=True)
            current = states / "Chrono Trigger.state2"
            current.write_bytes(b"state")
            (states / "Other Game.state2").write_bytes(b"other")
            profile = {
                "savestate_paths": ["saves/retroarch/states"],
                "savestate_patterns": ["{stem}.state*"],
            }
            result = SavestateIndex(root).lookup(profile, "/roms/Chrono Trigger.sfc")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["path"], str(current))
            self.assertEqual(result[0]["slot"], 2)

    def test_orders_states_newest_first(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            states = root / "states"
            states.mkdir()
            older = states / "Game.state1"
            newer = states / "Game.state2"
            older.touch()
            newer.touch()
            os.utime(older, (10, 10))
            os.utime(newer, (20, 20))
            profile = {"savestate_paths": ["states"], "savestate_patterns": ["{stem}.state*"]}
            result = SavestateIndex(root).lookup(profile, "Game.rom")
            self.assertEqual([item["slot"] for item in result], [2, 1])

    def test_handles_unavailable_storage(self):
        profile = {"savestate_paths": ["states"], "savestate_patterns": ["{stem}.state*"]}
        self.assertEqual(SavestateIndex(None).lookup(profile, "Game.rom"), [])

    def test_configured_path_without_emudeck_root_and_search_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "Game [Europe].state1"
            state.write_bytes(b"state")
            (root / "Other.state1").touch()
            (root / "nested").mkdir()
            (root / "nested/Game [Europe].state2").touch()
            profile = {"hotkey_config_format": "retroarch", "savestate_patterns": ["{stem}.state*"],
                       "hotkey_config": {"savestate_search": {"paths": [str(root), str(root), str(root / "absent"), "relative"]}}}
            index = SavestateIndex(None)
            self.assertEqual([item["path"] for item in index.lookup(profile, "Game [Europe].n64")], [str(state)])
            self.assertEqual(index.last_search["matched_files"], 1)
            self.assertEqual(index.last_search["directories"], [
                {"path": str(root), "status": "searched"},
                {"path": str(root / "absent"), "status": "missing_or_not_directory"},
            ])
            index.lookup(profile, None)
            self.assertEqual(index.last_search["directories"], [])

    def test_excludes_preview_images_and_keeps_unknown_slot_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("Game.state1", "Game.state.auto", "Game.state1.png", "Game.state2.JPG", "Game.state1.webp"):
                (root / name).write_bytes(b"data")
            profile = {"savestate_paths": ["."], "savestate_patterns": ["{stem}.state*"]}
            result = SavestateIndex(root).lookup(profile, "Game.rom")
            self.assertEqual({Path(item["path"]).name for item in result}, {"Game.state1", "Game.state.auto"})
            self.assertEqual(next(item for item in result if item["path"].endswith(".auto"))["slot"], None)

    def test_finds_melonds_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            states = root / "saves" / "melonds" / "states"
            states.mkdir(parents=True)
            state = states / "Mario Kart DS.ml3"
            state.write_bytes(b"state")
            profile = {
                "savestate_paths": ["saves/melonds/states"],
                "savestate_patterns": ["{stem}.ml?"],
            }
            result = SavestateIndex(root).lookup(profile, "/roms/Mario Kart DS.nds")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["slot"], 3)


if __name__ == "__main__":
    unittest.main()
