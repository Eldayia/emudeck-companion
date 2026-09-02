import json
import os
import runpy
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import companion_esde_hooks as hooks


class ESDEHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "ES-DE with spaces"
        self.root.mkdir()
        (self.root / "es_settings.xml").write_text("<config/>", encoding="utf-8")
        self.rom = str(self.root / "ROM's $game; (Europe).n64")
        self.args = [self.rom, 'Game "name" é', "n64", "Nintendo 64"]
        self.boot = patch.object(hooks, "boot_id", return_value="test-boot")
        self.boot.start()
        self.addCleanup(self.boot.stop)

    def install(self):
        return hooks.manage(self.root, "install")

    def event(self, event="game-start"):
        hooks.record_event(self.root, event, self.args)

    def test_install_idempotent_and_uninstall_preserves_other_scripts_and_settings(self):
        other = self.root / "scripts/game-start/user.sh"
        other.parent.mkdir(parents=True)
        other.write_text("user script", encoding="utf-8")
        paths = self.install()
        self.assertEqual(paths, self.install())
        self.assertEqual(hooks.read_status(self.root)["status"], "waiting_for_event")
        self.assertEqual(hooks.manage(self.root, "remove"), paths)
        self.assertEqual(hooks.manage(self.root, "remove"), [])
        self.assertEqual(other.read_text(), "user script")
        self.assertEqual((self.root / "es_settings.xml").read_text(), "<config/>")

    def test_conflict_preflight_does_not_install_first_hook(self):
        conflict = self.root / "scripts/game-end" / hooks.HOOK_NAME
        conflict.parent.mkdir(parents=True)
        conflict.write_text("existing user file", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse((self.root / "scripts/game-start" / hooks.HOOK_NAME).exists())
        self.assertEqual(conflict.read_text(), "existing user file")

    def test_modified_hook_prevents_removal_of_both(self):
        paths = self.install()
        Path(paths[1]).write_text("modified", encoding="utf-8")
        self.assertEqual(hooks.read_status(self.root)["status"], "modified_hooks")
        with self.assertRaises(ValueError):
            hooks.manage(self.root, "remove")
        self.assertTrue(Path(paths[0]).exists())

    def test_rejects_wrong_data_root_and_supports_settings_subdirectory(self):
        (self.root / "es_settings.xml").unlink()
        with self.assertRaises(ValueError):
            self.install()
        (self.root / "settings").mkdir()
        (self.root / "settings/es_settings.xml").write_text("<config/>")
        self.assertEqual(len(self.install()), 2)

    def test_round_trip_start_end_special_characters_and_single_snapshot(self):
        self.install()
        self.event()
        first = hooks.read_status(self.root, self.rom)
        self.assertEqual(first["status"], "event_received")
        self.assertTrue(first["same_rom"])
        self.assertEqual(first["last_event"]["game"], self.args[1])
        self.assertFalse(hooks.read_status(self.root, self.rom.upper())["same_rom"])
        self.event("game-end")
        last = hooks.read_status(self.root)
        self.assertNotEqual(first["last_event"]["id"], last["last_event"]["id"])
        self.assertEqual(last["last_event"]["event"], "game-end")
        self.assertEqual([p.name for p in (self.root / hooks.STATE_DIR).iterdir()], ["latest.json"])

    def test_previous_boot_does_not_match_active_game(self):
        self.install()
        self.event()
        with patch.object(hooks, "boot_id", return_value="other-boot"):
            status = hooks.read_status(self.root, self.rom)
        self.assertEqual(status["status"], "previous_boot")
        self.assertNotIn("last_event", status)

    def test_no_install_partial_and_missing_snapshot(self):
        self.assertEqual(hooks.read_status(None)["status"], "not_installed")
        self.assertEqual(hooks.read_status(self.root)["status"], "not_installed")
        paths = self.install()
        self.assertEqual(hooks.read_status(self.root)["status"], "waiting_for_event")
        Path(paths[0]).unlink()
        self.assertEqual(hooks.read_status(self.root)["status"], "partial_install")

    def test_invalid_and_oversized_events_fail_closed(self):
        self.install()
        self.event()
        target = self.root / hooks.STATE_DIR / "latest.json"
        valid = json.loads(target.read_bytes())
        bad = ["[]", "{", "x" * (hooks.MAX_EVENT_BYTES + 1)]
        for key, value in (("timestamp", float("nan")), ("timestamp", True), ("timestamp", float("inf")),
                           ("rom", "relative"), ("game", 9), ("id", "x" * 32), ("version", True), ("event", "quit")):
            bad.append(json.dumps({**valid, key: value}))
        for data in bad:
            with self.subTest(data=data[:80]):
                target.write_text(data, encoding="utf-8")
                self.assertEqual(hooks.read_status(self.root)["status"], "unreadable_or_invalid")

    def test_invalid_arguments_do_not_replace_existing_event(self):
        self.event()
        target = self.root / hooks.STATE_DIR / "latest.json"
        original = target.read_bytes()
        for event, args in (("quit", self.args), ("game-start", []), ("game-end", ["relative", "", "", ""]),
                            ("game-start", [self.rom, "x" * 1025, "", ""])):
            with self.assertRaises(ValueError):
                hooks.record_event(self.root, event, args)
        self.assertEqual(target.read_bytes(), original)

    def test_atomic_write_failure_keeps_snapshot_and_cleans_temporary(self):
        self.event()
        target = self.root / hooks.STATE_DIR / "latest.json"
        original = target.read_bytes()
        with patch.object(hooks.os, "replace", side_effect=OSError("test")):
            with self.assertRaises(OSError):
                self.event("game-end")
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(len(list(target.parent.iterdir())), 1)

    def test_installer_write_failure_rolls_back_only_created_hooks(self):
        original = Path.chmod
        def fail_second(path, *args, **kwargs):
            if path.parent.name == "game-end":
                raise OSError("test")
            return original(path, *args, **kwargs)
        with patch.object(Path, "chmod", fail_second):
            with self.assertRaises(OSError):
                self.install()
        self.assertFalse((self.root / "scripts/game-start" / hooks.HOOK_NAME).exists())
        self.assertFalse((self.root / "scripts/game-end" / hooks.HOOK_NAME).exists())

    def test_installed_copy_runs_without_plugin_imports(self):
        paths = self.install()
        original = Path.read_text
        def read(path, *args, **kwargs):
            if str(path).replace("\\", "/") == "/proc/sys/kernel/random/boot_id":
                return "test-boot"
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", read), patch("sys.argv", [paths[0], *self.args]):
            with self.assertRaises(SystemExit) as finished:
                runpy.run_path(paths[0], run_name="__main__")
        self.assertEqual(finished.exception.code, 0)
        self.assertEqual(hooks.read_status(self.root)["status"], "event_received")
        self.assertNotIn(b"\r\n", Path(paths[0]).read_bytes())

    @unittest.skipUnless(os.name == "posix", "POSIX symlinks/FIFOs")
    def test_rejects_symlinks_and_fifo_without_blocking(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "scripts").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.install()
        (self.root / "scripts").unlink()
        self.install()
        state = self.root / hooks.STATE_DIR
        state.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.event()
        self.assertEqual(hooks.read_status(self.root)["status"], "unreadable_or_invalid")
        state.unlink()
        state.mkdir()
        os.mkfifo(state / "latest.json")
        self.assertEqual(hooks.read_status(self.root)["status"], "unreadable_or_invalid")

    def test_nonregular_file_rejected_before_open_even_on_windows(self):
        from types import SimpleNamespace
        for mode in (stat.S_IFIFO, stat.S_IFLNK, stat.S_IFCHR, stat.S_IFDIR):
            with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_size=0)), patch.object(hooks.os, "open") as opened:
                with self.assertRaises(ValueError):
                    hooks.regular_file(self.root / "file", 100)
                opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
