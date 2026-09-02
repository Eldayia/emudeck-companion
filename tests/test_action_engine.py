import unittest

from companion_action_engine import ActionEngine
from companion_input_backends import InputBackend
from companion_models import Session


class FakeInputBackend(InputBackend):
    name = "fake"

    def __init__(self):
        self.calls = []

    async def press(self, keys, pid):
        self.calls.append((keys, pid))


def make_session() -> Session:
    return Session(
        emulator="test",
        emulator_name="Test Emulator",
        pid=123,
        argv=["test", "game.rom"],
        rom="game.rom",
        game="Game",
        platform="Test",
        capabilities=["save_state", "slot_next", "fast_forward"],
        actions={
            "save_state": {"label": "Save State", "method": "hotkey", "keys": ["f1"]},
            "slot_next": {"label": "Next Slot", "method": "hotkey", "keys": ["f2"], "maximum": 2},
            "fast_forward": {"label": "Fast Forward", "method": "hotkey", "keys": ["tab"], "mode": "toggle"},
        },
        started_at=0,
        slot=1,
    )


class ActionEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_action_without_session(self):
        result = await ActionEngine(FakeInputBackend()).execute(None, "save_state")
        self.assertFalse(result.ok)

    async def test_rejects_unsupported_action(self):
        result = await ActionEngine(FakeInputBackend()).execute(make_session(), "quit")
        self.assertFalse(result.ok)

    async def test_dispatches_hotkey_and_updates_slot(self):
        backend = FakeInputBackend()
        session = make_session()
        result = await ActionEngine(backend, debounce_ms=0).execute(session, "slot_next")
        self.assertTrue(result.ok)
        self.assertEqual(session.slot, 2)
        self.assertEqual(backend.calls, [(["f2"], 123)])

    async def test_tracks_toggle_state(self):
        engine = ActionEngine(FakeInputBackend(), debounce_ms=0)
        session = make_session()
        first = await engine.execute(session, "fast_forward")
        second = await engine.execute(session, "fast_forward")
        self.assertTrue(first.active)
        self.assertFalse(second.active)

    async def test_select_slot_needs_no_input_backend(self):
        session = make_session()
        session.actions["slot_next"]["method"] = "select_slot"
        result = await ActionEngine(debounce_ms=0).execute(session, "slot_next")
        self.assertTrue(result.ok)
        self.assertEqual(session.slot, 2)

    async def test_prepares_hotkey_for_steam_frontend(self):
        session = make_session()
        engine = ActionEngine(debounce_ms=0, frontend_input=True)
        result = await engine.execute(session, "save_state")
        self.assertTrue(result.ok)
        self.assertEqual(result.dispatch, "steam_input")
        self.assertEqual(result.keys, ["f1"])

    async def test_can_hide_slot_from_save_message(self):
        session = make_session()
        session.actions["save_state"]["show_slot"] = False
        result = await ActionEngine(FakeInputBackend(), debounce_ms=0).execute(session, "save_state")
        self.assertEqual(result.message, "Save State")

    async def test_wraps_emulator_slot_when_configured(self):
        engine = ActionEngine(FakeInputBackend(), debounce_ms=0)
        session = make_session()
        session.slot = 2
        session.actions["slot_next"]["wrap"] = True
        session.actions["slot_next"]["minimum"] = 0
        await engine.execute(session, "slot_next")
        self.assertEqual(session.slot, 0)


if __name__ == "__main__":
    unittest.main()
