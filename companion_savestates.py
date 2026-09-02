from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import Any


SLOT_PATTERNS = (
    re.compile(r"\.state(?P<slot>\d*)$", re.IGNORECASE),
    re.compile(r"\.s(?P<slot>\d{2})$", re.IGNORECASE),
    re.compile(r"[._-](?P<slot>\d{1,2})\.p2s$", re.IGNORECASE),
    re.compile(r"[._-](?P<slot>\d{1,2})\.sav$", re.IGNORECASE),
)


def _slot_from_name(name: str) -> int | None:
    for pattern in SLOT_PATTERNS:
        match = pattern.search(name)
        if match:
            value = match.group("slot")
            return int(value) if value else 0
    return None


class SavestateIndex:
    """Find savestates that can be unambiguously associated with the active ROM."""

    def __init__(self, emulation_root: Path | None):
        self.emulation_root = emulation_root

    def lookup(self, profile: dict[str, Any], rom: str | None) -> list[dict[str, Any]]:
        if not self.emulation_root or not rom:
            return []
        stem = Path(rom).stem
        escaped_stem = glob.escape(stem)
        found: dict[str, dict[str, Any]] = {}
        for relative_dir in profile.get("savestate_paths", []):
            directory = self.emulation_root / relative_dir
            if not directory.is_dir():
                continue
            for template in profile.get("savestate_patterns", []):
                pattern = str(template).replace("{stem}", escaped_stem)
                try:
                    candidates = directory.glob(pattern)
                    for path in candidates:
                        if not path.is_file():
                            continue
                        stat = path.stat()
                        found[str(path)] = {
                            "slot": _slot_from_name(path.name),
                            "path": str(path),
                            "modified_at": stat.st_mtime,
                            "size": stat.st_size,
                        }
                except OSError:
                    continue
        return sorted(found.values(), key=lambda state: state["modified_at"], reverse=True)
