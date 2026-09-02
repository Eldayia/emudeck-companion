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
                self.assertEqual(len(plugin.profile_store.profiles), 5)
                await plugin._unload()
            finally:
                sys.modules.pop("main", None)
                if previous is None:
                    sys.modules.pop("decky", None)
                else:
                    sys.modules["decky"] = previous


if __name__ == "__main__":
    unittest.main()
