from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProfileError(RuntimeError):
    pass


class ProfileStore:
    def __init__(self, profile_dir: Path) -> None:
        self.profile_dir = profile_dir
        self._profiles: dict[str, dict[str, Any]] = {}

    def load(self) -> None:
        loaded: dict[str, dict[str, Any]] = {}
        for path in sorted(self.profile_dir.glob("*.json")):
            try:
                profile = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ProfileError(f"Cannot load {path.name}: {error}") from error
            self._validate(profile, path)
            loaded[profile["id"]] = profile
        if not loaded:
            raise ProfileError(f"No emulator profile found in {self.profile_dir}")
        self._profiles = loaded

    @staticmethod
    def _validate(profile: dict[str, Any], path: Path) -> None:
        required = {"id", "name", "profile_version", "processes", "capabilities", "actions"}
        missing = required.difference(profile)
        if missing:
            raise ProfileError(f"{path.name} is missing: {', '.join(sorted(missing))}")
        if not isinstance(profile["processes"], list) or not profile["processes"]:
            raise ProfileError(f"{path.name} must declare at least one process")
        unknown = set(profile["actions"]).difference(profile["capabilities"])
        if unknown:
            raise ProfileError(f"{path.name} actions lack capabilities: {', '.join(sorted(unknown))}")

    @property
    def profiles(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._profiles.values())

    def get(self, profile_id: str) -> dict[str, Any] | None:
        return self._profiles.get(profile_id)
