import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

from companion_models import ProcessInfo
from companion_session import SessionManager


class SessionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "id": "emu", "name": "Emulator", "processes": ["emu"], "default_slot": 0,
            "capabilities": ["save_state", "pause"], "rom_extensions": ["sfc"],
            "actions": {"save_state": {"keys": ["f2"]}, "pause": {"keys": ["p"], "mode": "toggle"}},
        }
        self.store = SimpleNamespace(profiles=[self.profile])
        self.processes = [ProcessInfo(42, "emu", ("emu", "/roms/first.sfc"), 100)]
        self.metadata = Mock(side_effect=lambda rom: {"name": rom, "desc": f"Description: {rom}"} if rom else {})
        self.documents = Mock(side_effect=lambda rom, _: [{"id": rom}] if rom else [])
        self.states = Mock(side_effect=lambda _, rom: [{"path": rom + ".state"}] if rom else [])
        self.manager = SessionManager(self.store, process_provider=lambda: self.processes,
                                      metadata_provider=self.metadata, document_provider=self.documents,
                                      savestate_provider=self.states)

    def test_same_process_preserves_identity_clock_slot_and_toggles(self):
        first = self.manager.refresh()
        first.slot = 7
        first.toggles["pause"] = True
        self.assertIs(self.manager.refresh(), first)
        self.assertEqual(first.slot, 7)
        self.assertTrue(first.toggles["pause"])
        self.assertEqual(first.process_started_ticks, 100)
        self.metadata.assert_called_once_with("/roms/first.sfc")

    def test_reused_pid_with_different_start_ticks_resets_session(self):
        first = self.manager.refresh()
        first.slot = 8
        first.toggles["pause"] = True
        self.processes = [ProcessInfo(42, "emu", ("emu", "/roms/first.sfc"), 200)]
        second = self.manager.refresh()
        self.assertNotEqual(first.session_id, second.session_id)
        self.assertEqual(second.slot, 0)
        self.assertEqual(second.toggles, {})
        self.assertEqual(second.process_started_ticks, 200)

    def test_new_process_same_rom_starts_new_session(self):
        first = self.manager.refresh()
        self.processes = [ProcessInfo(43, "emu", ("emu", "/roms/first.sfc"), 200)]
        self.assertNotEqual(self.manager.refresh().session_id, first.session_id)

    def test_changed_rom_arguments_replace_all_game_data(self):
        first = self.manager.refresh()
        first.slot = 6
        first.toggles["pause"] = True
        first.discs = ["old1", "old2"]
        first.current_disc = 2
        self.processes = [ProcessInfo(42, "emu", ("emu", "/roms/second.sfc"), 100)]
        second = self.manager.refresh()
        self.assertNotEqual(second.session_id, first.session_id)
        self.assertEqual(second.game, "/roms/second.sfc")
        self.assertEqual(second.metadata["desc"], "Description: /roms/second.sfc")
        self.assertEqual(second.documents, [{"id": "/roms/second.sfc"}])
        self.assertEqual(second.savestates, [{"path": "/roms/second.sfc.state"}])
        self.assertEqual(second.slot, 0)
        self.assertEqual(second.toggles, {})
        self.assertEqual(second.discs, [])
        self.assertIsNone(second.current_disc)

    def test_removed_content_argument_does_not_keep_previous_game(self):
        self.manager.refresh()
        self.processes = [ProcessInfo(42, "emu", ("emu",), 100)]
        current = self.manager.refresh()
        self.assertIsNone(current.rom)
        self.assertIsNone(current.game)
        self.assertEqual(current.metadata, {})
        self.assertEqual(current.documents, [])
        self.assertEqual(current.savestates, [])

    def test_profile_change_with_same_pid_and_argv_resets_identity(self):
        first = self.manager.refresh()
        profile = deepcopy(self.profile)
        profile.update(id="specific", name="Specific core")
        self.store.profiles = [profile]
        second = self.manager.refresh()
        self.assertNotEqual(second.session_id, first.session_id)
        self.assertEqual(second.emulator, "specific")

    def test_launch_core_argument_change_resets_identity_even_with_same_rom(self):
        self.processes = [ProcessInfo(42, "emu", ("emu", "-L", "core1.so", "/roms/first.sfc"), 100)]
        first = self.manager.refresh()
        self.processes = [ProcessInfo(42, "emu", ("emu", "-L", "core2.so", "/roms/first.sfc"), 100)]
        second = self.manager.refresh()
        self.assertEqual(first.rom, second.rom)
        self.assertNotEqual(first.session_id, second.session_id)

    def test_exit_and_return_resets_even_with_identical_process_snapshot(self):
        first = self.manager.refresh()
        old = self.processes
        self.processes = []
        self.assertIsNone(self.manager.refresh())
        self.assertIsNone(self.manager.as_dict())
        self.processes = old
        self.assertNotEqual(self.manager.refresh().session_id, first.session_id)

    def test_profile_binding_refresh_does_not_reset_session_or_slot(self):
        first = self.manager.refresh()
        first.slot = 9
        first.toggles["pause"] = True
        updated = deepcopy(self.profile)
        updated["actions"]["pause"]["keys"] = ["f9"]
        self.store.profiles = [updated]
        self.assertIs(self.manager.refresh(), first)
        self.assertEqual(first.slot, 9)
        self.assertEqual(first.toggles, {})
        self.assertEqual(first.actions["pause"]["keys"], ["f9"])

    def test_forced_refresh_and_serialized_identity(self):
        first = self.manager.refresh()
        payload = first.as_dict()
        self.assertEqual(payload["session_id"], first.session_id)
        self.assertEqual(payload["process_started_ticks"], 100)
        self.manager.current = None
        self.assertNotEqual(self.manager.refresh().session_id, first.session_id)


if __name__ == "__main__":
    unittest.main()
