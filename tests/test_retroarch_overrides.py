import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion_action_engine import ActionEngine
from companion_models import ProcessInfo
from companion_profiles import ProfileStore
from companion_retroarch_config import CORE_NAMES, RetroArchHotkeyConfig
from companion_session import SessionManager


ROOT = Path(__file__).resolve().parents[1]


class RetroArchOverrideTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config = self.home / ".config/retroarch/retroarch.cfg"
        self.config.parent.mkdir(parents=True)
        self.override_root = self.config.parent / "config"
        self.core = "Mupen64Plus-Next"
        self.core_dir = self.override_root / self.core
        self.core_dir.mkdir(parents=True)
        self.rom = self.home / "roms/n64/Doom 64 (Europe).n64"
        self.store = ProfileStore(ROOT / "defaults/emulators")
        self.store.load()
        self.profile = self.store.get("retroarch")
        self.process = ProcessInfo(42, "retroarch", (
            "retroarch", "-L", "/cores/mupen64plus_next_libretro.so", str(self.rom),
        ))
        self.reader = RetroArchHotkeyConfig(self.home, self.home / "proc")
        self.config.write_text(
            f'rgui_config_directory = "{self.override_root}"\ninput_save_state = "f2"\n', encoding="utf-8",
        )

    def layer(self, name, text):
        path = self.core_dir / (name + ".cfg")
        path.write_text(text, encoding="utf-8")
        return path

    def resolve(self):
        return self.reader(self.profile, self.process)

    def test_global_core_directory_game_priority_and_read_only(self):
        original_profile = json.dumps(self.profile, sort_keys=True)
        paths = [self.config,
                 self.layer(self.core, 'input_save_state = "f3"\ninput_load_state = "f5"'),
                 self.layer("n64", 'input_save_state = "f6"\ninput_pause_toggle = "k"'),
                 self.layer(self.rom.stem, 'input_save_state = "f9"')]
        before = {path: path.read_bytes() for path in paths}
        result = self.resolve()
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f9"])
        self.assertEqual(result["actions"]["load_state"]["keys"], ["f5"])
        self.assertEqual(result["actions"]["pause"]["keys"], ["k"])
        report = result["hotkey_config"]["overrides"]
        self.assertEqual(report["status"], "applied")
        self.assertEqual([layer["level"] for layer in report["layers"]], ["core", "directory", "game"])
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        self.assertEqual(json.dumps(self.profile, sort_keys=True), original_profile)

    def test_game_overrides_appendconfig_and_enabler_is_resolved_after_merge(self):
        extra = self.home / "extra.cfg"
        extra.write_text('input_save_state = "f8"\ninput_enable_hotkey = "ctrl"', encoding="utf-8")
        self.process = ProcessInfo(42, "retroarch", self.process.argv + ("--appendconfig", str(extra)))
        self.layer(self.rom.stem, 'input_save_state = "f9"\ninput_enable_hotkey = "shift"')
        result = self.resolve()
        self.assertEqual(result["actions"]["save_state"]["keys"], ["leftshift", "f9"])

    def test_auto_overrides_disabled_and_invalid_flag(self):
        self.layer(self.rom.stem, 'input_save_state = "f9"')
        base = self.config.read_text(encoding="utf-8")
        for flag in ("false", "0"):
            self.config.write_text(base + f'auto_overrides_enable = "{flag}"', encoding="utf-8")
            result = self.resolve()
            self.assertEqual(result["hotkey_config"]["overrides"]["status"], "disabled")
            self.assertEqual(result["actions"]["save_state"]["keys"], ["f2"])
        self.config.write_text(base + 'auto_overrides_enable = "perhaps"', encoding="utf-8")
        self.assertEqual(self.resolve()["capabilities"], [])

    def test_unknown_core_never_scans_or_applies_other_core_files(self):
        self.layer(self.rom.stem, 'input_save_state = "f9"')
        self.process = ProcessInfo(42, "retroarch", ("retroarch", "-L", "/cores/unknown_libretro.so", str(self.rom)))
        result = self.resolve()
        self.assertEqual(result["hotkey_config"]["overrides"]["status"], "not_resolved")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f2"])
        self.assertEqual(len(result["hotkey_config"]["paths"]), 1)

    def test_missing_directory_setting_does_not_guess_default_folder(self):
        self.layer(self.rom.stem, 'input_save_state = "f9"')
        self.config.write_text('input_save_state = "f2"', encoding="utf-8")
        result = self.resolve()
        self.assertEqual(result["hotkey_config"]["overrides"]["status"], "not_resolved")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f2"])

    def test_explicit_default_directory_uses_base_config_parent(self):
        self.config.write_text('rgui_config_directory = "default"', encoding="utf-8")
        directory = self.config.parent / self.core
        directory.mkdir()
        (directory / (self.rom.stem + ".cfg")).write_text('input_save_state = "f9"', encoding="utf-8")
        self.assertEqual(self.resolve()["actions"]["save_state"]["keys"], ["f9"])

    def test_unknown_application_relative_directory_is_not_guessed(self):
        self.config.write_text('rgui_config_directory = ":/config"', encoding="utf-8")
        self.assertEqual(self.resolve()["hotkey_config"]["overrides"]["status"], "not_resolved")

    def test_nested_include_and_disabled_binding_in_override(self):
        self.layer("keys", 'input_save_state = "nul"\ninput_enable_hotkey = "ctrl"')
        self.layer(self.rom.stem, '#include "keys.cfg"\ninput_pause_toggle = "k"')
        result = self.resolve()
        self.assertNotIn("save_state", result["capabilities"])
        self.assertEqual(result["actions"]["pause"]["keys"], ["leftctrl", "k"])
        self.assertNotIn("emulator_menu", result["capabilities"])
        self.assertNotIn("rewind", result["capabilities"])

    def test_malformed_or_broken_include_override_fails_closed(self):
        for text in ('input_save_state = "f9', '#include "missing.cfg"'):
            self.layer(self.rom.stem, text)
            result = self.resolve()
            self.assertEqual(result["hotkey_config"]["status"], "unavailable")
            self.assertEqual(result["capabilities"], [])

    def test_nonexistent_overrides_leave_global_bindings_and_report_none(self):
        result = self.resolve()
        self.assertEqual(result["hotkey_config"]["overrides"]["status"], "none")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f2"])

    def test_same_pid_refresh_updates_override_and_preserves_slot(self):
        path = self.layer(self.rom.stem, 'input_save_state = "f9"')
        manager = SessionManager(self.store, process_provider=lambda: [self.process], profile_provider=self.reader)
        session = manager.refresh()
        session.slot = 4
        path.write_text('input_save_state = "f12"', encoding="utf-8")
        self.assertIs(manager.refresh(), session)
        self.assertEqual(session.slot, 4)
        self.assertEqual(session.actions["save_state"]["keys"], ["f12"])
        path.unlink()
        self.assertEqual(manager.refresh().actions["save_state"]["keys"], ["f2"])

    def test_game_change_selects_only_the_new_game_file(self):
        self.layer(self.rom.stem, 'input_save_state = "f9"')
        self.layer("Other", 'input_save_state = "f10"')
        self.assertEqual(self.resolve()["actions"]["save_state"]["keys"], ["f9"])
        self.process = ProcessInfo(43, "retroarch", self.process.argv[:-1] + (str(self.rom.parent / "Other.n64"),))
        self.assertEqual(self.resolve()["actions"]["save_state"]["keys"], ["f10"])

    def test_core_cli_forms_and_known_core_names(self):
        for stem, core in CORE_NAMES.items():
            directory = self.override_root / core
            directory.mkdir(exist_ok=True)
            (directory / (core + ".cfg")).write_text('input_save_state = "f9"', encoding="utf-8")
            for args in (("-L", f"/cores/{stem}.so"), (f"-L/cores/{stem}.so",),
                         ("--libretro", f"/cores/{stem}.so"), (f"--libretro=/cores/{stem}.so",)):
                self.process = ProcessInfo(42, "retroarch", ("retroarch", *args, str(self.rom)))
                result = self.resolve()
                self.assertEqual(result["actions"]["save_state"]["keys"], ["f9"])
                self.assertEqual(result["hotkey_config"]["overrides"]["core"], core)

    def test_directory_selection_not_changed_midway_by_an_override(self):
        self.layer(self.core, 'rgui_config_directory = "missing"\ninput_save_state = "f5"')
        self.layer(self.rom.stem, 'input_save_state = "f9"')
        self.assertEqual(self.resolve()["actions"]["save_state"]["keys"], ["f9"])

    def test_archive_member_not_used_to_guess_game_name(self):
        self.process = ProcessInfo(42, "retroarch", self.process.argv[:-1] + (str(self.rom) + "#inner.n64",))
        self.assertEqual(self.resolve()["hotkey_config"]["overrides"]["status"], "not_resolved")

    def test_engine_uses_final_override_chord(self):
        self.layer(self.rom.stem, 'input_enable_hotkey = "alt"\ninput_save_state = "f9"')
        manager = SessionManager(self.store, process_provider=lambda: [self.process], profile_provider=self.reader)
        result = asyncio.run(ActionEngine(frontend_input=True).execute(manager.refresh(), "save_state"))
        self.assertTrue(result.ok)
        self.assertEqual(result.keys, ["leftalt", "f9"])

    def test_relative_directory_and_rom_use_emulator_cwd(self):
        cwd = self.home / "proc/42/cwd"
        cwd.mkdir(parents=True)
        directory = cwd / "overrides" / self.core
        directory.mkdir(parents=True)
        (directory / "n64.cfg").write_text('input_save_state = "f9"', encoding="utf-8")
        self.config.write_text('rgui_config_directory = "overrides"', encoding="utf-8")
        self.process = ProcessInfo(42, "retroarch", self.process.argv[:-1] + ("roms/n64/Game.n64",))
        self.assertEqual(self.resolve()["actions"]["save_state"]["keys"], ["f9"])

    def test_override_permission_error_is_not_treated_as_absence(self):
        target = self.layer(self.core, 'input_save_state = "f9"')
        original_stat = Path.stat

        def denied(path, *args, **kwargs):
            if path == target:
                raise PermissionError("denied")
            return original_stat(path, *args, **kwargs)

        with patch.object(Path, "stat", denied):
            result = self.resolve()
        self.assertEqual(result["hotkey_config"]["overrides"]["status"], "unavailable")
        self.assertEqual(result["capabilities"], [])


if __name__ == "__main__":
    unittest.main()
