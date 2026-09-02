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


if __name__ == "__main__":
    unittest.main()
