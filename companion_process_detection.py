from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from companion_models import ProcessInfo


def _read_process(proc_dir: Path) -> ProcessInfo | None:
    try:
        raw = (proc_dir / "cmdline").read_bytes()
        argv = tuple(item.decode("utf-8", "replace") for item in raw.split(b"\0") if item)
        comm = (proc_dir / "comm").read_text(encoding="utf-8").strip()
        stat = (proc_dir / "stat").read_text(encoding="utf-8").split()
        started_ticks = int(stat[21]) if len(stat) > 21 else None
        return ProcessInfo(int(proc_dir.name), comm, argv, started_ticks)
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError):
        return None


def iter_processes(proc_root: Path = Path("/proc")) -> Iterable[ProcessInfo]:
    if not proc_root.is_dir():
        return
    for entry in proc_root.iterdir():
        if entry.name.isdigit():
            process = _read_process(entry)
            if process is not None:
                yield process


def _matches(process: ProcessInfo, names: list[str], argv_contains: list[str] | None = None) -> bool:
    candidates = {process.name.casefold()}
    if process.argv:
        candidates.add(os.path.basename(process.argv[0]).casefold())
    expected = {name.casefold() for name in names}
    if not candidates.intersection(expected):
        return False
    required = [value.casefold() for value in (argv_contains or [])]
    command = "\0".join(process.argv).casefold()
    return not required or any(value in command for value in required)


def find_emulator(
    profiles: Iterable[dict], processes: Iterable[ProcessInfo] | None = None
) -> tuple[dict, ProcessInfo] | None:
    process_list = list(processes if processes is not None else iter_processes())
    matches: list[tuple[int, int, int, dict, ProcessInfo]] = []
    for profile in profiles:
        for process in process_list:
            if _matches(process, profile["processes"], profile.get("argv_contains")):
                # Prefer the most recently created matching process. This keeps ES-DE
                # and stale helper processes from masking the active emulator. A
                # core-specific profile wins over its generic frontend profile.
                matches.append((
                    process.started_ticks or 0,
                    process.pid,
                    1 if profile.get("argv_contains") else 0,
                    profile,
                    process,
                ))
    if not matches:
        return None
    _, _, _, profile, process = max(matches, key=lambda item: item[:3])
    return profile, process
