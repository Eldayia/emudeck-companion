#!/usr/bin/env python3
"""Optional, standalone ES-DE event recorder and reversible CLI installer.

Installed copies contain no plugin imports and never execute event arguments.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4


HOOK_NAME = "emudeck-companion.py"
EVENTS = ("game-start", "game-end")
STATE_DIR = ".emudeck-companion-events"
MAX_EVENT_BYTES = 16384


def regular_file(path: Path, limit: int) -> bytes:
    # Reject symlinks, devices and FIFOs before opening; cap all reads.
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError(f"Not a bounded regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Not a regular file")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("File exceeds size limit")
    return data


def checked_directory(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"Not a real directory: {path}")


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()


def record_event(root: Path, event: str, args: list[str]) -> None:
    if event not in EVENTS or len(args) != 4:
        raise ValueError("Expected event and four ES-DE arguments")
    limits = (4096, 1024, 256, 1024)
    if any(not isinstance(v, str) or len(v) > limit or "\0" in v for v, limit in zip(args, limits)):
        raise ValueError("Invalid event arguments")
    if not Path(args[0]).is_absolute():
        raise ValueError("Expected an absolute ROM path")
    checked_directory(root)
    state = root / STATE_DIR
    state.mkdir(mode=0o700, exist_ok=True)
    checked_directory(state)
    payload = {
        "version": 1, "id": uuid4().hex, "event": event,
        "timestamp": time.time(), "boot_id": boot_id(),
        "rom": args[0], "game": args[1], "system": args[2], "system_name": args[3],
    }
    data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    if len(data) > MAX_EVENT_BYTES:
        raise ValueError("Event exceeds size limit")
    fd, temporary = tempfile.mkstemp(prefix=".event-", dir=state)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, state / "latest.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_status(root: Path | None, rom: str | None = None) -> dict:
    result = {"status": "not_installed", "root": str(root) if root else None,
              "installed_hooks": 0, "activation": "Not checked; enable custom event scripts in ES-DE"}
    if root is None:
        return result
    try:
        checked_directory(root)
        source = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
        for event in EVENTS:
            path = root / "scripts" / event / HOOK_NAME
            for parent in (path.parent.parent, path.parent):
                if parent.exists() or parent.is_symlink():
                    checked_directory(parent)
            if path.exists() or path.is_symlink():
                if regular_file(path, 65536) != source:
                    result["status"] = "modified_hooks"
                    return result
                result["installed_hooks"] += 1
        if result["installed_hooks"] != 2:
            result["status"] = "partial_install" if result["installed_hooks"] else "not_installed"
            return result
        result["status"] = "waiting_for_event"
        state = root / STATE_DIR
        if not state.exists():
            return result
        checked_directory(state)
        data = json.loads(regular_file(state / "latest.json", MAX_EVENT_BYTES))
        if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1 or data.get("event") not in EVENTS:
            raise ValueError("Invalid event schema")
        for field, limit in (("id", 32), ("boot_id", 64), ("rom", 4096), ("game", 1024),
                             ("system", 256), ("system_name", 1024)):
            if not isinstance(data.get(field), str) or len(data[field]) > limit or "\0" in data[field]:
                raise ValueError("Invalid event field")
        timestamp = data.get("timestamp")
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not 0 < timestamp <= time.time() + 5:
            raise ValueError("Invalid event timestamp")
        if len(data["id"]) != 32 or any(c not in "0123456789abcdef" for c in data["id"]) or not Path(data["rom"]).is_absolute():
            raise ValueError("Invalid event identity")
        if data["boot_id"] != boot_id():
            result["status"] = "previous_boot"
            return result
        result["status"] = "event_received"
        result["last_event"] = {key: data[key] for key in (
            "id", "event", "timestamp", "rom", "game", "system", "system_name")}
        result["same_rom"] = bool(rom and os.path.normpath(rom) == os.path.normpath(data["rom"]))
    except FileNotFoundError:
        pass
    except (OSError, ValueError, UnicodeError, RecursionError):
        result["status"] = "unreadable_or_invalid"
    return result


def manage(root: Path, operation: str) -> list[str]:
    root = root.expanduser().resolve(strict=True)
    checked_directory(root)
    if not any((root / name).is_file() for name in ("es_settings.xml", "settings/es_settings.xml")):
        raise ValueError("Choose the ES-DE application data folder containing es_settings.xml or settings/es_settings.xml")
    source = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    targets = [root / "scripts" / event / HOOK_NAME for event in EVENTS]
    # Preflight every target before changing anything; never overwrite user scripts.
    for path in targets:
        for parent in (path.parent.parent, path.parent):
            if parent.exists() or parent.is_symlink():
                checked_directory(parent)
        if path.exists() or path.is_symlink():
            if regular_file(path, 65536) != source:
                raise ValueError(f"Refusing to replace/remove an unknown or modified hook: {path}")
    changed = []
    if operation == "install":
        created = []
        try:
            for path in targets:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    with path.open("xb") as stream:
                        created.append(path)
                        stream.write(source)
                path.chmod(0o755)
                changed.append(str(path))
        except OSError:
            for path in created:
                path.unlink(missing_ok=True)
            raise
    elif operation == "remove":
        for path in targets:
            if path.exists():
                path.unlink()
                changed.append(str(path))
    else:
        raise ValueError("Unknown operation")
    return changed


def main() -> int:
    location = Path(__file__).absolute()
    if location.name == HOOK_NAME and location.parent.name in EVENTS:
        try:
            record_event(location.parents[2], location.parent.name, sys.argv[1:])
        except (OSError, ValueError, UnicodeError) as error:
            print(f"EmuDeck Companion hook: {error}", file=sys.stderr)
        return 0  # Recorder failures must not deliberately fail game launch.
    parser = argparse.ArgumentParser(description="Optional ES-DE lifecycle diagnostics (Linux/Steam Deck)")
    parser.add_argument("operation", choices=("install", "remove", "status"))
    parser.add_argument("--esde-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "status":
            print(json.dumps(read_status(args.esde_root.expanduser()), indent=2, ensure_ascii=False))
        else:
            if sys.platform != "linux" or os.geteuid() == 0:
                raise ValueError("Run as the desktop user on Linux, without sudo")
            print("\n".join(manage(args.esde_root, args.operation)))
            print("ES-DE settings unchanged. Enable custom event scripts manually after installation.")
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
