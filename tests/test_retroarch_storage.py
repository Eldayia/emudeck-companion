import tempfile
import unittest
from pathlib import Path

from companion_models import ProcessInfo
from companion_retroarch_storage import storage_search


class RetroArchStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.rom = str(self.home / "roms/n64/Game.n64")
        self.process = ProcessInfo(42, "retroarch", ("retroarch", self.rom))
        self.values = {"savestate_directory": "~/states", "savestates_in_content_dir": "false",
                       "sort_savestates_enable": "false", "sort_savestates_by_content_enable": "false"}

    def resolve(self, core="Mupen64Plus-Next"):
        return storage_search(self.values, self.process, self.home, core, self.home / "proc", self.rom)

    def test_plain_path_and_sorting_order_without_creating_directories(self):
        self.assertEqual(self.resolve()["paths"], [str(self.home / "states")])
        self.values.update(sort_savestates_enable="true", sort_savestates_by_content_enable="true")
        self.assertEqual(self.resolve()["paths"], [str(self.home / "states/n64/Mupen64Plus-Next"), str(self.home / "states")])
        self.assertFalse((self.home / "states").exists())

    def test_content_directory_with_sorting(self):
        self.values.update(savestates_in_content_dir="true", sort_savestates_enable="true")
        self.assertEqual(self.resolve()["paths"], [str(self.home / "roms/n64/Mupen64Plus-Next"), str(self.home / "roms/n64")])

    def test_incomplete_or_invalid_settings_do_not_guess(self):
        for key in self.values:
            original = self.values[key]
            self.values[key] = "\0invalid"
            self.assertEqual(self.resolve()["paths"], [])
            self.values[key] = original
        self.values.pop("sort_savestates_enable")
        self.assertEqual(self.resolve()["status"], "not_resolved")

    def test_unknown_core_only_blocks_core_sort(self):
        self.assertTrue(self.resolve(core=None)["paths"])
        self.values["sort_savestates_enable"] = "true"
        self.assertEqual(self.resolve(core=None)["paths"], [])

    def test_unsupported_launch_overrides_and_archive_members(self):
        for arg in ("-S", "-Scustom", "--savestate=custom", "--subsystem"):
            self.process = ProcessInfo(42, "retroarch", ("retroarch", arg, self.rom))
            self.assertEqual(self.resolve()["paths"], [])
        self.process = ProcessInfo(42, "retroarch", ("retroarch", self.rom))
        self.rom += "#member"
        self.assertEqual(self.resolve()["paths"], [])

    def test_relative_path_requires_known_process_cwd(self):
        self.values["savestate_directory"] = "states"
        self.assertEqual(self.resolve()["paths"], [])
        cwd = self.home / "proc/42/cwd"
        cwd.mkdir(parents=True)
        self.assertEqual(self.resolve()["paths"], [str(cwd / "states")])
