from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Iterable


GENERIC_EXTENSIONS = {
    ".3ds", ".7z", ".bin", ".chd", ".cia", ".cso", ".cue", ".elf",
    ".gcm", ".iso", ".m3u", ".md", ".nsp", ".pbp", ".rvz", ".sfc",
    ".smc", ".wad", ".wbfs", ".wua", ".wud", ".xci", ".zip",
}


def _looks_like_path(value: str, extensions: set[str]) -> bool:
    cleaned = value.strip().strip('"\'')
    if not cleaned or cleaned.startswith("-"):
        return False
    suffix = PurePosixPath(cleaned.replace("\\", "/")).suffix.casefold()
    return suffix in extensions


def extract_rom(argv: Iterable[str], profile: dict) -> str | None:
    extensions = GENERIC_EXTENSIONS | {
        ext.casefold() if ext.startswith(".") else f".{ext.casefold()}"
        for ext in profile.get("rom_extensions", [])
    }
    candidates = [arg.strip().strip('"\'') for arg in argv if _looks_like_path(arg, extensions)]
    return candidates[-1] if candidates else None


def game_name_from_rom(rom: str | None, profile: dict | None = None) -> str | None:
    if not rom:
        return None
    path = Path(rom.replace("\\", "/"))
    markers = {
        str(marker).casefold() for marker in (profile or {}).get("game_name_parent_markers", [])
    }
    marker_index = next(
        (index for index, part in enumerate(path.parts) if part.casefold() in markers),
        None,
    )
    name = path.parts[marker_index - 1] if marker_index is not None and marker_index > 0 else path.stem
    name = re.sub(r"\s*[\[(](?:disc|disk|cd)\s*\d+[^\])]?[\])]\s*$", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name.replace("_", " ")).strip()
    return name or None
