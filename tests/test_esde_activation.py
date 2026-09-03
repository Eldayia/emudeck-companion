import tempfile
import builtins
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

from companion_esde_activation import diagnostic_status, read_activation
from companion_esde_hooks import manage, record_event


class ESDEActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "es_settings.xml"

    def write(self, text):
        self.path.write_text(text, encoding="utf-8")

    def test_reads_enabled_and_disabled_without_modifying_file(self):
        for enabled in ("true", "false"):
            self.write(f'<config><bool name="CustomEventScripts" value="{enabled}"/></config>')
            before = self.path.read_bytes()
            self.assertEqual(read_activation(self.root)["status"], "enabled_on_disk" if enabled == "true" else "disabled_on_disk")
            self.assertEqual(self.path.read_bytes(), before)

    def test_modern_location_fragment_declaration_bom_and_comments(self):
        self.path = self.root / "settings/es_settings.xml"
        self.path.parent.mkdir()
        self.write('\ufeff<?xml version="1.0"?>\n<!-- note -->\n<bool name="Other" value="false"/>\n<bool value="true" name="CustomEventScripts"/>')
        result = read_activation(self.root)
        self.assertEqual(result["status"], "enabled_on_disk")
        self.assertEqual(result["path"], str(self.path))

    def test_unknown_is_not_disabled(self):
        self.assertEqual(read_activation(None)["status"], "unknown")
        self.assertEqual(read_activation(self.root)["status"], "unknown")
        for content in ('<config/>', '<bool name="CustomEventScripts" value="yes"/>',
                        '<bool name="CustomEventScripts" value="true"/><bool name="CustomEventScripts" value="false"/>',
                        '<!-- <bool name="CustomEventScripts" value="true"/> -->',
                        '<string name="CustomEventScripts" value="true"/>'):
            self.write(content)
            self.assertEqual(read_activation(self.root)["status"], "unknown")

    def test_conflicting_files_do_not_guess_active_configuration(self):
        self.write('<bool name="CustomEventScripts" value="false"/>')
        modern = self.root / "settings/es_settings.xml"
        modern.parent.mkdir()
        modern.write_text('<bool name="CustomEventScripts" value="true"/>')
        self.assertIn("Multiple", read_activation(self.root)["reason"])

    def test_invalid_xml_entities_and_oversized_files_are_rejected(self):
        for content in ('<broken', '<!DOCTYPE config [<!ENTITY yes "true">]><config/>',
                        '<!ENTITY yes "true">', 'x' * (1024 * 1024 + 1)):
            self.write(content)
            self.assertEqual(read_activation(self.root)["status"], "unknown")

    def test_unreadable_file_does_not_leak_contents_or_error(self):
        with patch("companion_esde_activation.regular_file", side_effect=PermissionError("secret")):
            result = read_activation(self.root)
        self.assertEqual(result["status"], "unknown")
        self.assertNotIn("secret", str(result))

    def test_setting_is_reread_after_changes(self):
        self.write('<bool name="CustomEventScripts" value="true"/>')
        self.assertEqual(read_activation(self.root)["status"], "enabled_on_disk")
        self.write('<bool name="CustomEventScripts" value="false"/>')
        self.assertEqual(read_activation(self.root)["status"], "disabled_on_disk")

    def test_received_event_and_saved_setting_are_independent_and_copies_unchanged(self):
        self.write('<bool name="CustomEventScripts" value="true"/>')
        paths = manage(self.root, "install")
        originals = [Path(p).read_bytes() for p in paths]
        with patch("companion_esde_hooks.boot_id", return_value="test-boot"):
            record_event(self.root, "game-start", [str(self.root / "rom.n64"), "Game", "n64", "N64"])
            for value in ("true", "false", "unknown"):
                self.write(f'<bool name="CustomEventScripts" value="{value}"/>')
                result = diagnostic_status(self.root)
                self.assertEqual(result["status"], "event_received")
                self.assertIn("hook event received this boot", result["activation"])
                self.assertNotIn("Not checked", result["activation"])
                self.assertNotIn("enable custom event scripts", result["activation"])
        self.assertEqual([Path(p).read_bytes() for p in paths], originals)
        self.assertEqual(manage(self.root, "remove"), paths)

    def test_previous_boot_does_not_claim_receipt_this_boot(self):
        self.write('<bool name="CustomEventScripts" value="true"/>')
        manage(self.root, "install")
        with patch("companion_esde_hooks.boot_id", return_value="old"):
            record_event(self.root, "game-end", [str(self.root / "rom.n64"), "Game", "n64", "N64"])
        with patch("companion_esde_hooks.boot_id", return_value="new"):
            result = diagnostic_status(self.root)
        self.assertIn("Enabled in saved", result["activation"])
        self.assertIn("no valid hook event", result["activation"])

    def test_module_import_and_status_survive_missing_xml_runtime(self):
        original = builtins.__import__
        def without_xml(name, *args, **kwargs):
            if name.startswith("xml"):
                raise ModuleNotFoundError("XML unavailable")
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", without_xml):
            module = runpy.run_path(str(Path(__file__).parents[1] / "companion_esde_activation.py"))
            result = module["diagnostic_status"](self.root)
        self.assertEqual(result["activation_config"]["status"], "unknown")
        self.assertIn("XML parser unavailable", result["activation_config"]["reason"])

    def test_native_parser_dependency_failure_is_optional(self):
        self.write('<bool name="CustomEventScripts" value="true"/>')
        with patch("xml.etree.ElementTree.fromstring", side_effect=ImportError("pyexpat")):
            result = read_activation(self.root)
        self.assertEqual(result["status"], "unknown")
        self.assertIn("XML parser unavailable", result["reason"])
