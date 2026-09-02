from __future__ import annotations

import re
import socket
import time
from copy import deepcopy
from pathlib import Path
from typing import Callable

from companion_models import ProcessInfo, Session


COMMANDS = {
    "save_state": "SAVE_STATE", "load_state": "LOAD_STATE",
    "slot_previous": "STATE_SLOT_MINUS", "slot_next": "STATE_SLOT_PLUS",
    "fast_forward": "FAST_FORWARD", "pause": "PAUSE_TOGGLE",
    "previous_disc": "DISK_PREV", "next_disc": "DISK_NEXT",
    "screenshot": "SCREENSHOT", "fullscreen": "FULLSCREEN_TOGGLE", "quit": "QUIT",
    "emulator_menu": "MENU_TOGGLE", "menu_up": "MENU_UP", "menu_down": "MENU_DOWN",
    "menu_left": "MENU_LEFT", "menu_right": "MENU_RIGHT", "menu_confirm": "MENU_A",
    "menu_back": "MENU_B", "disk_eject": "DISK_EJECT_TOGGLE",
}
EXTRA_LABELS = {
    "emulator_menu": "Open / Close RetroArch Menu", "menu_up": "Up", "menu_down": "Down",
    "menu_left": "Left", "menu_right": "Right", "menu_confirm": "Confirm", "menu_back": "Back",
    "disk_eject": "Open / Close Disc Tray",
}


def settings_actions(profile: dict) -> set[str]:
    """Include dynamically offered actions in persisted favorites/visibility rules."""
    allowed = set(profile["actions"])
    if profile.get("hotkey_config_format") == "retroarch":
        allowed.update(EXTRA_LABELS)
        if "next_disc" not in profile["capabilities"]:
            allowed.discard("disk_eject")
    return allowed


def udp_owner(table: str, inodes: set[str], port: int) -> str | None:
    """Reject shared ports and listeners not reachable locally; wildcard is allowed."""
    matches = []
    for line in table.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 10:
            continue
        local = fields[1].split(":")
        if len(local) != 2:
            continue
        try:
            selected_port = int(local[1], 16)
        except ValueError:
            continue
        if selected_port == port:
            matches.append(fields)
    if len(matches) != 1:
        return None
    fields = matches[0]
    if (fields[1].split(":")[0] not in {"00000000", "0100007F"}
            or fields[2] != "00000000:0000" or fields[9] not in inodes):
        return None
    return fields[9]


def owned_endpoint(pid: int, port: int, proc_root: Path = Path("/proc")) -> str | None:
    try:
        process = proc_root / str(pid)
        if (process / "ns/net").readlink() != (proc_root / "self/ns/net").readlink():
            return None
        inodes: set[str] = set()
        for count, fd in enumerate((process / "fd").iterdir()):
            if count >= 4096:
                return None
            try:
                link = str(fd.readlink())
            except OSError:
                continue
            match = re.fullmatch(r"socket:\[(\d+)\]", link)
            if match:
                inodes.add(match[1])
        with (process / "net/udp").open("rb") as stream:
            data = stream.read(256 * 1024 + 1)
        if len(data) > 256 * 1024:
            return None
        return udp_owner(data.decode("ascii"), inodes, port)
    except (OSError, ValueError):
        return None


class RetroArchCommands:
    """Only send to an IPv4 loopback endpoint owned by the selected emulator PID."""

    def __init__(self, owner: Callable[[int, int], str | None] = owned_endpoint, timeout: float = 0.15):
        self.owner = owner
        self.timeout = timeout
        self._cache: dict = {}

    def _socket(self, port: int):
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            connection.settimeout(self.timeout)
            connection.connect(("127.0.0.1", port))
        except Exception:
            connection.close()
            raise
        return connection

    @staticmethod
    def _query(connection, command: str) -> str:
        connection.send(command.encode("ascii") + b"\n")
        return connection.recv(1024).decode("utf-8", "strict").strip()

    def inspect(self, pid: int, port: int, force: bool = False) -> dict:
        result = {"status": "unavailable", "port": port,
                  "reason": "No exclusive local UDP listener owned by this RetroArch process"}
        if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
            return {**result, "reason": "Invalid network command port"}
        inode = self.owner(pid, port)
        if not inode:
            self._cache = {}
            return result
        key = (pid, port, inode)
        if not force and self._cache.get("key") == key and time.monotonic() < self._cache["expires"]:
            return dict(self._cache["result"])
        try:
            with self._socket(port) as connection:
                version = self._query(connection, "VERSION")
                match = re.fullmatch(r"(\d+)\.(\d+)(?:[\w.+() -]{0,64})", version)
                if not match or tuple(map(int, match.groups())) < (1, 19):
                    raise ValueError("RetroArch 1.19 or newer was not identified")
                state = self._query(connection, "GET_STATUS")
                if not re.match(r"^GET_STATUS (?:PLAYING |PAUSED |CONTENTLESS\b)", state):
                    raise ValueError("Unexpected RetroArch status reply")
            if self.owner(pid, port) != inode:
                raise ValueError("RetroArch command socket changed")
            result = {"status": "ready", "port": port, "inode": inode, "version": version,
                      "reason": "Local native commands verified; action execution is not acknowledged by UDP"}
        except (OSError, ValueError) as error:
            result["reason"] = f"Native interface did not validate: {error}"
        self._cache = {"key": key, "expires": time.monotonic() + 3, "result": dict(result)}
        return result

    def apply(self, original: dict, effective: dict, process: ProcessInfo) -> dict:
        if original.get("hotkey_config_format") != "retroarch":
            return effective
        effective = deepcopy(effective)
        settings = effective["hotkey_config"].get("network_settings", {})
        report = self.inspect(process.pid, settings.get("port", 55355))
        effective["hotkey_config"]["native_commands"] = report
        if report["status"] != "ready":
            return effective
        capabilities = list(original["capabilities"])
        for action, label in EXTRA_LABELS.items():
            if action == "disk_eject" and "next_disc" not in capabilities:
                continue
            capabilities.append(action)
            effective["actions"][action] = {"label": label}
        disabled = effective["hotkey_config"]["disabled_actions"]
        for action in capabilities:
            if action not in COMMANDS:
                continue
            definition = effective["actions"][action]
            definition.update(method="retroarch_udp", command=COMMANDS[action],
                              command_port=report["port"], command_inode=report["inode"],
                              binding_source="RetroArch native commands")
            definition.pop("keys", None)
            # Without an acknowledgement, do not present guessed toggle states as ON.
            definition.pop("mode", None)
            disabled.pop(action, None)
        effective["capabilities"] = [action for action in capabilities if action not in disabled]
        return effective

    def execute(self, session: Session, action: str) -> None:
        if session.emulator not in {"retroarch", "fbneo"} or action not in COMMANDS:
            raise ValueError("Unsupported native action")
        definition = session.actions[action]
        if definition.get("command") != COMMANDS[action]:
            raise ValueError("Invalid native command mapping")
        port = definition.get("command_port")
        report = self.inspect(session.pid, port, force=True)
        if report["status"] != "ready" or report.get("inode") != definition.get("command_inode"):
            raise ValueError("RetroArch native endpoint changed or is unavailable; refresh detection")
        with self._socket(port) as connection:
            if self.owner(session.pid, port) != report["inode"]:
                raise ValueError("RetroArch command socket changed before dispatch")
            # Exactly one action datagram. Never retry a toggle/save after an uncertain send.
            connection.send((COMMANDS[action] + "\n").encode("ascii"))
        self._cache = {}
