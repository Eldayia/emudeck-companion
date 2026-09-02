from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    name: str
    argv: tuple[str, ...]
    started_ticks: int | None = None


@dataclass
class Session:
    emulator: str
    emulator_name: str
    pid: int
    argv: list[str]
    rom: str | None
    game: str | None
    platform: str | None
    capabilities: list[str]
    actions: dict[str, dict[str, Any]]
    started_at: float
    slot: int = 0
    toggles: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    discs: list[str] = field(default_factory=list)
    current_disc: int | None = None
    savestates: list[dict[str, Any]] = field(default_factory=list)
    documents: list[dict[str, Any]] = field(default_factory=list)
    hotkey_config: dict[str, Any] = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: uuid4().hex)
    process_started_ticks: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionResult:
    ok: bool
    action: str
    message: str
    slot: int | None = None
    active: bool | None = None
    keys: list[str] | None = None
    dispatch: str = "none"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
