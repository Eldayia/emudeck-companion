import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion_process_detection import _read_process, _started_ticks


def stat_line(name="retroarch", ticks=1234, pid=42):
    # Fields 3 through 22: state, 18 intermediate fields, starttime.
    return f"{pid} ({name}) S " + "0 " * 18 + f"{ticks} 0 0\n"


class ProcessSnapshotTests(unittest.TestCase):
    def test_stat_name_with_spaces_parentheses_and_newline(self):
        for name in ("retroarch", "Duck Station", "game (one)", "game ) (two)", "game\nname"):
            self.assertEqual(_started_ticks(stat_line(name), 42), 1234)

    def test_rejects_malformed_wrong_pid_negative_or_missing_start_time(self):
        for raw in ("", "42 retroarch 0", "42 (retroarch) S 0", stat_line(pid=43), stat_line(ticks=-1), stat_line(ticks="bad")):
            with self.assertRaises(ValueError):
                _started_ticks(raw, 42)

    def test_reads_matching_process_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory) / "42"
            proc.mkdir()
            (proc / "stat").write_text(stat_line("Retro Arch"))
            (proc / "comm").write_text("retroarch\n")
            (proc / "cmdline").write_bytes(b"retroarch\0/roms/Game with spaces.sfc\0")
            result = _read_process(proc)
            self.assertEqual(result.started_ticks, 1234)
            self.assertEqual(result.argv, ("retroarch", "/roms/Game with spaces.sfc"))

    def test_rejects_snapshot_if_pid_reused_between_reads(self):
        with patch.object(Path, "read_text", side_effect=[stat_line(ticks=10), "retroarch", stat_line(ticks=20)]), \
             patch.object(Path, "read_bytes", return_value=b"retroarch\0game.sfc\0"):
            self.assertIsNone(_read_process(Path("/proc/42")))

    def test_disappearing_and_inaccessible_processes_are_ignored(self):
        for error in (FileNotFoundError(), PermissionError(), ProcessLookupError()):
            with patch.object(Path, "read_text", side_effect=error):
                self.assertIsNone(_read_process(Path("/proc/42")))


if __name__ == "__main__":
    unittest.main()
