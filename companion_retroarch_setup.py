from __future__ import annotations

import os
import re
import stat
import tempfile
import uuid
from pathlib import Path

from companion_hotkey_config import MAX_CONFIG_BYTES


def configure_network(user_home: Path, backup_dir: Path, enabled: bool) -> dict:
    """Explicit setup for the user's standard EmuDeck RetroArch Flatpak config."""
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be a boolean")
    path = user_home / ".var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg"
    path = path.resolve(strict=True)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_CONFIG_BYTES:
        raise ValueError("RetroArch configuration is not a bounded regular file")
    with path.open("rb") as stream:
        original = stream.read(MAX_CONFIG_BYTES + 1)
    if len(original) > MAX_CONFIG_BYTES:
        raise ValueError("Oversized RetroArch configuration")
    text = original.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    # Put the enable flag before includes (first assignment wins). Leave every bind,
    # port setting, comment and unrelated byte unchanged.
    lines = [line for line in text.splitlines(keepends=True)
             if not re.match(r"^\s*network_cmd_enable\s*=", line)]
    changed = f'network_cmd_enable = "{str(enabled).lower()}"{newline}' + "".join(lines)
    updated = (b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b"") + changed.encode("utf-8")
    if original == updated:
        return {"ok": True, "message": "Setting already matches; restart RetroArch if necessary", "path": str(path)}
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / ("retroarch-before-network-" + uuid.uuid4().hex + ".cfg")
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(original)
        stream.flush()
        os.fsync(stream.fileno())
    fd, temporary = tempfile.mkstemp(prefix=".companion-network-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, stat.S_IMODE(before.st_mode))
        if hasattr(os, "chown"):
            os.chown(temporary, before.st_uid, before.st_gid)
        with path.open("rb") as stream:
            current = stream.read(MAX_CONFIG_BYTES + 1)
        if current != original:
            raise ValueError("RetroArch configuration changed during setup; nothing overwritten")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"ok": True, "path": str(path), "backup": str(backup),
            "message": f'Native commands {"enabled" if enabled else "disabled"}. Launch RetroArch again.'}
