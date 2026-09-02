from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from companion_models import ProcessInfo


MAX_CONFIG_BYTES = 1024 * 1024
MODIFIERS = {"leftctrl", "leftalt", "leftshift"}
SUPPORTED_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789") | MODIFIERS | {
    *(f"f{number}" for number in range(1, 13)),
    "enter", "esc", "tab", "space", "insert", "home", "end", "pageup",
    "pagedown", "delete", "backspace", "up", "down", "left", "right",
}
KEY_ALIASES = {
    "control": "leftctrl", "ctrl": "leftctrl", "shift": "leftshift",
    "alt": "leftalt", "escape": "esc", "return": "enter",
}


def keyboard_binding(value: str) -> list[str] | None:
    """Accept a complete keyboard chord, never the keyboard part of a mixed chord."""
    parts = value.split("&")
    if not 1 <= len(parts) <= 4:
        return None
    keys: list[str] = []
    for part in parts:
        source, separator, name = part.strip().partition("/")
        if separator != "/" or source != "Keyboard":
            return None
        key = KEY_ALIASES.get(name.casefold(), name.casefold())
        if key not in SUPPORTED_KEYS or key in keys:
            return None
        keys.append(key)
    if all(key in MODIFIERS for key in keys):
        return None
    return sorted(keys, key=lambda key: key not in MODIFIERS)


def parse_hotkeys(text: str) -> dict[str, list[str]]:
    """DuckStation stores alternative bindings as repeated INI keys."""
    section = ""
    result: dict[str, list[str]] = {}
    for raw in text.lstrip("\ufeff").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise ValueError("Malformed section")
            section = line[1:-1].strip()
        elif section == "Hotkeys":
            key, separator, value = line.partition("=")
            if not separator or not key.strip():
                raise ValueError("Malformed hotkey")
            result.setdefault(key.strip(), []).append(value.strip())
    return result


class DuckStationHotkeyConfig:
    """Read-only global settings resolver for EmuDeck AppImage and legacy Flatpak."""

    def __init__(self, user_home: Path, proc_root: Path = Path("/proc")) -> None:
        self.user_home = user_home
        self.proc_root = proc_root
        self._signature: tuple | None = None
        self._bindings: dict[str, list[str]] = {}

    def _config_path(self, process: ProcessInfo) -> Path:
        # Read only the variables needed to locate this process's configuration.
        environment: dict[str, str] = {}
        try:
            with (self.proc_root / str(process.pid) / "environ").open("rb") as stream:
                for entry in stream.read(128 * 1024).decode("utf-8", "replace").split("\0"):
                    key, separator, value = entry.partition("=")
                    if separator and key in {"HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "FLATPAK_ID"}:
                        environment[key] = value
        except OSError:
            pass
        home = Path(environment.get("HOME", str(self.user_home)))
        if not home.is_absolute():
            home = self.user_home
        flatpak = environment.get("FLATPAK_ID") == "org.duckstation.DuckStation" or any(
            "org.duckstation.DuckStation" in arg or arg.startswith("/app/bin/duckstation")
            for arg in process.argv
        )
        if flatpak:
            default = self.user_home / ".var/app/org.duckstation.DuckStation/config"
            root = Path(environment.get("XDG_CONFIG_HOME", str(default)))
        else:
            default = home / ".local/share"
            root = Path(environment.get("XDG_DATA_HOME", str(default)))
        return (root if root.is_absolute() else default) / "duckstation/settings.ini"

    def __call__(self, profile: dict[str, Any], process: ProcessInfo) -> dict[str, Any]:
        if profile["id"] != "duckstation":
            return profile
        effective = deepcopy(profile)
        path = self._config_path(process)
        status = "configured"
        bindings: dict[str, list[str]] = {}
        try:
            stat = path.stat()
            if stat.st_size > MAX_CONFIG_BYTES:
                raise ValueError("Oversized config")
            signature = (str(path), stat.st_mtime_ns, stat.st_size)
            if signature != self._signature:
                with path.open("rb") as stream:
                    content = stream.read(MAX_CONFIG_BYTES + 1)
                if len(content) > MAX_CONFIG_BYTES:
                    raise ValueError("Oversized config")
                self._bindings = parse_hotkeys(content.decode("utf-8-sig"))
                self._signature = signature
            bindings = self._bindings
        except FileNotFoundError:
            status = "fallback"
            self._signature = None
        except (OSError, ValueError, UnicodeError):
            status = "unavailable"
            self._signature = None

        disabled: dict[str, str] = {}
        for action, setting in profile.get("hotkey_settings", {}).items():
            if status == "fallback" and action not in profile.get("requires_config", []):
                continue
            keys = next((parsed for value in bindings.get(setting, [])
                         if (parsed := keyboard_binding(value)) is not None), None)
            if keys is None:
                reason = "No supported keyboard binding (unset, controller-only or unsupported key)"
                if status != "configured":
                    reason = "No verified binding: configuration " + status
                disabled[action] = reason
            else:
                effective["actions"][action]["keys"] = keys
                effective["actions"][action]["binding_source"] = "DuckStation global settings"
        effective["capabilities"] = [a for a in profile["capabilities"] if a not in disabled]
        effective["hotkey_config"] = {
            "status": status, "path": str(path), "disabled_actions": disabled,
            "scope": "Global settings on disk; game-specific input profiles are not resolved",
        }
        return effective
