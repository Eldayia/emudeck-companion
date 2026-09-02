from __future__ import annotations

import time
from pathlib import PurePosixPath
from typing import Any, Callable, Iterable

from companion_game_detection import extract_rom, game_name_from_rom
from companion_models import ProcessInfo, Session
from companion_multidisc import playlist_discs
from companion_process_detection import find_emulator, iter_processes
from companion_profiles import ProfileStore


def contextual_capabilities(profile: dict[str, Any], rom: str | None) -> list[str]:
    capabilities = list(profile["capabilities"])
    if not rom:
        return capabilities
    path_parts = {
        part.casefold()
        for part in PurePosixPath(rom.replace("\\", "/")).parts
        if part not in {"/", "\\"}
    }
    for rule in profile.get("capability_rules", []):
        matching_parts = {str(part).casefold() for part in rule.get("rom_path_segments", [])}
        if path_parts.intersection(matching_parts):
            removed = set(rule.get("remove", []))
            capabilities = [action for action in capabilities if action not in removed]
    return capabilities


class SessionManager:
    def __init__(
        self,
        profiles: ProfileStore,
        process_provider: Callable[[], Iterable[ProcessInfo]] = iter_processes,
        metadata_provider: Callable[[str | None], dict[str, Any]] | None = None,
        savestate_provider: Callable[[dict[str, Any], str | None], list[dict[str, Any]]] | None = None,
        document_provider: Callable[[str | None, dict[str, Any]], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.profiles = profiles
        self.process_provider = process_provider
        self.metadata_provider = metadata_provider
        self.savestate_provider = savestate_provider
        self.document_provider = document_provider
        self.current: Session | None = None

    def refresh(self) -> Session | None:
        detected = find_emulator(self.profiles.profiles, self.process_provider())
        if detected is None:
            self.current = None
            return None
        profile, process = detected
        if self.current is not None and self.current.pid == process.pid:
            if self.savestate_provider:
                self.current.savestates = self.savestate_provider(profile, self.current.rom)
            if self.document_provider:
                self.current.documents = self.document_provider(
                    self.current.rom, self.current.metadata
                )
            return self.current
        rom = extract_rom(process.argv, profile)
        discs = playlist_discs(rom)
        metadata = self.metadata_provider(rom) if self.metadata_provider else {}
        capabilities = contextual_capabilities(profile, rom)
        if len(discs) <= 1:
            capabilities = [action for action in capabilities if action not in {"previous_disc", "next_disc"}]
        self.current = Session(
            emulator=profile["id"],
            emulator_name=profile["name"],
            pid=process.pid,
            argv=list(process.argv),
            rom=rom,
            game=metadata.get("name") or game_name_from_rom(rom, profile),
            platform=profile.get("platform"),
            capabilities=capabilities,
            actions=dict(profile["actions"]),
            started_at=time.time(),
            slot=int(profile.get("default_slot", 0)),
            metadata=metadata,
            discs=discs,
            current_disc=1 if discs else None,
            savestates=self.savestate_provider(profile, rom) if self.savestate_provider else [],
            documents=self.document_provider(rom, metadata) if self.document_provider else [],
        )
        return self.current

    def as_dict(self) -> dict | None:
        return self.current.as_dict() if self.current else None
