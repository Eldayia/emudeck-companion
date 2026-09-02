from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


DOCUMENT_EXTENSIONS = (".pdf", ".txt", ".md", ".markdown", ".html", ".htm")
DOCUMENT_TITLES = {
    "manual": "Manual",
    "controls": "Controls",
    "guide": "Guide",
    "notes": "Notes",
}


class DocumentIndex:
    """Discover local, game-specific documents without scanning the full library."""

    def __init__(self, emulation_root: Path | None, rom_root: Path | None) -> None:
        self.emulation_root = emulation_root
        self.rom_root = rom_root

    @staticmethod
    def _document(path: Path, title: str | None = None) -> dict[str, Any] | None:
        try:
            resolved = path.expanduser().resolve(strict=True)
            if not resolved.is_file() or resolved.suffix.casefold() not in DOCUMENT_EXTENSIONS:
                return None
            stat = resolved.stat()
        except (OSError, RuntimeError):
            return None
        stem = re.sub(r"[_-]+", " ", resolved.stem).strip()
        label = title or DOCUMENT_TITLES.get(stem.casefold()) or stem.title()
        return {
            "id": hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16],
            "title": label,
            "path": str(resolved),
            "url": resolved.as_uri(),
            "format": resolved.suffix.casefold().lstrip("."),
            "size": stat.st_size,
        }

    def lookup(self, rom: str | None, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        if not rom:
            return []
        rom_path = Path(rom)
        documents: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add(path: Path, title: str | None = None) -> None:
            document = self._document(path, title)
            if document and document["path"] not in seen:
                seen.add(document["path"])
                documents.append(document)

        manual = metadata.get("manual")
        if isinstance(manual, str) and manual:
            add(Path(manual), "Manual")

        for extension in DOCUMENT_EXTENSIONS:
            add(rom_path.with_suffix(extension), "Manual" if extension == ".pdf" else None)

        directories = [rom_path.parent / rom_path.stem]
        if self.emulation_root and self.rom_root:
            try:
                relative = rom_path.resolve(strict=False).relative_to(self.rom_root.resolve(strict=False))
                system = relative.parts[0]
                directories.extend([
                    self.emulation_root / "documents" / system / rom_path.stem,
                    self.emulation_root / "docs" / system / rom_path.stem,
                ])
            except (ValueError, IndexError, OSError):
                pass
        for directory in directories:
            try:
                children = sorted(directory.iterdir(), key=lambda item: item.name.casefold())
            except OSError:
                continue
            for child in children:
                add(child)
                if len(documents) >= 32:
                    return documents
        return documents
