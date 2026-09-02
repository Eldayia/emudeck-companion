from __future__ import annotations

import asyncio
import os
import signal
import time
from typing import Callable

from companion_input_backends import InputBackend, InputBackendError, select_input_backend
from companion_models import ActionResult, Session


class ActionEngine:
    def __init__(
        self,
        backend: InputBackend | None = None,
        debounce_ms: int = 250,
        frontend_input: bool = False,
    ) -> None:
        self.backend = backend if backend is not None else select_input_backend()
        self.frontend_input = frontend_input
        self.debounce_seconds = debounce_ms / 1000
        self._last_actions: dict[str, float] = {}

    async def execute(self, session: Session | None, action: str) -> ActionResult:
        if session is None:
            return ActionResult(False, action, "No active emulation session")
        if action not in session.capabilities or action not in session.actions:
            return ActionResult(False, action, f"{session.emulator_name} does not support this action")
        now = time.monotonic()
        debounce_key = f"{session.pid}:{action}"
        if now - self._last_actions.get(debounce_key, 0) < self.debounce_seconds:
            return ActionResult(False, action, "Action ignored to prevent a double trigger")
        self._last_actions[debounce_key] = now
        definition = session.actions[action]
        method = definition.get("method", "hotkey")
        keys: list[str] | None = None
        dispatch = "none"
        try:
            if method == "hotkey":
                keys = [str(key).format(slot=session.slot) for key in definition.get("keys", [])]
                if not keys:
                    return ActionResult(False, action, "The emulator profile has no hotkey for this action")
                if self.frontend_input:
                    # Steam's own controller keyboard API is available in the Decky
                    # frontend and works in Gamescope without extra system packages.
                    dispatch = "steam_input"
                elif self.backend is not None:
                    await self.backend.press(keys, session.pid)
                    dispatch = self.backend.name
                else:
                    return ActionResult(False, action, "No compatible virtual input backend is available")
            elif method == "select_slot":
                # Some emulators address slots directly in their save/load shortcuts.
                # Changing the Companion selection therefore requires no injected key.
                pass
            elif method == "signal":
                await self._send_signal(session.pid, definition.get("signal", "SIGTERM"))
                dispatch = "signal"
            else:
                return ActionResult(False, action, f"Unsupported action method: {method}")
        except (InputBackendError, OSError, asyncio.TimeoutError, ValueError) as error:
            return ActionResult(False, action, str(error))

        slot = None
        if action == "slot_next":
            session.slot = min(int(definition.get("maximum", 9)), session.slot + 1)
            slot = session.slot
        elif action == "slot_previous":
            session.slot = max(int(definition.get("minimum", 0)), session.slot - 1)
            slot = session.slot

        active = None
        if definition.get("mode") == "toggle":
            active = not session.toggles.get(action, False)
            session.toggles[action] = active
        label = definition.get("label", action.replace("_", " ").title())
        suffix = f" — Slot {session.slot}" if action in {"save_state", "load_state"} else ""
        return ActionResult(
            True,
            action,
            f"{label}{suffix}",
            slot=slot,
            active=active,
            keys=keys,
            dispatch=dispatch,
        )

    @staticmethod
    async def _send_signal(pid: int, signal_name: str) -> None:
        selected = getattr(signal, signal_name, None)
        if selected is None:
            raise ValueError(f"Unknown signal: {signal_name}")
        os.kill(pid, selected)
        await asyncio.sleep(0)

    async def release_all(self) -> None:
        if self.backend is not None:
            await self.backend.release_all()
