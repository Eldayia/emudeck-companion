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
from companion_action_history import ActionHistory
from companion_diagnostics import build_diagnostics
from companion_document_server import DocumentServer
from companion_documents import DocumentIndex
from companion_emudeck import detect_emudeck
from companion_esde import ESDEMetadataIndex
from companion_esde_hooks import read_status as esde_hook_status
from companion_game_overrides import hidden_actions, session_payload
from companion_hotkey_config import DuckStationHotkeyConfig
from companion_models import ActionResult, ProcessInfo
from companion_profiles import ProfileStore
from companion_retroarch_config import RetroArchHotkeyConfig
from companion_retroarch_commands import RetroArchCommands, settings_actions
from companion_retroarch_setup import configure_network
from companion_process_detection import iter_processes, find_emulator
from companion_savestates import SavestateIndex
from companion_session import SessionManager


class Plugin:
    async def _main(self) -> None:
        plugin_dir = Path(decky.DECKY_PLUGIN_DIR)
        try:
            version = json.loads((plugin_dir / "package.json").read_text(encoding="utf-8")).get("version")
            self.plugin_version = version[:80] if isinstance(version, str) else "unknown"
        except (OSError, ValueError, AttributeError):
            self.plugin_version = "unknown"
        profile_dir = plugin_dir / "emulators"
        if not profile_dir.is_dir():
            # In a source checkout profiles live under defaults/. Decky's release
            # builder copies defaults/ contents to the plugin archive root.
            profile_dir = plugin_dir / "defaults" / "emulators"
        self.profile_store = ProfileStore(profile_dir)
        self.profile_store.load()
        self.emudeck = detect_emudeck(Path(decky.DECKY_USER_HOME))
        self.metadata_index = self._build_metadata_index()
        self.savestate_index = self._build_savestate_index()
        self.document_index = self._build_document_index()
        self.document_server = DocumentServer()
        self.document_server.start()
        decky.logger.info(
            "Document server started on localhost:%s",
            self.document_server.diagnostics()["port"],
        )
        self.retroarch_commands = RetroArchCommands()
        self.hotkey_readers = (
            DuckStationHotkeyConfig(Path(decky.DECKY_USER_HOME)),
            RetroArchHotkeyConfig(Path(decky.DECKY_USER_HOME)),
        )
        self.session_manager = SessionManager(
            self.profile_store,
            metadata_provider=self.metadata_index.lookup,
            savestate_provider=self.savestate_index.lookup,
            document_provider=self.document_index.lookup,
            profile_provider=self._resolve_hotkey_profile,
        )
        self.action_engine = ActionEngine(frontend_input=True, native_commands=self.retroarch_commands)
        self.action_history = ActionHistory()
        self.settings_path = Path(decky.DECKY_PLUGIN_SETTINGS_DIR) / "settings.json"
        self.settings = self._load_settings()
        self._lock = asyncio.Lock()
        decky.logger.info("EmuDeck Companion %s loaded with %d profiles", self.plugin_version, len(self.profile_store.profiles))

    def _resolve_hotkey_profile(self, profile: dict[str, Any], process: ProcessInfo) -> dict[str, Any]:
        original = profile
        for reader in self.hotkey_readers:
            profile = reader(profile, process)
        return self.retroarch_commands.apply(original, profile, process)

    async def configure_retroarch_network(self, enabled: bool) -> dict[str, Any]:
        async with self._lock:
            profiles = [p for p in self.profile_store.profiles if p.get("hotkey_config_format") == "retroarch"]
            if find_emulator(profiles, iter_processes()) is not None:
                return {"ok": False, "message": "Close RetroArch completely before changing this setting"}
            try:
                result = await asyncio.to_thread(
                    configure_network, Path(decky.DECKY_USER_HOME),
                    self.settings_path.parent / "retroarch-backups", enabled,
                )
            except (OSError, ValueError) as error:
                return {"ok": False, "message": str(error)}
            decky.logger.info("RetroArch network setup: %s; backup: %s", result["message"], result.get("backup", "unchanged"))
            return result

    def _build_metadata_index(self) -> ESDEMetadataIndex:
        value = self.emudeck
        return ESDEMetadataIndex(
            Path(value["esde_root"]) if value.get("esde_root") else None,
            Path(value["rom_root"]) if value.get("rom_root") else None,
            Path(value["root"]) if value.get("root") else None,
        )

    def _build_savestate_index(self) -> SavestateIndex:
        root = self.emudeck.get("root")
        return SavestateIndex(Path(root) if root else None)

    def _build_document_index(self) -> DocumentIndex:
        root = self.emudeck.get("root")
        rom_root = self.emudeck.get("rom_root")
        return DocumentIndex(Path(root) if root else None, Path(rom_root) if rom_root else None)

    async def _unload(self) -> None:
        await self.action_engine.release_all()
        await asyncio.to_thread(self.document_server.stop)
        decky.logger.info("EmuDeck Companion unloaded")

    async def _uninstall(self) -> None:
        await self.action_engine.release_all()
        await asyncio.to_thread(self.document_server.stop)

    def _load_settings(self) -> dict[str, Any]:
        defaults = {
            "settings_version": 2,
            "compact_actions": False,
            "detection_interval_ms": 1500,
            "show_platform": True,
            "show_emulator": True,
            "show_session_time": True,
            "notifications": True,
            "favorites": {},
            "game_overrides": {},
        }
        try:
            stored = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                defaults.update(stored)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            pass
        return self._validated_settings(defaults)

    def _validated_settings(self, value: dict[str, Any]) -> dict[str, Any]:
        interval = value.get("detection_interval_ms", 1500)
        if not isinstance(interval, int) or isinstance(interval, bool):
            interval = 1500
        favorites: dict[str, list[str]] = {}
        raw_favorites = value.get("favorites", {})
        if isinstance(raw_favorites, dict):
            for profile_id, actions in raw_favorites.items():
                profile = self.profile_store.get(str(profile_id))
                if profile is None or not isinstance(actions, list):
                    continue
                allowed = settings_actions(profile)
                selected: list[str] = []
                for action in actions:
                    if isinstance(action, str) and action in allowed and action not in selected:
                        selected.append(action)
                if selected:
                    favorites[profile["id"]] = selected[:4]
        game_overrides: dict[str, dict[str, list[str]]] = {}
        raw_overrides = value.get("game_overrides", {})
        if isinstance(raw_overrides, dict):
            for key, override in list(raw_overrides.items())[:256]:
                if not isinstance(key, str) or ":" not in key or not isinstance(override, dict):
                    continue
                profile = self.profile_store.get(key.split(":", 1)[0])
                if profile is None:
                    continue
                allowed = settings_actions(profile)
                normalized: dict[str, list[str]] = {}
                raw_hidden = override.get("hidden_actions", [])
                hidden: list[str] = []
                if isinstance(raw_hidden, list):
                    for action in raw_hidden:
                        if (
                            isinstance(action, str)
                            and action in allowed
                            and action not in hidden
                        ):
                            hidden.append(action)
                if hidden:
                    normalized["hidden_actions"] = hidden
                raw_game_favorites = override.get("favorites")
                if isinstance(raw_game_favorites, list):
                    selected: list[str] = []
                    for action in raw_game_favorites:
                        if (
                            isinstance(action, str)
                            and action in allowed
                            and action not in hidden
                            and action not in selected
                        ):
                            selected.append(action)
                    normalized["favorites"] = selected[:4]
                if normalized:
                    game_overrides[key] = normalized
        return {
            "settings_version": 2,
            "compact_actions": value.get("compact_actions") is True,
            "detection_interval_ms": min(5000, max(1000, interval)),
            "show_platform": value.get("show_platform") is not False,
            "show_emulator": value.get("show_emulator") is not False,
            "show_session_time": value.get("show_session_time") is not False,
            "notifications": value.get("notifications") is not False,
            "favorites": favorites,
            "game_overrides": game_overrides,
        }

    def _save_settings(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.settings_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.settings, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.settings_path)

    async def get_settings(self) -> dict[str, Any]:
        async with self._lock:
            return json.loads(json.dumps(self.settings))

    async def update_settings(self, changes: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            if not isinstance(changes, dict):
                raise ValueError("Settings update must be an object")
            merged = dict(self.settings)
            merged.update(changes)
            self.settings = self._validated_settings(merged)
            self._save_settings()
            return json.loads(json.dumps(self.settings))

    async def get_current_session(self) -> dict[str, Any] | None:
        async with self._lock:
            session = self.session_manager.refresh()
            return session_payload(session, self.settings) if session else None

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

    async def get_document_url(self, document_id: str) -> str | None:
        async with self._lock:
            session = self.session_manager.refresh()
            if session is None:
                return None
            document = next(
                (item for item in session.documents if item.get("id") == document_id),
                None,
            )
            if document is None:
                return None
            return self.document_server.url_for(Path(document["path"]))

    async def execute_action(self, action: str, session_id: str | None = None) -> dict[str, Any]:
        async with self._lock:
            session = self.session_manager.refresh()
            if session is not None and session_id != session.session_id:
                result = ActionResult(False, action, "Session changed or missing; refresh Companion before sending this action")
            elif session is not None and action in hidden_actions(session, self.settings):
                result = ActionResult(False, action, "Action hidden by this game's settings")
            else:
                result = await self.action_engine.execute(session, action)
            payload = self.action_history.record(result, session)
            log = decky.logger.info if result.ok else decky.logger.warning
            log("Action %s [%s; %s]: %s", action, payload["request_id"], result.dispatch, result.message)
            return payload

    async def report_keyboard_delivery(self, request_id: str, delivered: bool, error: str = "") -> dict[str, bool]:
        async with self._lock:
            accepted = self.action_history.report_keyboard(request_id, delivered, error)
            if accepted:
                log = decky.logger.info if delivered else decky.logger.warning
                log("Keyboard dispatch %s: %s", request_id, "sent (execution unconfirmed)" if delivered else error[:250])
            return {"ok": accepted}

    async def refresh_detection(self) -> dict[str, Any] | None:
        async with self._lock:
            self.emudeck = detect_emudeck(Path(decky.DECKY_USER_HOME))
            self.metadata_index = self._build_metadata_index()
            self.savestate_index = self._build_savestate_index()
            self.document_index = self._build_document_index()
            self.session_manager.metadata_provider = self.metadata_index.lookup
            self.session_manager.savestate_provider = self.savestate_index.lookup
            self.session_manager.document_provider = self.document_index.lookup
            self.session_manager.current = None
            session = self.session_manager.refresh()
            return session_payload(session, self.settings) if session else None

    async def reload_profiles(self) -> dict[str, Any]:
        async with self._lock:
            self.profile_store.load()
            self.session_manager.current = None
            return {"ok": True, "count": len(self.profile_store.profiles)}

    def _build_diagnostics(self) -> dict[str, Any]:
        session = self.session_manager.refresh()
        history = self.action_history.snapshot()
        backend_name = (
            "SteamClient.Input"
            if self.action_engine.frontend_input
            else self.action_engine.backend.name if self.action_engine.backend else None
        )
        if session and any(a.get("method") == "retroarch_udp" for a in session.actions.values()):
            backend_name = "RetroArch native commands (UDP loopback)"
        diagnostics = build_diagnostics(
            session_payload(session, self.settings) if session else None,
            self.emudeck,
            backend_name,
            history["last_action"],
        )
        diagnostics["document_server"] = self.document_server.diagnostics()
        diagnostics["plugin_version"] = self.plugin_version
        diagnostics["action_history"] = history["action_history"]
        esde_root = self.emudeck.get("esde_root")
        diagnostics["esde_hooks"] = esde_hook_status(
            Path(esde_root) if esde_root else None, session.rom if session else None,
        )
        return diagnostics

    async def get_diagnostics(self) -> dict[str, Any]:
        async with self._lock:
            return self._build_diagnostics()

    async def export_diagnostics(self) -> dict[str, Any]:
        async with self._lock:
            diagnostics = self._build_diagnostics()
            destination = self.settings_path.parent / "diagnostics.json"
            temporary = destination.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            temporary.replace(destination)
            decky.logger.info("Diagnostics exported to %s", destination)
            return {"ok": True, "path": str(destination)}
