import asyncio
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion_action_engine import ActionEngine
from companion_hotkey_config import (
    MAX_CONFIG_BYTES, SUPPORTED_KEYS, DuckStationHotkeyConfig, keyboard_binding, parse_hotkeys,
)
from companion_models import ProcessInfo
from companion_profiles import ProfileStore
from companion_session import SessionManager


ROOT = Path(__file__).resolve().parents[1]


class HotkeyConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.path = self.home / ".local/share/duckstation/settings.ini"
        self.path.parent.mkdir(parents=True)
        self.store = ProfileStore(ROOT / "defaults/emulators")
        self.store.load()
        self.profile = self.store.get("duckstation")
        self.process = ProcessInfo(42, "DuckStation.App", (
            "/home/deck/Applications/DuckStation.AppImage", "-batch", "/roms/Silent Hill.chd",
        ))
        self.reader = DuckStationHotkeyConfig(self.home, self.home / "proc")

    def resolve(self, text):
        self.path.write_text(text, encoding="utf-8")
        return self.reader(self.profile, self.process)

    def test_parses_repeated_hotkeys_without_collecting_other_settings(self):
        parsed = parse_hotkeys(
            "\ufeff[Achievements]\nToken = private\n[Hotkeys]\n"
            "SaveSelectedSaveState = SDL-0/A\nSaveSelectedSaveState = Keyboard/F5\n"
            "TogglePause =\n; comment\n[Other]\nPassword = private\n"
        )
        self.assertEqual(parsed, {
            "SaveSelectedSaveState": ["SDL-0/A", "Keyboard/F5"], "TogglePause": [""],
        })

    def test_keyboard_chords_and_rejected_inputs(self):
        self.assertEqual(keyboard_binding("Keyboard/F5 & Keyboard/Control"), ["leftctrl", "f5"])
        self.assertEqual(keyboard_binding("Keyboard/Shift & Keyboard/K"), ["leftshift", "k"])
        for value in ("", "SDL-0/A", "Keyboard/F5 & SDL-0/A", "Keyboard/F25",
                      "Keyboard/Alt", "Keyboard/K & Keyboard/K", "Keyboard/Shift+F5"):
            with self.subTest(value=value):
                self.assertIsNone(keyboard_binding(value))

    def test_configured_binding_is_read_only_and_does_not_mutate_profile(self):
        original = json.dumps(self.profile, sort_keys=True)
        text = "[Hotkeys]\nSaveSelectedSaveState = SDL-0/A\nSaveSelectedSaveState = Keyboard/Shift & Keyboard/K\n"
        result = self.resolve(text)
        self.assertEqual(result["actions"]["save_state"]["keys"], ["leftshift", "k"])
        self.assertIn("save_state", result["capabilities"])
        self.assertIn("quit", result["capabilities"])
        self.assertEqual(self.path.read_text(encoding="utf-8"), text)
        self.assertEqual(json.dumps(self.profile, sort_keys=True), original)

    def test_missing_file_uses_explicit_fallback_but_not_false_fast_forward_toggle(self):
        result = self.reader(self.profile, self.process)
        self.assertEqual(result["hotkey_config"]["status"], "fallback")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f2"])
        self.assertIn("save_state", result["capabilities"])
        self.assertNotIn("fast_forward", result["capabilities"])

    def test_empty_absent_and_controller_only_bindings_do_not_fall_back(self):
        for text in ("[Hotkeys]\n", "[Main]\nSettingsVersion = 3\n",
                     "[Hotkeys]\nSaveSelectedSaveState =\nLoadSelectedSaveState = SDL-0/A\n"):
            with self.subTest(text=text):
                result = self.resolve(text)
                self.assertEqual(result["capabilities"], ["quit"])
                self.assertEqual(result["hotkey_config"]["status"], "configured")

    def test_hold_is_not_used_as_toggle(self):
        result = self.resolve("[Hotkeys]\nFastForward = Keyboard/Tab\n")
        self.assertNotIn("fast_forward", result["capabilities"])
        result = self.resolve("[Hotkeys]\nToggleFastForward = Keyboard/T\n")
        self.assertIn("fast_forward", result["capabilities"])
        self.assertEqual(result["actions"]["fast_forward"]["keys"], ["t"])

    def test_malformed_and_oversized_configs_fail_closed(self):
        for text in ("[Hotkeys\nSaveSelectedSaveState = Keyboard/K", ";" * (MAX_CONFIG_BYTES + 1)):
            result = self.resolve(text)
            self.assertEqual(result["hotkey_config"]["status"], "unavailable")
            self.assertEqual(result["capabilities"], ["quit"])

    def test_cache_reloads_modified_file_and_drops_deleted_file(self):
        with patch("companion_hotkey_config.parse_hotkeys", wraps=parse_hotkeys) as parser:
            self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/K\n")
            self.reader(self.profile, self.process)
            self.assertEqual(parser.call_count, 1)
            result = self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/F12\n")
            self.assertEqual(parser.call_count, 2)
            self.assertEqual(result["actions"]["save_state"]["keys"], ["f12"])
        self.path.unlink()
        self.assertEqual(self.reader(self.profile, self.process)["hotkey_config"]["status"], "fallback")

    def test_flatpak_environment_selects_legacy_config_not_appimage(self):
        self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/K\n")
        flatpak_dir = self.home / ".var/app/org.duckstation.DuckStation/config"
        (flatpak_dir / "duckstation").mkdir(parents=True)
        (flatpak_dir / "duckstation/settings.ini").write_text(
            "[Hotkeys]\nSaveSelectedSaveState = Keyboard/F7\n", encoding="utf-8",
        )
        proc = self.home / "proc/42"
        proc.mkdir(parents=True)
        (proc / "environ").write_bytes(
            f"FLATPAK_ID=org.duckstation.DuckStation\0XDG_CONFIG_HOME={flatpak_dir}\0SECRET=private".encode()
        )
        result = self.reader(self.profile, self.process)
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f7"])
        self.assertNotIn("private", json.dumps(result))

    def test_native_missing_config_does_not_select_stale_flatpak_file(self):
        legacy = self.home / ".var/app/org.duckstation.DuckStation/config/duckstation/settings.ini"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("[Hotkeys]\nSaveSelectedSaveState = Keyboard/K\n", encoding="utf-8")
        self.assertEqual(self.reader(self.profile, self.process)["hotkey_config"]["status"], "fallback")

    def test_same_pid_refresh_updates_bindings_and_retains_slot(self):
        self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/K\n")
        manager = SessionManager(self.store, process_provider=lambda: [self.process], profile_provider=self.reader)
        session = manager.refresh()
        self.assertIsNotNone(session)
        session.slot = 3
        self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/F12\n")
        refreshed = manager.refresh()
        self.assertIs(refreshed, session)
        self.assertEqual(refreshed.slot, 3)
        self.assertEqual(refreshed.actions["save_state"]["keys"], ["f12"])
        self.resolve("[Hotkeys]\nSaveSelectedSaveState =\n")
        self.assertNotIn("save_state", manager.refresh().capabilities)

    def test_other_emulators_are_unchanged(self):
        profile = self.store.get("cemu")
        self.assertIs(self.reader(profile, self.process), profile)

    def test_unreadable_file_disables_bindings_instead_of_using_defaults(self):
        self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/K\n")
        self.reader._signature = None
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            result = self.reader(self.profile, self.process)
        self.assertEqual(result["hotkey_config"]["status"], "unavailable")
        self.assertEqual(result["capabilities"], ["quit"])

    def test_action_engine_dispatches_resolved_keys_and_rejects_disabled_actions(self):
        self.resolve("[Hotkeys]\nSaveSelectedSaveState = Keyboard/Control & Keyboard/K\n")
        manager = SessionManager(self.store, process_provider=lambda: [self.process], profile_provider=self.reader)
        session = manager.refresh()
        engine = ActionEngine(frontend_input=True)
        saved = asyncio.run(engine.execute(session, "save_state"))
        self.assertTrue(saved.ok)
        self.assertEqual(saved.keys, ["leftctrl", "k"])
        self.assertEqual(saved.dispatch, "steam_input")
        loaded = asyncio.run(engine.execute(session, "load_state"))
        self.assertFalse(loaded.ok)

    def test_all_accepted_keys_have_a_steam_frontend_mapping(self):
        source = (ROOT / "src/hotkey.ts").read_text(encoding="utf-8")
        names = set(re.findall(r'^\s*"?([a-z0-9]+)"?: EHIDKeyboardKey\.', source, re.MULTILINE))
        self.assertFalse(SUPPORTED_KEYS - names, SUPPORTED_KEYS - names)


if __name__ == "__main__":
    unittest.main()
