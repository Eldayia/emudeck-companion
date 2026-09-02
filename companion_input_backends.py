from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod


class InputBackendError(RuntimeError):
    pass


class InputBackend(ABC):
    name = "unavailable"

    @abstractmethod
    async def press(self, keys: list[str], pid: int) -> None:
        raise NotImplementedError

    async def release_all(self) -> None:
        return None


async def _run(argv: list[str], env: dict[str, str] | None = None) -> None:
    process = await asyncio.create_subprocess_exec(
        *argv,
        env=env,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(process.communicate(), timeout=3)
    if process.returncode != 0:
        raise InputBackendError(stderr.decode("utf-8", "replace").strip() or f"{argv[0]} failed")


class YdotoolBackend(InputBackend):
    name = "ydotool"

    _codes = {
        "esc": 1, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
        "6": 7, "7": 8, "8": 9, "9": 10, "0": 11, "tab": 15,
        "q": 16, "w": 17, "e": 18, "r": 19, "p": 25, "a": 30,
        "s": 31, "d": 32, "f": 33, "l": 38, "space": 57,
        "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63,
        "f6": 64, "f7": 65, "f8": 66, "f9": 67, "f10": 68,
        "leftctrl": 29, "leftshift": 42, "leftalt": 56, "enter": 28,
    }

    async def press(self, keys: list[str], pid: int) -> None:
        del pid
        try:
            codes = [self._codes[key.casefold()] for key in keys]
        except KeyError as error:
            raise InputBackendError(f"Unsupported ydotool key: {error.args[0]}") from error
        events = [f"{code}:1" for code in codes] + [f"{code}:0" for code in reversed(codes)]
        await _run(["ydotool", "key", *events])


class WtypeBackend(InputBackend):
    name = "wtype"

    _modifiers = {"leftctrl": "CTRL", "leftshift": "SHIFT", "leftalt": "ALT"}

    async def press(self, keys: list[str], pid: int) -> None:
        del pid
        argv = ["wtype"]
        modifiers = [self._modifiers[key.casefold()] for key in keys if key.casefold() in self._modifiers]
        normal_keys = [key for key in keys if key.casefold() not in self._modifiers]
        for modifier in modifiers:
            argv.extend(["-M", modifier])
        for key in normal_keys:
            argv.extend(["-k", key])
        for modifier in reversed(modifiers):
            argv.extend(["-m", modifier])
        if not normal_keys:
            raise InputBackendError("A wtype action needs at least one non-modifier key")
        await _run(argv)


class XdotoolBackend(InputBackend):
    name = "xdotool"

    _names = {"leftctrl": "ctrl", "leftshift": "shift", "leftalt": "alt", "esc": "Escape"}

    async def press(self, keys: list[str], pid: int) -> None:
        key_combo = "+".join(self._names.get(key.casefold(), key) for key in keys)
        env = dict(os.environ)
        # --pid targets the emulator window rather than whichever QAM surface owns focus.
        search = await asyncio.create_subprocess_exec(
            "xdotool", "search", "--onlyvisible", "--pid", str(pid),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
        )
        stdout, _ = await asyncio.wait_for(search.communicate(), timeout=3)
        windows = stdout.decode().split()
        if not windows:
            raise InputBackendError("No visible emulator window found")
        await _run(["xdotool", "key", "--window", windows[-1], "--clearmodifiers", key_combo], env)


def select_input_backend() -> InputBackend | None:
    if shutil.which("ydotool"):
        return YdotoolBackend()
    if shutil.which("wtype") and os.environ.get("WAYLAND_DISPLAY"):
        return WtypeBackend()
    if shutil.which("xdotool") and os.environ.get("DISPLAY"):
        return XdotoolBackend()
    return None
