import unittest

from companion_game_overrides import game_override_key, hidden_actions, session_payload
from companion_models import Session


class GameOverrideTests(unittest.TestCase):
    def setUp(self):
        self.session = Session(
            emulator="duckstation",
            emulator_name="DuckStation",
            pid=42,
            argv=["duckstation", "/roms/Silent Hill.chd"],
            rom="/roms/Silent Hill.chd",
            game="Silent Hill",
            platform="PlayStation",
            capabilities=["save_state", "fast_forward", "quit"],
            actions={},
            started_at=1.0,
        )

    def test_applies_hidden_actions_without_mutating_session(self):
        key = game_override_key(self.session)
        settings = {"game_overrides": {key: {"hidden_actions": ["fast_forward"]}}}
        payload = session_payload(self.session, settings)
        self.assertEqual(payload["game_key"], key)
        self.assertEqual(payload["available_capabilities"], self.session.capabilities)
        self.assertEqual(payload["capabilities"], ["save_state", "quit"])
        self.assertEqual(self.session.capabilities, ["save_state", "fast_forward", "quit"])
        self.assertEqual(hidden_actions(self.session, settings), {"fast_forward"})

    def test_needs_a_rom_for_an_override(self):
        self.session.rom = None
        self.assertIsNone(game_override_key(self.session))
        self.assertEqual(hidden_actions(self.session, {"game_overrides": {}}), set())


if __name__ == "__main__":
    unittest.main()
