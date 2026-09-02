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


if __name__ == "__main__":
    unittest.main()
