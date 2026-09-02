from __future__ import annotations

from pathlib import Path


def playlist_discs(rom: str | None) -> list[str]:
    """Return playable disc paths from an M3U playlist."""
    if not rom or Path(rom).suffix.lower() != ".m3u":
        return []
    playlist = Path(rom)
    try:
        lines = playlist.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return []
    discs: list[str] = []
    for line in lines:
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = playlist.parent / path
        discs.append(str(path.resolve(strict=False)))
    return discs
