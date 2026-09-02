from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from companion_hotkey_config import MAX_CONFIG_BYTES, process_environment
from companion_models import ProcessInfo


MAX_CONFIG_FILES = 8
HOTKEY_SETTINGS = {
    "save_state": "input_save_state",
    "load_state": "input_load_state",
    "slot_previous": "input_state_slot_decrease",
    "slot_next": "input_state_slot_increase",
    "fast_forward": "input_toggle_fast_forward",
    "pause": "input_pause_toggle",
    "rewind": "input_rewind",
    "previous_disc": "input_disk_prev",
    "next_disc": "input_disk_next",
    "screenshot": "input_screenshot",
    "fullscreen": "input_toggle_fullscreen",
    "quit": "input_exit_emulator",
}
CONFIG_KEYS = set(HOTKEY_SETTINGS.values()) | {"input_enable_hotkey", "input_hotkey_device_merge"}
KEYS = {key: key for key in "abcdefghijklmnopqrstuvwxyz"} | {
    f"num{number}": str(number) for number in range(10)
} | {f"f{number}": f"f{number}" for number in range(1, 13)} | {
    key: key for key in (
        "enter", "tab", "insert", "end", "home", "space", "pageup", "pagedown",
        "backspace", "left", "right", "up", "down",
    )
} | {"escape": "esc", "del": "delete", "ctrl": "leftctrl", "shift": "leftshift", "alt": "leftalt"}


def parse_retroarch_config(text: str) -> list[tuple[str, str]]:
    """Retain relevant assignments and include positions, not account settings."""
    entries: list[tuple[str, str]] = []
    for raw in text.lstrip("\ufeff").splitlines():
        line = raw.strip()
        if re.match(r"#include(?:\s|$)", line):
            match = re.fullmatch(r'#include\s+"([^"\n]+)"\s*(?:#.*)?', line)
            if not match:
                raise ValueError("Malformed #include directive")
            entries.append(("#include", match[1]))
            continue
        if not line or line.startswith("#"):
            continue
        key = re.split(r'[\s=]', line, maxsplit=1)[0]
        if key not in CONFIG_KEYS:
            continue
        match = re.fullmatch(r'([a-z_]+)\s*=\s*(?:"([^"\n]*)"|([^\s"#]+))\s*(?:#.*)?', line)
        if not match:
            raise ValueError("Malformed hotkey setting")
        entries.append((key, match[2] if match[2] is not None else match[3]))
    return entries


class RetroArchHotkeyConfig:
    """Read global/CLI configuration only; automatic content overrides are not inferred."""

    def __init__(self, user_home: Path, proc_root: Path = Path("/proc")) -> None:
        self.user_home = user_home
        self.proc_root = proc_root
        self._cache: dict[Path, tuple[tuple[int, int], list[tuple[str, str]]]] = {}

    def _path(self, value: str, base: Path, home: Path) -> Path:
        if value.startswith("~/"):
            return home / value[2:]
        path = Path(value)
        return path if path.is_absolute() else base / path

    @staticmethod
    def _exists(path: Path) -> bool:
        # Path.exists() can suppress permission errors on newer Python versions.
        # Only a genuinely missing file may enable default-key fallback.
        try:
            path.stat()
        except FileNotFoundError:
            return False
        return True

    def _locations(self, process: ProcessInfo) -> tuple[Path, list[Path], bool, Path]:
        env = process_environment(self.proc_root, process.pid)
        home = Path(env.get("HOME", str(self.user_home)))
        if not home.is_absolute():
            home = self.user_home
        flatpak = env.get("FLATPAK_ID") == "org.libretro.RetroArch" or any(
            arg == "org.libretro.RetroArch" or arg.startswith("/app/bin/retroarch")
            for arg in process.argv
        )
        if not flatpak:
            flatpak = (self.proc_root / str(process.pid) / "root/.flatpak-info").is_file()
        default = home / ".config"
        if flatpak:
            default = self.user_home / ".var/app/org.libretro.RetroArch/config"
        root = Path(env.get("XDG_CONFIG_HOME", str(default)))
        if not root.is_absolute():
            root = default
        path = root / "retroarch/retroarch.cfg"
        if not flatpak and not self._exists(path):
            for candidate in (
                home / ".config/retroarch/retroarch.cfg", home / ".retroarch.cfg",
                self.proc_root / str(process.pid) / "root/etc/retroarch.cfg",
            ):
                if self._exists(candidate):
                    path = candidate
                    break
        explicit: str | None = None
        appended: str | None = None
        args = iter(process.argv[1:])
        for arg in args:
            if arg == "--":
                break
            if arg in {"-c", "--config", "--appendconfig"}:
                value = next(args, "")
                if not value or value.startswith("-"):
                    raise ValueError("Missing configuration argument")
                if arg == "--appendconfig":
                    appended = value
                else:
                    explicit = value
            elif arg.startswith("--config="):
                explicit = arg.partition("=")[2]
            elif arg.startswith("--appendconfig="):
                appended = arg.partition("=")[2]
            elif arg.startswith("-c") and len(arg) > 2:
                explicit = arg[2:]
        if explicit == "" or appended == "":
            raise ValueError("Empty configuration argument")
        values = ([explicit] if explicit is not None else []) + (appended.split("|") if appended else [])
        if any(not value for value in values) or len(values) > MAX_CONFIG_FILES:
            raise ValueError("Invalid or excessive configuration file list")
        # Relative CLI paths are relative to the emulator, never the Decky process.
        cwd = home
        if any(not Path(value).is_absolute() and not value.startswith("~/") for value in values):
            cwd = (self.proc_root / str(process.pid) / "cwd").resolve(strict=True)
        if explicit is not None:
            path = self._path(explicit, cwd, home)
        extras = [self._path(value, cwd, home) for value in appended.split("|")] if appended else []
        return path, extras, explicit is not None, home

    def _load(self, path: Path, home: Path, active: set[Path], visited: list[Path]) -> dict[str, str]:
        path = path.resolve(strict=True)
        if path in active or len(visited) >= MAX_CONFIG_FILES:
            raise ValueError("Configuration include cycle or file limit reached")
        visited.append(path)
        stat = path.stat()
        if not path.is_file() or stat.st_size > MAX_CONFIG_BYTES:
            raise ValueError("Configuration is not a bounded regular file")
        signature = (stat.st_mtime_ns, stat.st_size)
        cached = self._cache.get(path)
        if cached is None or cached[0] != signature:
            with path.open("rb") as stream:
                content = stream.read(MAX_CONFIG_BYTES + 1)
            if len(content) > MAX_CONFIG_BYTES:
                raise ValueError("Oversized configuration")
            entries = parse_retroarch_config(content.decode("utf-8-sig"))
            self._cache[path] = signature, entries
        else:
            entries = cached[1]
        result: dict[str, str] = {}
        for key, value in entries:
            if key == "#include":
                nested = self._load(self._path(value, path.parent, home), home, active | {path}, visited)
                for nested_key, nested_value in nested.items():
                    result.setdefault(nested_key, nested_value)
            else:
                # Like RetroArch, the first occurrence within a file wins.
                result.setdefault(key, value)
        return result

    def __call__(self, profile: dict[str, Any], process: ProcessInfo) -> dict[str, Any]:
        if profile.get("hotkey_config_format") != "retroarch":
            return profile
        effective = deepcopy(profile)
        status, reason = "configured", ""
        path: Path | None = None
        visited: list[Path] = []
        values: dict[str, str] = {}
        try:
            path, extras, explicit, home = self._locations(process)
            if not explicit and not self._exists(path):
                status = "fallback"
            else:
                values = self._load(path, home, set(), visited)
            for extra in extras:
                values.update(self._load(extra, home, set(), visited))
                status = "configured"
        except (OSError, ValueError, RuntimeError):
            status, reason = "unavailable", "Configuration could not be read completely (path, syntax, include or size limit)"
            values = {}
        finally:
            self._cache = {key: value for key, value in self._cache.items() if key in visited}

        enabler_value = values.get("input_enable_hotkey", "nul").casefold()
        enabler = KEYS.get(enabler_value)
        if status != "unavailable":
            if enabler_value != "nul" and enabler is None:
                reason = "Unsupported keyboard hotkey enabler"
            merge = values.get("input_hotkey_device_merge", "false").casefold()
            if merge not in {"true", "false", "1", "0"}:
                reason = "Unsupported hotkey device merge setting"
            elif merge in {"true", "1"} and enabler is None:
                reason = "Merged hotkey devices may require a controller enabler; keyboard-only dispatch is unavailable"

        disabled: dict[str, str] = {}
        for action in profile["capabilities"]:
            setting = HOTKEY_SETTINGS.get(action)
            if not setting:
                continue
            if action == "rewind":
                disabled[action] = "Rewind requires a held key; Companion does not support hold actions yet"
                continue
            if reason:
                disabled[action] = reason
                continue
            definition = effective["actions"][action]
            if setting in values:
                key = KEYS.get(values[setting].casefold())
                if key is None:
                    disabled[action] = "Keyboard binding is disabled (nul) or unsupported"
                    continue
                keys = [key]
                source = "RetroArch configuration on disk"
            elif action in {"previous_disc", "next_disc"}:
                disabled[action] = "No configured keyboard disc shortcut"
                continue
            else:
                keys = list(definition["keys"])
                source = "Bundled default (setting absent)"
            if enabler:
                if enabler in keys:
                    disabled[action] = "Action shares its key with the hotkey enabler"
                    continue
                keys.insert(0, enabler)
            definition["keys"] = keys
            definition["binding_source"] = source
        effective["capabilities"] = [action for action in profile["capabilities"] if action not in disabled]
        effective["hotkey_config"] = {
            "status": status, "path": str(path) if path else "", "paths": [str(p) for p in visited],
            "disabled_actions": disabled,
            "scope": "Global and CLI configs on disk; automatic core/content overrides and unsaved changes are not resolved",
        }
        return effective
