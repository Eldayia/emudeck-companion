from __future__ import annotations

import time
import uuid
from collections import deque
from copy import deepcopy
from typing import Callable

from companion_models import ActionResult, Session


class ActionHistory:
    """Bounded, in-memory dispatch journal. Sending input is not emulator success."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self.entries: deque[dict] = deque(maxlen=30)
        self.last_result: dict | None = None

    def _update(self, entry: dict, status: str, message: str) -> None:
        entry.update(status=status, message=message[:400])
        if self.last_result and self.last_result["request_id"] == entry["id"]:
            self.last_result.update(ok=status in {"sent", "completed"}, message=entry["message"])

    def _expire(self) -> None:
        now = self.clock()
        for entry in self.entries:
            if entry["status"] == "pending" and now >= entry["_deadline"]:
                self._update(entry, "unknown", "Keyboard delivery not reported; outcome unknown (no retry)")

    def record(self, result: ActionResult, session: Session | None) -> dict:
        self._expire()
        request_id = uuid.uuid4().hex
        payload = {**result.as_dict(), "request_id": request_id}
        pending = result.ok and result.dispatch == "steam_input"
        status = "pending" if pending else "failed" if not result.ok else "completed" if result.dispatch == "none" else "sent"
        message = result.message[:300]
        if pending:
            message += " — waiting for keyboard dispatch"
        elif status == "sent" and result.dispatch != "retroarch_udp":
            message += " — input sent, execution not confirmed"
        entry = {
            "id": request_id, "timestamp": time.time(), "action": str(result.action)[:80],
            "emulator": session.emulator[:80] if session else None,
            "game": session.game[:160] if session and session.game else None,
            "pid": session.pid if session else None, "dispatch": result.dispatch,
            "session_id": session.session_id if session else None,
            "status": status, "message": message[:400],
            "_deadline": self.clock() + 15,
        }
        self.entries.append(entry)
        self.last_result = deepcopy(payload)
        self.last_result["message"] = entry["message"]
        return payload

    def report_keyboard(self, request_id: str, delivered: bool, error: str = "") -> bool:
        self._expire()
        if not isinstance(request_id, str) or not isinstance(delivered, bool) or not isinstance(error, str):
            return False
        entry = next((item for item in self.entries if item["id"] == request_id), None)
        if entry is None or entry["status"] != "pending":
            return False
        if delivered:
            self._update(entry, "sent", "Keyboard input sent; execution not confirmed")
        else:
            self._update(entry, "failed", f"Keyboard dispatch failed (input may be partial): {error[:250] or 'unspecified error'}")
        return True

    def snapshot(self) -> dict:
        self._expire()
        return {
            "last_action": deepcopy(self.last_result),
            "action_history": [
                {key: value for key, value in entry.items() if not key.startswith("_")}
                for entry in reversed(self.entries)
            ],
        }
