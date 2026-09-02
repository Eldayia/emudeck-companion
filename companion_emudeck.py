from __future__ import annotations

from pathlib import Path
from typing import Iterable


def candidate_roots(user_home: Path, mount_root: Path = Path("/run/media")) -> Iterable[Path]:
    yield user_home / "Emulation"
    if mount_root.is_dir():
        for user_dir in mount_root.iterdir():
            if user_dir.is_dir():
                for device in user_dir.iterdir():
                    yield device / "Emulation"


def detect_emudeck(user_home: Path, mount_root: Path = Path("/run/media")) -> dict:
    for root in candidate_roots(user_home, mount_root):
        if root.is_dir() and ((root / "roms").is_dir() or (root / "bios").is_dir()):
            esde_candidates = [
                user_home / ".emulationstation",
                user_home / ".config" / "ES-DE",
                root / "tools" / "downloaded_media",
            ]
            esde = next((path for path in esde_candidates if path.exists()), None)
            return {
                "detected": True,
                "root": str(root),
                "rom_root": str(root / "roms"),
                "save_root": str(root / "saves"),
                "bios_root": str(root / "bios"),
                "esde_detected": esde is not None,
                "esde_root": str(esde) if esde else None,
            }
    return {
        "detected": False,
        "root": None,
        "rom_root": None,
        "save_root": None,
        "bios_root": None,
        "esde_detected": False,
        "esde_root": None,
    }
