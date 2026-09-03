import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from companion_models import ProcessInfo, Session


ROOT = Path(__file__).resolve().parents[1]


class PluginIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_plugin_starts_from_source_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_decky = types.SimpleNamespace(
                DECKY_PLUGIN_DIR=str(ROOT),
                DECKY_USER_HOME=directory,
                DECKY_PLUGIN_SETTINGS_DIR=directory,
                logger=Mock(),
            )
            previous = sys.modules.get("decky")
            sys.modules["decky"] = fake_decky
            sys.modules.pop("main", None)
            try:
                plugin_module = importlib.import_module("main")
                plugin = plugin_module.Plugin()
                await plugin._main()
                self.assertFalse((await plugin.get_settings())["compact_actions"])
                diagnostics = await plugin.get_diagnostics()
                self.assertIsNone(diagnostics["session"])
                self.assertEqual(diagnostics["esde_hooks"]["status"], "not_installed")
                from companion_esde_hooks import manage, record_event
                esde_root = Path(directory) / "ES-DE"
                esde_root.mkdir()
                (esde_root / "es_settings.xml").write_text("<config/>")
                manage(esde_root, "install")
                await plugin.refresh_detection()
                with patch("companion_esde_hooks.boot_id", return_value="integration-boot"):
                    record_event(esde_root, "game-start", [str(esde_root / "game.n64"), "Test game", "n64", "Nintendo 64"])
                    received = await plugin.get_diagnostics()
                    self.assertIsNone(received["session"])
                    self.assertEqual(received["esde_hooks"]["last_event"]["game"], "Test game")
                    self.assertIn("hook event received this boot", received["esde_hooks"]["activation"])
                    self.assertEqual(received["esde_hooks"]["activation_config"]["status"], "unknown")
                    hook_export = await plugin.export_diagnostics()
                    exported_hooks = json.loads(Path(hook_export["path"]).read_text())["esde_hooks"]
                    self.assertEqual(exported_hooks, received["esde_hooks"])
                self.assertTrue(diagnostics["document_server"]["running"])
                self.assertIsInstance(diagnostics["document_server"]["port"], int)
                self.assertEqual(len(plugin.profile_store.profiles), 14)
                resolved = plugin._resolve_hotkey_profile(
                    plugin.profile_store.get("retroarch"),
                    ProcessInfo(999999, "retroarch", ("retroarch",)),
                )
                self.assertEqual(resolved["hotkey_config"]["status"], "fallback")
                self.assertNotIn("rewind", resolved["capabilities"])
                settings = await plugin.update_settings({
                    "notifications": False,
                    "detection_interval_ms": 100,
                    "favorites": {
                        "cemu": ["pause", "invalid", "pause", "swap_screen", "fullscreen", "quit"],
                        "unknown": ["quit"],
                    },
                    "game_overrides": {
                        "duckstation:/roms/Silent Hill.chd": {
                            "hidden_actions": ["fast_forward", "invalid", "fast_forward"],
                            "favorites": ["save_state", "invalid", "save_state", "fast_forward", "quit", "load_state", "pause"],
                        },
                        "duckstation:/roms/No Favorites.chd": {"favorites": []},
                        "unknown:/roms/game.iso": {"hidden_actions": ["quit"]},
                    },
                })
                self.assertFalse(settings["notifications"])
                self.assertEqual(settings["detection_interval_ms"], 1000)
                self.assertEqual(
                    settings["favorites"],
                    {"cemu": ["pause", "swap_screen", "fullscreen", "quit"]},
                )
                self.assertEqual(settings["settings_version"], 2)
                self.assertEqual(
                    settings["game_overrides"],
                    {
                        "duckstation:/roms/Silent Hill.chd": {
                            "hidden_actions": ["fast_forward"],
                            "favorites": ["save_state", "quit", "load_state", "pause"],
                        },
                        "duckstation:/roms/No Favorites.chd": {"favorites": []},
                    },
                )
                plugin.session_manager.refresh = Mock(return_value=Session(
                    emulator="duckstation",
                    emulator_name="DuckStation",
                    pid=42,
                    argv=["duckstation", "/roms/Silent Hill.chd"],
                    rom="/roms/Silent Hill.chd",
                    game="Silent Hill",
                    platform="PlayStation",
                    capabilities=["fast_forward", "quit"],
                    actions={"fast_forward": {"label": "Fast Forward", "method": "hotkey", "keys": ["tab"]}},
                    started_at=1.0,
                ))
                active_id = plugin.session_manager.refresh().session_id
                with patch.object(plugin.action_engine, "execute") as dispatch:
                    for stale_id in (None, "old-session"):
                        rejected = await plugin.execute_action("fast_forward", stale_id)
                        self.assertFalse(rejected["ok"])
                        self.assertIn("Session changed", rejected["message"])
                    dispatch.assert_not_called()
                hidden_result = await plugin.execute_action("fast_forward", active_id)
                self.assertFalse(hidden_result["ok"])
                self.assertEqual(hidden_result["message"], "Action hidden by this game's settings")
                persisted = json.loads(Path(directory, "settings.json").read_text(encoding="utf-8"))
                self.assertEqual(persisted, settings)
                exported = await plugin.export_diagnostics()
                self.assertTrue(exported["ok"])
                export_path = Path(exported["path"])
                self.assertEqual(export_path, Path(directory, "diagnostics.json"))
                report = json.loads(export_path.read_text(encoding="utf-8"))
                self.assertEqual(report["input_backend"], "SteamClient.Input")
                self.assertTrue(report["document_server"]["running"])
                self.assertFalse(Path(directory, "diagnostics.tmp").exists())
                self.assertEqual(report["plugin_version"], json.loads((ROOT / "package.json").read_text())["version"])
                self.assertEqual(report["action_history"][0]["status"], "failed")
                self.assertEqual(report["action_history"][0]["id"], hidden_result["request_id"])
                await plugin.update_settings({"game_overrides": {}})
                keyboard_result = await plugin.execute_action("fast_forward", active_id)
                self.assertEqual((await plugin.get_diagnostics())["action_history"][0]["status"], "pending")
                self.assertTrue((await plugin.report_keyboard_delivery(keyboard_result["request_id"], False, "test dispatch error"))["ok"])
                self.assertFalse((await plugin.get_diagnostics())["last_action"]["ok"])
                self.assertFalse((await plugin.report_keyboard_delivery(keyboard_result["request_id"], True))["ok"])
                await plugin.update_settings({"game_overrides": settings["game_overrides"]})
                compact = await plugin.update_settings({"compact_actions": True})
                self.assertTrue(compact["compact_actions"])
                self.assertTrue(plugin._load_settings()["compact_actions"])
                self.assertEqual(compact["favorites"], settings["favorites"])
                self.assertEqual(compact["game_overrides"], settings["game_overrides"])
                for invalid_compact in ("true", "false", 1, None, [], {}):
                    self.assertFalse(plugin._validated_settings({"compact_actions": invalid_compact})["compact_actions"])
                self.assertFalse((await plugin.update_settings({"compact_actions": False}))["compact_actions"])
                native_settings = await plugin.update_settings({
                    "favorites": {"retroarch": ["emulator_menu", "menu_confirm", "invalid"]},
                    "game_overrides": {"retroarch:game.n64": {
                        "hidden_actions": ["menu_up", "invalid"], "favorites": ["menu_back", "invalid"],
                    }},
                })
                self.assertEqual(native_settings["favorites"]["retroarch"], ["emulator_menu", "menu_confirm"])
                self.assertEqual(native_settings["game_overrides"]["retroarch:game.n64"], {
                    "hidden_actions": ["menu_up"], "favorites": ["menu_back"],
                })
                with patch.object(plugin_module, "iter_processes", return_value=iter([ProcessInfo(42, "retroarch", ("retroarch",))])), \
                     patch.object(plugin_module, "configure_network") as configure:
                    response = await plugin.configure_retroarch_network(True)
                    self.assertFalse(response["ok"])
                    self.assertIn("Close RetroArch", response["message"])
                    configure.assert_not_called()
                with patch.object(plugin_module, "iter_processes", return_value=iter([])), \
                     patch.object(plugin_module, "configure_network", return_value={"ok": True, "message": "Enabled"}) as configure:
                    response = await plugin.configure_retroarch_network(True)
                    self.assertTrue(response["ok"])
                    configure.assert_called_once_with(Path(directory), Path(directory) / "retroarch-backups", True)
                await plugin._unload()
                self.assertFalse(plugin.document_server.diagnostics()["running"])
            finally:
                sys.modules.pop("main", None)
                if previous is None:
                    sys.modules.pop("decky", None)
                else:
                    sys.modules["decky"] = previous

    async def test_main_bootstraps_plugin_import_path(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_decky = types.SimpleNamespace(
                DECKY_PLUGIN_DIR=str(ROOT),
                DECKY_USER_HOME=directory,
                DECKY_PLUGIN_SETTINGS_DIR=directory,
                logger=Mock(),
            )
            previous_decky = sys.modules.get("decky")
            original_path = list(sys.path)
            sys.modules["decky"] = fake_decky
            sys.modules.pop("main", None)
            sys.path = [entry for entry in sys.path if Path(entry or ".").resolve() != ROOT]
            try:
                spec = importlib.util.spec_from_file_location("main", ROOT / "main.py")
                assert spec is not None and spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                sys.modules["main"] = module
                spec.loader.exec_module(module)
                self.assertEqual(Path(sys.path[0]), ROOT)
                plugin = module.Plugin()
                await plugin._main()
                self.assertEqual(len(plugin.profile_store.profiles), 14)
                await plugin._unload()
            finally:
                sys.path = original_path
                sys.modules.pop("main", None)
                if previous_decky is None:
                    sys.modules.pop("decky", None)
                else:
                    sys.modules["decky"] = previous_decky


if __name__ == "__main__":
    unittest.main()
