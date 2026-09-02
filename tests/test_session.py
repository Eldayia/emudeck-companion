import unittest

from companion_session import contextual_capabilities


class ContextualCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "capabilities": ["save_state", "load_state", "fast_forward", "emulator_menu", "quit"],
            "capability_rules": [{
                "rom_path_segments": ["atomiswave", "naomi", "naomi2"],
                "remove": ["save_state", "load_state", "fast_forward"],
            }],
        }

    def test_keeps_dreamcast_actions(self):
        actions = contextual_capabilities(self.profile, "/home/deck/Emulation/roms/dreamcast/Sonic.chd")
        self.assertIn("fast_forward", actions)
        self.assertIn("save_state", actions)

    def test_hides_conflicting_arcade_actions(self):
        actions = contextual_capabilities(self.profile, "/home/deck/Emulation/roms/Naomi/Crazy Taxi.zip")
        self.assertEqual(actions, ["emulator_menu", "quit"])

    def test_does_not_match_game_name_substrings(self):
        actions = contextual_capabilities(self.profile, "/roms/dreamcast/Naomi Adventure.chd")
        self.assertIn("fast_forward", actions)


if __name__ == "__main__":
    unittest.main()
