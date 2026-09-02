import tempfile
import unittest
from pathlib import Path

from companion_emudeck import detect_emudeck


class EmuDeckDetectionTests(unittest.TestCase):
    def test_detects_internal_install(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "Emulation" / "roms").mkdir(parents=True)
            (home / ".config" / "ES-DE").mkdir(parents=True)
            status = detect_emudeck(home, home / "missing-mounts")
            self.assertTrue(status["detected"])
            self.assertTrue(status["esde_detected"])

    def test_handles_missing_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            status = detect_emudeck(home, home / "missing-mounts")
            self.assertFalse(status["detected"])

    def test_detects_drive_mounted_below_home(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home / "Elements" / "Emulation"
            (root / "roms").mkdir(parents=True)
            status = detect_emudeck(home, home / "missing-mounts")
            self.assertTrue(status["detected"])
            self.assertEqual(status["root"], str(root))

    def test_detects_esde_without_emudeck(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            esde = home / ".emulationstation"
            esde.mkdir()
            status = detect_emudeck(home, home / "missing-mounts")
            self.assertFalse(status["detected"])
            self.assertTrue(status["esde_detected"])
            self.assertEqual(status["esde_root"], str(esde))


if __name__ == "__main__":
    unittest.main()
