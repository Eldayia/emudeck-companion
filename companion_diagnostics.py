from __future__ import annotations

import platform
import time


def build_diagnostics(session: dict | None, emudeck: dict, input_backend: str | None, last_action: dict | None) -> dict:
    return {
        "timestamp": time.time(),
        "system": platform.platform(),
        "emudeck": emudeck,
        "session": session,
        "input_backend": input_backend or "unavailable",
        "last_action": last_action,
    }
