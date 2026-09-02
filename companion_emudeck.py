from __future__ import annotations

from pathlib import Path
from typing import Iterable


def candidate_roots(user_home: Path, mount_root: Path = Path("/run/media")) -> Iterable[Path]:
    yield user_home / "Emulation"
    # EmuDeck also supports drives mounted directly below the user's home,
    # for example /home/deck/Elements/Emulation.
    try:
        for child in user_home.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                yield child / "Emulation"
    except OSError:
        pass
    if mount_root.is_dir():
        try:
            for user_dir in mount_root.iterdir():
                if user_dir.is_dir():
                    for device in user_dir.iterdir():
                        yield device / "Emulation"
        except OSError:
            pass


def candidate_esde_roots(user_home: Path, emulation_root: Path | None = None) -> Iterable[Path]:
    yield user_home / ".emulationstation"
    yield user_home / ".config" / "ES-DE"
    yield user_home / ".var" / "app" / "org.es_de.frontend" / "config" / "ES-DE"
    yield user_home / ".var" / "app" / "org.es_de.frontend" / "data" / "ES-DE"
    yield user_home / "ES-DE"
    if emulation_root is not None:
        yield emulation_root / "tools" / "downloaded_media"


def find_esde_root(user_home: Path, emulation_root: Path | None = None) -> Path | None:
    return next((path for path in candidate_esde_roots(user_home, emulation_root) if path.exists()), None)


def detect_emudeck(user_home: Path, mount_root: Path = Path("/run/media")) -> dict:
    for root in candidate_roots(user_home, mount_root):
        if root.is_dir() and ((root / "roms").is_dir() or (root / "bios").is_dir()):
            esde = find_esde_root(user_home, root)
            return {
                "detected": True,
                "root": str(root),
                "rom_root": str(root / "roms"),
                "save_root": str(root / "saves"),
                "bios_root": str(root / "bios"),
                "esde_detected": esde is not None,
                "esde_root": str(esde) if esde else None,
            }
    esde = find_esde_root(user_home)
    return {
        "detected": False,
        "root": None,
        "rom_root": None,
        "save_root": None,
        "bios_root": None,
        "esde_detected": esde is not None,
        "esde_root": str(esde) if esde else None,
    }
