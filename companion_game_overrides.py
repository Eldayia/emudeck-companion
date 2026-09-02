from __future__ import annotations

from typing import Any

from companion_models import Session


def game_override_key(session: Session) -> str | None:
    if not session.rom:
        return None
    normalized_rom = session.rom.replace("\\", "/")
    return f"{session.emulator}:{normalized_rom}"


def hidden_actions(session: Session, settings: dict[str, Any]) -> set[str]:
    key = game_override_key(session)
    if key is None:
        return set()
    override = settings.get("game_overrides", {}).get(key, {})
    actions = override.get("hidden_actions", []) if isinstance(override, dict) else []
    return {action for action in actions if isinstance(action, str)}


def session_payload(session: Session, settings: dict[str, Any]) -> dict[str, Any]:
    payload = session.as_dict()
    available = list(session.capabilities)
    hidden = hidden_actions(session, settings)
    payload["game_key"] = game_override_key(session)
    payload["available_capabilities"] = available
    payload["capabilities"] = [action for action in available if action not in hidden]
    return payload
