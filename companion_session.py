from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterable

from companion_game_detection import extract_rom, game_name_from_rom
from companion_models import ProcessInfo, Session
from companion_process_detection import find_emulator, iter_processes
from companion_profiles import ProfileStore


class SessionManager:
    def __init__(
        self,
        profiles: ProfileStore,
        process_provider: Callable[[], Iterable[ProcessInfo]] = iter_processes,
    ) -> None:
        self.profiles = profiles
        self.process_provider = process_provider
        self.current: Session | None = None

    def refresh(self) -> Session | None:
        detected = find_emulator(self.profiles.profiles, self.process_provider())
        if detected is None:
            self.current = None
            return None
        profile, process = detected
        if self.current is not None and self.current.pid == process.pid:
            return self.current
        rom = extract_rom(process.argv, profile)
        self.current = Session(
            emulator=profile["id"],
            emulator_name=profile["name"],
            pid=process.pid,
            argv=list(process.argv),
            rom=rom,
            game=game_name_from_rom(rom),
            platform=profile.get("platform"),
            capabilities=list(profile["capabilities"]),
            actions=dict(profile["actions"]),
            started_at=time.time(),
            slot=int(profile.get("default_slot", 0)),
        )
        return self.current

    def as_dict(self) -> dict | None:
        return self.current.as_dict() if self.current else None
