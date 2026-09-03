from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import Any


SLOT_PATTERNS = (
    re.compile(r"\.state(?P<slot>\d*)$", re.IGNORECASE),
    re.compile(r"\.ml(?P<slot>[1-8])$", re.IGNORECASE),
    re.compile(r"_(?P<slot>\d)\.ppst$", re.IGNORECASE),
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
        self.last_search: dict[str, Any] = {}

    def lookup(self, profile: dict[str, Any], rom: str | None) -> list[dict[str, Any]]:
        self.last_search = {"rom": rom, "directories": [], "matched_files": 0}
        if not rom:
            return []
        stem = Path(rom).stem
        escaped_stem = glob.escape(stem)
        found: dict[str, dict[str, Any]] = {}
        directories = []
        if profile.get("hotkey_config_format") == "retroarch":
            search = (profile.get("hotkey_config") or {}).get("savestate_search") or {}
            for name in search.get("paths", []):
                if isinstance(name, str) and "\0" not in name and Path(name).is_absolute():
                    directories.append(Path(name))
        if self.emulation_root:
            directories.extend(self.emulation_root / name for name in profile.get("savestate_paths", []))
        for directory in dict.fromkeys(directories):
            entry = {"path": str(directory), "status": "searched"}
            self.last_search["directories"].append(entry)
            try:
                if not directory.is_dir():
                    entry["status"] = "missing_or_not_directory"
                    continue
            except OSError:
                entry["status"] = "unavailable"
                continue
            for template in profile.get("savestate_patterns", []):
                pattern = str(template).replace("{stem}", escaped_stem)
                try:
                    candidates = directory.glob(pattern)
                    for path in candidates:
                        # Broad .state* patterns also match preview images. They
                        # are not savestates and must not inflate the inventory.
                        if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
                            continue
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
                    entry["status"] = "incomplete_or_unavailable"
                    continue
        self.last_search["matched_files"] = len(found)
        return sorted(found.values(), key=lambda state: state["modified_at"], reverse=True)
