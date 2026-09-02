import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion_hotkey_config import MAX_CONFIG_BYTES
from companion_retroarch_config import parse_retroarch_config
from companion_retroarch_setup import configure_network


class SetupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.path = self.home / ".var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg"
        self.path.parent.mkdir(parents=True)
        self.backups = self.home / "backups"

    def test_enable_preserves_binds_port_comments_and_exact_backup(self):
        original = (b'# comment\ninput_save_state = "nul"\ninput_save_state_btn = "10"\n'
                    b'input_enable_hotkey = "nul"\nnetwork_cmd_port = "12345"\n')
        self.path.write_bytes(original)
        result = configure_network(self.home, self.backups, True)
        self.assertTrue(result["ok"])
        self.assertEqual(Path(result["backup"]).read_bytes(), original)
        self.assertEqual(self.path.read_bytes(), b'network_cmd_enable = "true"\n' + original)
        self.assertFalse(list(self.path.parent.glob(".companion-network-*")))
        if os.name != "nt":
            self.assertEqual(Path(result["backup"]).stat().st_mode & 0o777, 0o600)

    def test_preserves_bom_crlf_and_non_ascii(self):
        original = '\ufeff# café\r\ninput_pause_toggle = "nul"\r\n'.encode("utf-8")
        self.path.write_bytes(original)
        configure_network(self.home, self.backups, True)
        self.assertEqual(self.path.read_bytes(), b'\xef\xbb\xbfnetwork_cmd_enable = "true"\r\n' + original[3:])

    def test_flag_precedes_includes_duplicate_flags_removed_and_disable_is_reversible(self):
        original = '#include "input.cfg"\nnetwork_cmd_enable = "false"\n  network_cmd_enable = "true" # duplicate\n'
        self.path.write_text(original, encoding="utf-8")
        configure_network(self.home, self.backups, True)
        entries = parse_retroarch_config(self.path.read_text(encoding="utf-8"))
        self.assertEqual(entries, [("network_cmd_enable", "true"), ("#include", "input.cfg")])
        enabled = self.path.read_bytes()
        result = configure_network(self.home, self.backups, False)
        self.assertEqual(Path(result["backup"]).read_bytes(), enabled)
        self.assertTrue(self.path.read_bytes().startswith(b'network_cmd_enable = "false"'))

    def test_idempotent_setting_creates_no_extra_backup(self):
        self.path.write_bytes(b'network_cmd_enable = "true"\ninput_save_state = "nul"\n')
        result = configure_network(self.home, self.backups, True)
        self.assertTrue(result["ok"])
        self.assertNotIn("backup", result)
        self.assertFalse(self.backups.exists())

    def test_missing_oversized_invalid_encoding_and_non_boolean_fail_without_write(self):
        with self.assertRaises(FileNotFoundError):
            configure_network(self.home, self.backups, True)
        for original in (b"#" * (MAX_CONFIG_BYTES + 1), b"\xff"):
            self.path.write_bytes(original)
            with self.assertRaises(ValueError):
                configure_network(self.home, self.backups, True)
            self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(ValueError):
            configure_network(self.home, self.backups, "true")
        self.assertFalse(self.backups.exists())

    def test_backup_failure_leaves_config_unchanged(self):
        original = b'input_save_state = "nul"\n'
        self.path.write_bytes(original)
        with patch("companion_retroarch_setup.os.open", side_effect=PermissionError("backup denied")):
            with self.assertRaises(PermissionError):
                configure_network(self.home, self.backups, True)
        self.assertEqual(self.path.read_bytes(), original)

    def test_replace_failure_keeps_original_and_cleans_temporary(self):
        original = b'input_save_state = "nul"\n'
        self.path.write_bytes(original)
        with patch("companion_retroarch_setup.os.replace", side_effect=OSError("replace denied")):
            with self.assertRaises(OSError):
                configure_network(self.home, self.backups, True)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(len(list(self.backups.glob("*.cfg"))), 1)
        self.assertFalse(list(self.path.parent.glob(".companion-network-*")))

    def test_concurrent_edit_is_not_overwritten(self):
        self.path.write_bytes(b'input_save_state = "nul"\n')
        real_chmod = os.chmod

        def concurrent_edit(path, mode):
            real_chmod(path, mode)
            self.path.write_bytes(b"# edited concurrently\n")

        with patch("companion_retroarch_setup.os.chmod", side_effect=concurrent_edit):
            with self.assertRaisesRegex(ValueError, "changed during setup"):
                configure_network(self.home, self.backups, True)
        self.assertEqual(self.path.read_bytes(), b"# edited concurrently\n")
        self.assertFalse(list(self.path.parent.glob(".companion-network-*")))


if __name__ == "__main__":
    unittest.main()
