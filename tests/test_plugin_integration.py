import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


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
                diagnostics = await plugin.get_diagnostics()
                self.assertIsNone(diagnostics["session"])
                self.assertEqual(len(plugin.profile_store.profiles), 14)
                await plugin._unload()
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
