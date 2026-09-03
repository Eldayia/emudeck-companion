import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion_action_engine import ActionEngine
from companion_hotkey_config import SUPPORTED_KEYS
from companion_models import ProcessInfo
from companion_profiles import ProfileStore
from companion_retroarch_config import (
    KEYS, MAX_CONFIG_BYTES, MAX_CONFIG_FILES, RetroArchHotkeyConfig, parse_retroarch_config,
)
from companion_session import SessionManager


ROOT = Path(__file__).resolve().parents[1]


class RetroArchConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.path = self.home / ".config/retroarch/retroarch.cfg"
        self.path.parent.mkdir(parents=True)
        self.proc = self.home / "proc/42"
        self.proc.mkdir(parents=True)
        self.process = ProcessInfo(42, "retroarch", ("retroarch", "-L", "/cores/snes9x.so", "/roms/game.sfc"))
        self.store = ProfileStore(ROOT / "defaults/emulators")
        self.store.load()
        self.profile = self.store.get("retroarch")
        self.reader = RetroArchHotkeyConfig(self.home, self.home / "proc")

    def resolve(self, text, process=None, profile=None):
        self.path.write_text(text, encoding="utf-8")
        return self.reader(profile or self.profile, process or self.process)

    def process_with(self, *args):
        return ProcessInfo(42, "retroarch", ("retroarch", *args, "/roms/game.sfc"))

    def test_parser_keeps_only_hotkey_settings_and_include_order(self):
        result = parse_retroarch_config(
            '\ufeff# comment\ninput_save_state = "f5" # note\n'
            'cheevos_token = "private"\n#include "other.cfg"\n'
            'input_load_state=f6\ninput_enable_hotkey = "nul"\n'
        )
        self.assertEqual(result, [
            ("input_save_state", "f5"), ("#include", "other.cfg"),
            ("input_load_state", "f6"), ("input_enable_hotkey", "nul"),
        ])

    def test_emudeck_nul_enabler_does_not_disable_keyboard_shortcuts(self):
        original = json.dumps(self.profile, sort_keys=True)
        text = 'input_enable_hotkey = "nul"\ninput_enable_hotkey_btn = "8"\ninput_save_state = "f5"\n'
        result = self.resolve(text)
        self.assertEqual(result["hotkey_config"]["status"], "configured")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f5"])
        self.assertIn("save_state", result["capabilities"])
        self.assertEqual(json.dumps(self.profile, sort_keys=True), original)
        self.assertEqual(self.path.read_text(encoding="utf-8"), text)
        self.assertNotIn("emulator_menu", result["capabilities"])

    def test_configured_enabler_is_prepended_to_configured_and_default_keys(self):
        result = self.resolve('input_enable_hotkey = "ctrl"\ninput_save_state = "num5"\n')
        self.assertEqual(result["actions"]["save_state"]["keys"], ["leftctrl", "5"])
        self.assertEqual(result["actions"]["load_state"]["keys"], ["leftctrl", "f4"])
        self.assertIn("default", result["actions"]["load_state"]["binding_source"])

    def test_network_settings_default_custom_and_invalid_ports(self):
        self.assertEqual(self.resolve("")["hotkey_config"]["network_settings"], {
            "enabled_on_disk": False, "port": 55355,
        })
        self.assertEqual(self.resolve('network_cmd_enable = "true"\nnetwork_cmd_port = "12345"')["hotkey_config"]["network_settings"], {
            "enabled_on_disk": True, "port": 12345,
        })
        for value in ("invalid", "-1", "999999", ""):
            result = self.resolve(f'network_cmd_port = "{value}"')
            self.assertEqual(result["hotkey_config"]["network_settings"]["port"], 0)

    def test_nul_and_unsupported_keyboard_binding_never_fall_back(self):
        for value in ("nul", "", "rctrl", "ctrl+f5", "keypad1", "f25"):
            result = self.resolve(f'input_save_state = "{value}"\ninput_save_state_btn = "3"\n')
            self.assertNotIn("save_state", result["capabilities"])

    def test_unsupported_enabler_and_merged_controller_gate_disable_actions(self):
        for text in ('input_enable_hotkey = "rctrl"', 'input_enable_hotkey = ""',
                     'input_hotkey_device_merge = "true"', 'input_hotkey_device_merge = "unknown"'):
            with self.subTest(text=text):
                self.assertEqual(self.resolve(text)["capabilities"], [])
        result = self.resolve('input_enable_hotkey = "shift"\ninput_hotkey_device_merge = "true"')
        self.assertIn("save_state", result["capabilities"])
        self.assertEqual(result["actions"]["save_state"]["keys"], ["leftshift", "f2"])

    def test_action_cannot_share_enabler_key(self):
        result = self.resolve('input_enable_hotkey = "p"\ninput_pause_toggle = "p"')
        self.assertNotIn("pause", result["capabilities"])
        self.assertIn("save_state", result["capabilities"])

    def test_missing_file_and_missing_entries_use_explicit_defaults(self):
        result = self.reader(self.profile, self.process)
        self.assertEqual(result["hotkey_config"]["status"], "fallback")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f2"])
        result = self.resolve('video_driver = "vulkan"')
        self.assertEqual(result["hotkey_config"]["status"], "configured")
        self.assertIn("default", result["actions"]["save_state"]["binding_source"])

    def test_hold_rewind_and_unconfigured_disc_actions_are_hidden(self):
        result = self.resolve('input_rewind = "r"\ninput_hold_fast_forward = "l"')
        self.assertNotIn("rewind", result["capabilities"])
        self.assertNotIn("previous_disc", result["capabilities"])
        self.assertNotIn("next_disc", result["capabilities"])
        self.assertEqual(result["actions"]["fast_forward"]["keys"], ["space"])
        result = self.resolve('input_disk_prev = "num8"\ninput_disk_next = "num9"')
        self.assertEqual(result["actions"]["previous_disc"]["keys"], ["8"])
        self.assertEqual(result["actions"]["next_disc"]["keys"], ["9"])

    def test_duplicate_entries_and_includes_use_first_occurrence(self):
        include = self.path.parent / "included.cfg"
        include.write_text('input_save_state = "f6"\ninput_load_state = "f9"', encoding="utf-8")
        result = self.resolve('input_save_state = "f5"\n#include "included.cfg"\ninput_save_state = "f7"')
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f5"])
        self.assertEqual(result["actions"]["load_state"]["keys"], ["f9"])
        result = self.resolve('#include "included.cfg"\ninput_save_state = "f5"')
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f6"])

    def test_appendconfig_overrides_base_and_last_extra_wins(self):
        extra1, extra2 = self.home / "extra 1.cfg", self.home / "extra2.cfg"
        extra1.write_text('input_save_state = "f6"\ninput_enable_hotkey = "ctrl"', encoding="utf-8")
        extra2.write_text('input_save_state = "f7"', encoding="utf-8")
        for flag in (("--appendconfig", f"{extra1}|{extra2}"), (f"--appendconfig={extra1}|{extra2}",)):
            result = self.resolve('input_save_state = "f5"', self.process_with(*flag))
            self.assertEqual(result["actions"]["save_state"]["keys"], ["leftctrl", "f7"])
            self.assertEqual(len(result["hotkey_config"]["paths"]), 3)

    def test_explicit_config_forms_take_priority(self):
        custom = self.home / "custom.cfg"
        custom.write_text('input_save_state = "f9"', encoding="utf-8")
        for args in (("-c", str(custom)), ("--config", str(custom)), (f"--config={custom}",), (f"-c{custom}",)):
            result = self.resolve('input_save_state = "f5"', self.process_with(*args))
            self.assertEqual(result["actions"]["save_state"]["keys"], ["f9"])

    def test_relative_cli_path_uses_emulator_cwd(self):
        cwd = self.proc / "cwd"
        cwd.mkdir()
        (cwd / "custom.cfg").write_text('input_save_state = "f9"', encoding="utf-8")
        result = self.resolve('input_save_state = "f5"', self.process_with("-c", "custom.cfg"))
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f9"])
        (cwd / "custom.cfg").unlink()
        cwd.rmdir()
        result = self.reader(self.profile, self.process_with("-c", "custom.cfg"))
        self.assertEqual(result["hotkey_config"]["status"], "unavailable")

    def test_flatpak_config_selected_from_environment_without_secret_leak(self):
        flatpak = self.home / ".var/app/org.libretro.RetroArch/config"
        (flatpak / "retroarch").mkdir(parents=True)
        (flatpak / "retroarch/retroarch.cfg").write_text('input_save_state = "f8"', encoding="utf-8")
        (self.proc / "environ").write_bytes(
            f"FLATPAK_ID=org.libretro.RetroArch\0XDG_CONFIG_HOME={flatpak}\0TOKEN=private".encode()
        )
        result = self.resolve('input_save_state = "f5"')
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f8"])
        self.assertNotIn("private", json.dumps(result))

    def test_native_xdg_and_legacy_path_without_using_stale_flatpak(self):
        custom = self.home / "xdg"
        (custom / "retroarch").mkdir(parents=True)
        (custom / "retroarch/retroarch.cfg").write_text('input_save_state = "f9"', encoding="utf-8")
        (self.proc / "environ").write_bytes(f"XDG_CONFIG_HOME={custom}\0".encode())
        self.assertEqual(self.reader(self.profile, self.process)["actions"]["save_state"]["keys"], ["f9"])
        (self.proc / "environ").unlink()
        legacy = self.home / ".retroarch.cfg"
        legacy.write_text('input_save_state = "f10"', encoding="utf-8")
        self.assertEqual(self.reader(self.profile, self.process)["actions"]["save_state"]["keys"], ["f10"])
        legacy.unlink()
        stale = self.home / ".var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg"
        stale.parent.mkdir(parents=True)
        stale.write_text('input_save_state = "f11"', encoding="utf-8")
        self.assertEqual(self.reader(self.profile, self.process)["hotkey_config"]["status"], "fallback")

    def test_malformed_oversized_missing_explicit_and_missing_include_fail_closed(self):
        for text in ('input_save_state = "f5', 'input_enable_hotkey', '#include "missing.cfg"',
                     '#include bad.cfg', '#' * (MAX_CONFIG_BYTES + 1)):
            result = self.resolve(text)
            self.assertEqual(result["hotkey_config"]["status"], "unavailable")
            self.assertEqual(result["capabilities"], [])
        result = self.resolve('input_save_state = "f5"', self.process_with("-c", str(self.home / "missing.cfg")))
        self.assertEqual(result["capabilities"], [])

    def test_xdg_missing_falls_back_to_user_config_before_legacy(self):
        (self.proc / "environ").write_bytes(f"XDG_CONFIG_HOME={self.home / 'missing'}\0".encode())
        (self.home / ".retroarch.cfg").write_text('input_save_state = "f10"', encoding="utf-8")
        result = self.resolve('input_save_state = "f9"')
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f9"])

    def test_flatpak_root_marker_finds_config_without_environment(self):
        marker = self.proc / "root/.flatpak-info"
        marker.parent.mkdir()
        marker.write_text("[Application]\nname=org.libretro.RetroArch", encoding="utf-8")
        config = self.home / ".var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg"
        config.parent.mkdir(parents=True)
        config.write_text('input_save_state = "f10"', encoding="utf-8")
        result = self.resolve('input_save_state = "f9"')
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f10"])

    def test_invalid_cli_configuration_and_missing_append_fail_closed(self):
        for args in (("--config=",), ("--appendconfig=",), ("--appendconfig=one.cfg||two.cfg",),
                     (f"--appendconfig={self.home / 'missing.cfg'}",), ("--config", "--verbose")):
            with self.subTest(args=args):
                result = self.resolve('input_save_state = "f5"', self.process_with(*args))
                self.assertEqual(result["capabilities"], [])

    def test_include_cycle_and_file_count_limit_fail_closed(self):
        self.assertEqual(self.resolve('#include "retroarch.cfg"')["capabilities"], [])
        for index in range(MAX_CONFIG_FILES):
            (self.path.parent / f"{index}.cfg").write_text(
                f'#include "{index + 1}.cfg"' if index < MAX_CONFIG_FILES - 1 else 'input_save_state = "f5"',
                encoding="utf-8",
            )
        self.assertEqual(self.resolve('#include "0.cfg"')["hotkey_config"]["status"], "unavailable")

    def test_unreadable_config_does_not_reuse_previous_bindings(self):
        self.resolve('input_save_state = "f5"')
        self.reader._cache.clear()
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            result = self.reader(self.profile, self.process)
        self.assertEqual(result["capabilities"], [])

    def test_stat_permission_error_is_not_treated_as_missing_config(self):
        original_stat = Path.stat

        def denied(path, *args, **kwargs):
            if path == self.path:
                raise PermissionError("denied")
            return original_stat(path, *args, **kwargs)

        with patch.object(Path, "stat", denied):
            result = self.reader(self.profile, self.process)
        self.assertEqual(result["hotkey_config"]["status"], "unavailable")
        self.assertEqual(result["capabilities"], [])

    def test_cache_reloads_included_file_and_same_pid_keeps_slot(self):
        include = self.path.parent / "included.cfg"
        include.write_text('input_save_state = "f5"', encoding="utf-8")
        with patch("companion_retroarch_config.parse_retroarch_config", wraps=parse_retroarch_config) as parser:
            self.resolve('#include "included.cfg"')
            manager = SessionManager(self.store, process_provider=lambda: [self.process], profile_provider=self.reader)
            session = manager.refresh()
            session.slot = 4
            self.assertEqual(parser.call_count, 2)
            include.write_text('input_save_state = "f12"', encoding="utf-8")
            self.assertIs(manager.refresh(), session)
            self.assertEqual(parser.call_count, 3)
            self.assertEqual(session.actions["save_state"]["keys"], ["f12"])
            self.assertEqual(session.slot, 4)
            include.unlink()
            self.assertEqual(manager.refresh().capabilities, [])

    def test_fbneo_uses_same_resolver_other_emulators_unchanged(self):
        result = self.resolve('input_save_state = "f5"', profile=self.store.get("fbneo"))
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f5"])
        self.assertNotIn("rewind", result["capabilities"])
        for name in ("duckstation", "cemu"):
            profile = self.store.get(name)
            self.assertIs(self.reader(profile, self.process), profile)

    def test_resolved_chord_dispatched_and_disabled_action_rejected(self):
        self.resolve('input_enable_hotkey = "ctrl"\ninput_save_state = "f9"\ninput_load_state = "nul"')
        manager = SessionManager(self.store, process_provider=lambda: [self.process], profile_provider=self.reader)
        session = manager.refresh()
        engine = ActionEngine(frontend_input=True)
        result = asyncio.run(engine.execute(session, "save_state"))
        self.assertTrue(result.ok)
        self.assertEqual(result.keys, ["leftctrl", "f9"])
        self.assertEqual(result.dispatch, "steam_input")
        self.assertFalse(asyncio.run(engine.execute(session, "load_state")).ok)
        self.assertFalse(asyncio.run(engine.execute(session, "rewind")).ok)

    def test_all_translated_keys_have_frontend_support(self):
        self.assertFalse(set(KEYS.values()) - SUPPORTED_KEYS)

    def test_storage_include_override_priority_and_cache_refresh(self):
        process = ProcessInfo(42, "retroarch", ("retroarch", "-L", "/cores/snes9x_libretro.so", str(self.home / "roms/game.sfc")))
        override_dir = self.path.parent / "config/Snes9x"
        override_dir.mkdir(parents=True)
        game = override_dir / "game.cfg"
        game.write_text('savestate_directory = "~/custom"', encoding="utf-8")
        include = self.path.parent / "storage.cfg"
        include.write_text('savestate_directory = "~/base"', encoding="utf-8")
        result = self.resolve('#include "storage.cfg"\nrgui_config_directory = "' +
                              str(override_dir.parent).replace("\\", "/") + '"\n' +
                              'sort_savestates_enable = "false"\nsort_savestates_by_content_enable = "false"\n'
                              'savestates_in_content_dir = "false"\n', process=process)
        self.assertEqual(result["hotkey_config"]["savestate_search"]["paths"], [str(self.home / "custom"), str(self.path.parent / "states")])
        game.write_text('savestate_directory = "~/new_custom"', encoding="utf-8")
        result = self.reader(self.profile, process)
        self.assertEqual(result["hotkey_config"]["savestate_search"]["paths"], [str(self.home / "new_custom"), str(self.path.parent / "states")])

    def test_malformed_optional_storage_setting_keeps_working_hotkeys(self):
        result = self.resolve('input_save_state = "f5"\nsavestate_directory = "unterminated')
        self.assertEqual(result["hotkey_config"]["status"], "configured")
        self.assertEqual(result["actions"]["save_state"]["keys"], ["f5"])
        self.assertEqual(result["hotkey_config"]["savestate_search"]["paths"], [str(self.path.parent / "states")])

    def test_flatpak_local_states_when_recorded_emudeck_folder_is_missing(self):
        from companion_savestates import SavestateIndex

        self.path = self.home / ".var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg"
        self.path.parent.mkdir(parents=True)
        states = self.path.parent / "states"
        states.mkdir()
        stem = "1080 TenEighty Snowboarding (Europe) (En,Ja,Fr,De)"
        for name in (stem + ".state", stem + ".state.auto", stem + ".state.png", stem + ".state.auto.png", "Other.state"):
            (states / name).write_bytes(b"untouched")
        rom = str(self.home / "Emulation/roms/n64" / (stem + ".n64"))
        process = ProcessInfo(42, "retroarch", ("retroarch", "-c", str(self.path), rom))
        config = ('savestate_directory = "~/Emulation/saves/retroarch/states"\n'
                  'savestates_in_content_dir = "false"\nsort_savestates_enable = "false"\n'
                  'sort_savestates_by_content_enable = "false"\ninput_save_state = "f5"\n')
        resolved = self.resolve(config, process=process)
        index = SavestateIndex(self.home / "Emulation")
        found = index.lookup(resolved, rom)
        self.assertEqual({Path(item["path"]).name for item in found}, {stem + ".state", stem + ".state.auto"})
        self.assertEqual(index.last_search["matched_files"], 2)
        self.assertEqual(len(index.last_search["directories"]), 2)
        self.assertEqual(index.last_search["directories"][0]["status"], "missing_or_not_directory")
        self.assertEqual(self.path.read_text(encoding="utf-8"), config)
        self.assertTrue(all(path.read_bytes() == b"untouched" for path in states.iterdir()))
        self.assertEqual(resolved["actions"]["save_state"]["keys"], ["f5"])


if __name__ == "__main__":
    unittest.main()
