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


def _matches(process: ProcessInfo, names: list[str]) -> bool:
    candidates = {process.name.casefold()}
    if process.argv:
        candidates.add(os.path.basename(process.argv[0]).casefold())
    expected = {name.casefold() for name in names}
    return bool(candidates.intersection(expected))


def find_emulator(
    profiles: Iterable[dict], processes: Iterable[ProcessInfo] | None = None
) -> tuple[dict, ProcessInfo] | None:
    process_list = list(processes if processes is not None else iter_processes())
    matches: list[tuple[int, dict, ProcessInfo]] = []
    for profile in profiles:
        for process in process_list:
            if _matches(process, profile["processes"]):
                # Prefer the most recently created matching process. This keeps ES-DE
                # and stale helper processes from masking the active emulator.
                matches.append((process.started_ticks or 0, profile, process))
    if not matches:
        return None
    _, profile, process = max(matches, key=lambda item: (item[0], item[2].pid))
    return profile, process
