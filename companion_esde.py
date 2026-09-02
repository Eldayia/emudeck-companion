from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


METADATA_FIELDS = (
    "name", "desc", "developer", "publisher", "genre", "releasedate",
    "players", "rating", "image", "marquee", "video", "manual",
)
MEDIA_KINDS = {
    "image": ("covers", "miximages", "screenshots", "titlescreens"),
    "marquee": ("marquees", "3dboxes"),
    "video": ("videos",),
    "manual": ("manuals",),
}
MEDIA_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mkv", ".pdf")


def _normal(path: Path) -> str:
    return str(path.resolve(strict=False)).replace("\\", "/").casefold()


class ESDEMetadataIndex:
    """Small, mtime-aware cache for ES-DE gamelists and scraped media."""

    def __init__(self, esde_root: Path | None, rom_root: Path | None, emulation_root: Path | None = None):
        self.esde_root = esde_root
        self.rom_root = rom_root
        self.media_roots = self._media_roots(emulation_root)
        self._cache: dict[Path, tuple[tuple[int, int], dict[str, dict[str, Any]]]] = {}

    def _media_roots(self, emulation_root: Path | None) -> list[Path]:
        candidates: list[Path] = []
        if self.esde_root:
            candidates.extend([self.esde_root / "downloaded_media", self.esde_root])
        if emulation_root:
            candidates.append(emulation_root / "tools" / "downloaded_media")
        return list(dict.fromkeys(candidates))

    def _gamelists_root(self) -> Path | None:
        if not self.esde_root:
            return None
        root = self.esde_root / "gamelists"
        return root if root.is_dir() else None

    def _parse(self, xml_path: Path, system_rom_root: Path) -> dict[str, dict[str, Any]]:
        try:
            stat = xml_path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            return {}
        cached = self._cache.get(xml_path)
        if cached and cached[0] == signature:
            return cached[1]
        entries: dict[str, dict[str, Any]] = {}
        try:
            root = ET.parse(xml_path).getroot()
            for game in root.findall("game"):
                raw_path = (game.findtext("path") or "").strip()
                if not raw_path:
                    continue
                game_path = Path(raw_path).expanduser()
                if not game_path.is_absolute():
                    game_path = system_rom_root / game_path
                data = {
                    field: value.strip()
                    for field in METADATA_FIELDS
                    if (value := game.findtext(field)) and value.strip()
                }
                entries[_normal(game_path)] = data
        except (OSError, ET.ParseError):
            entries = {}
        self._cache[xml_path] = (signature, entries)
        return entries

    def lookup(self, rom: str | None) -> dict[str, Any]:
        if not rom or not self.rom_root:
            return {}
        rom_path = Path(rom)
        try:
            relative = rom_path.resolve(strict=False).relative_to(self.rom_root.resolve(strict=False))
            system = relative.parts[0]
        except (ValueError, IndexError, OSError):
            system = rom_path.parent.name
        metadata: dict[str, Any] = {}
        gamelists = self._gamelists_root()
        if gamelists:
            xml_path = gamelists / system / "gamelist.xml"
            metadata.update(self._parse(xml_path, self.rom_root / system).get(_normal(rom_path), {}))
        self._resolve_media(metadata, rom_path, system)
        return metadata

    def _resolve_media(self, metadata: dict[str, Any], rom: Path, system: str) -> None:
        names = tuple(dict.fromkeys((rom.stem, rom.name)))
        for field, directories in MEDIA_KINDS.items():
            existing = metadata.get(field)
            if existing:
                path = Path(existing).expanduser()
                if not path.is_absolute() and self.esde_root:
                    path = self.esde_root / path
                metadata[field] = str(path.resolve(strict=False))
                continue
            for media_root in self.media_roots:
                found = self._find_media(media_root / system, directories, names)
                if found:
                    metadata[field] = str(found)
                    break

    @staticmethod
    def _find_media(system_root: Path, directories: tuple[str, ...], names: tuple[str, ...]) -> Path | None:
        for directory in directories:
            parent = system_root / directory
            for name in names:
                for extension in MEDIA_EXTENSIONS:
                    candidate = parent / f"{name}{extension}"
                    if candidate.is_file():
                        return candidate
        return None
