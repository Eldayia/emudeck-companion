from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any

import decky

# Decky loads main.py through importlib without necessarily adding the plugin
# directory to sys.path. Keep the backend split into distributable root modules
# while making their imports deterministic in both developer and Store installs.
_plugin_import_root = str(Path(decky.DECKY_PLUGIN_DIR).resolve())
if _plugin_import_root not in sys.path:
    sys.path.insert(0, _plugin_import_root)

from companion_action_engine import ActionEngine
from companion_diagnostics import build_diagnostics
from companion_emudeck import detect_emudeck
from companion_esde import ESDEMetadataIndex
from companion_profiles import ProfileStore
from companion_session import SessionManager


class Plugin:
    async def _main(self) -> None:
        plugin_dir = Path(decky.DECKY_PLUGIN_DIR)
        profile_dir = plugin_dir / "emulators"
        if not profile_dir.is_dir():
            # In a source checkout profiles live under defaults/. Decky's release
            # builder copies defaults/ contents to the plugin archive root.
            profile_dir = plugin_dir / "defaults" / "emulators"
        self.profile_store = ProfileStore(profile_dir)
        self.profile_store.load()
        self.emudeck = detect_emudeck(Path(decky.DECKY_USER_HOME))
        self.metadata_index = self._build_metadata_index()
        self.session_manager = SessionManager(self.profile_store, metadata_provider=self.metadata_index.lookup)
        self.action_engine = ActionEngine(frontend_input=True)
        self.last_action: dict[str, Any] | None = None
        self.settings_path = Path(decky.DECKY_PLUGIN_SETTINGS_DIR) / "settings.json"
        self.settings = self._load_settings()
        self._lock = asyncio.Lock()
        decky.logger.info("EmuDeck Companion loaded with %d profiles", len(self.profile_store.profiles))

    def _build_metadata_index(self) -> ESDEMetadataIndex:
        value = self.emudeck
        return ESDEMetadataIndex(
            Path(value["esde_root"]) if value.get("esde_root") else None,
            Path(value["rom_root"]) if value.get("rom_root") else None,
            Path(value["root"]) if value.get("root") else None,
        )

    async def _unload(self) -> None:
        await self.action_engine.release_all()
        decky.logger.info("EmuDeck Companion unloaded")

    async def _uninstall(self) -> None:
        await self.action_engine.release_all()

    def _load_settings(self) -> dict[str, Any]:
        defaults = {
            "settings_version": 1,
            "detection_interval_ms": 1500,
            "show_platform": True,
            "show_emulator": True,
            "show_session_time": True,
            "notifications": True,
        }
        try:
            stored = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                defaults.update(stored)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            pass
        return defaults

    async def get_current_session(self) -> dict[str, Any] | None:
        async with self._lock:
            session = self.session_manager.refresh()
            return session.as_dict() if session else None

    async def get_artwork(self) -> str | None:
        async with self._lock:
            session = self.session_manager.refresh()
            artwork = session.metadata.get("image") if session else None
            if not artwork:
                return None
            path = Path(artwork)
            try:
                if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
                    return None
                mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
            except OSError:
                return None

    async def execute_action(self, action: str) -> dict[str, Any]:
        async with self._lock:
            session = self.session_manager.refresh()
            result = await self.action_engine.execute(session, action)
            self.last_action = result.as_dict()
            log = decky.logger.info if result.ok else decky.logger.warning
            log("Action %s: %s", action, result.message)
            return self.last_action

    async def refresh_detection(self) -> dict[str, Any] | None:
        async with self._lock:
            self.emudeck = detect_emudeck(Path(decky.DECKY_USER_HOME))
            self.metadata_index = self._build_metadata_index()
            self.session_manager.metadata_provider = self.metadata_index.lookup
            self.session_manager.current = None
            session = self.session_manager.refresh()
            return session.as_dict() if session else None

    async def reload_profiles(self) -> dict[str, Any]:
        async with self._lock:
            self.profile_store.load()
            self.session_manager.current = None
            return {"ok": True, "count": len(self.profile_store.profiles)}

    async def get_diagnostics(self) -> dict[str, Any]:
        async with self._lock:
            session = self.session_manager.refresh()
            backend_name = (
                "SteamClient.Input"
                if self.action_engine.frontend_input
                else self.action_engine.backend.name if self.action_engine.backend else None
            )
            return build_diagnostics(
                session.as_dict() if session else None,
                self.emudeck,
                backend_name,
                self.last_action,
            )
