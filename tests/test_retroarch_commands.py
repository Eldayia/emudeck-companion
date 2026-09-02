import asyncio
import socket
import tempfile
import threading
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch

from companion_action_engine import ActionEngine
from companion_models import ProcessInfo, Session
from companion_profiles import ProfileStore
from companion_retroarch_commands import COMMANDS, RetroArchCommands, owned_endpoint, udp_owner
from companion_retroarch_config import HOTKEY_SETTINGS, RetroArchHotkeyConfig
from companion_session import SessionManager


ROOT = Path(__file__).resolve().parents[1]


def udp_table(address="00000000", port=55355, inode="123", remote="00000000:0000"):
    return ("sl local_address rem_address st tx_queue rx_queue tr tm retr uid timeout inode\n"
            f"0: {address}:{port:04X} {remote} 07 00000000:00000000 00:00000000 00000000 1000 0 {inode} 2\n")


def connection(*replies):
    result = Mock()
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    result.recv.side_effect = list(replies or (b"1.19.1\n", b"GET_STATUS PLAYING n64,Game,crc32=12345678\n"))
    return result


class EndpointTests(unittest.TestCase):
    def test_exclusive_ipv4_local_and_wildcard_listeners(self):
        for address in ("00000000", "0100007F"):
            self.assertEqual(udp_owner(udp_table(address), {"123"}, 55355), "123")

    def test_rejects_wrong_owner_nonlocal_connected_or_shared_port(self):
        for table, inodes in (
            (udp_table(), {"other"}),
            (udp_table("0101A8C0"), {"123"}),
            (udp_table(remote="0100007F:DEAD"), {"123"}),
            (udp_table() + udp_table().splitlines()[1] + "\n", {"123"}),
            (udp_table(port=55356), {"123"}),
            ("header\ninvalid\n0: BAD:PORT no\n", {"123"}),
        ):
            self.assertIsNone(udp_owner(table, inodes, 55355))

    def test_proc_reader_verifies_namespace_and_socket_fds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "42/fd").mkdir(parents=True)
            (root / "42/net").mkdir()
            (root / "42/fd/3").touch()
            (root / "42/net/udp").write_text(udp_table(), encoding="ascii")
            links = {
                root / "42/ns/net": Path("net:[100]"),
                root / "self/ns/net": Path("net:[100]"),
                root / "42/fd/3": Path("socket:[123]"),
            }
            with patch.object(Path, "readlink", lambda path: links[path]):
                self.assertEqual(owned_endpoint(42, 55355, root), "123")
                links[root / "42/ns/net"] = Path("net:[200]")
                self.assertIsNone(owned_endpoint(42, 55355, root))
            with patch.object(Path, "readlink", side_effect=PermissionError()):
                self.assertIsNone(owned_endpoint(42, 55355, root))


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.owner = Mock(return_value="123")
        self.backend = RetroArchCommands(owner=self.owner)

    def session(self, action="save_state"):
        return Session("retroarch", "RetroArch", 42, [], None, None, None, [action], {
            action: {"method": "retroarch_udp", "command": COMMANDS[action],
                     "command_port": 55355, "command_inode": "123"},
        }, 0)

    def test_socket_connects_only_to_loopback(self):
        with patch("companion_retroarch_commands.socket.socket") as factory:
            self.backend._socket(55355)
            factory.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
            factory.return_value.connect.assert_called_once_with(("127.0.0.1", 55355))

    def test_loopback_protocol_integration_with_fake_retroarch(self):
        received = []
        stopped = threading.Event()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(("127.0.0.1", 0))
            server.settimeout(0.1)
            port = server.getsockname()[1]

            def serve():
                while not stopped.is_set():
                    try:
                        data, address = server.recvfrom(1024)
                    except socket.timeout:
                        continue
                    received.append(data)
                    if data == b"VERSION\n":
                        server.sendto(b"1.19.1\n", address)
                    elif data == b"GET_STATUS\n":
                        server.sendto(b"GET_STATUS CONTENTLESS\n", address)
                    else:
                        stopped.set()

            worker = threading.Thread(target=serve, daemon=True)
            worker.start()
            try:
                backend = RetroArchCommands(owner=self.owner, timeout=0.5)
                session = self.session("pause")
                session.actions["pause"]["command_port"] = port
                backend.execute(session, "pause")
                self.assertTrue(stopped.wait(1))
                self.assertEqual(received, [b"VERSION\n", b"GET_STATUS\n", b"PAUSE_TOGGLE\n"])
            finally:
                stopped.set()
                worker.join(1)

    def test_validates_version_status_and_caches_only_same_owned_endpoint(self):
        conn = connection()
        with patch.object(self.backend, "_socket", return_value=conn) as factory:
            self.assertEqual(self.backend.inspect(42, 55355)["status"], "ready")
            self.assertEqual(self.backend.inspect(42, 55355)["version"], "1.19.1")
            factory.assert_called_once_with(55355)
            self.assertEqual([call.args[0] for call in conn.send.call_args_list], [b"VERSION\n", b"GET_STATUS\n"])
            self.owner.return_value = None
            self.assertEqual(self.backend.inspect(42, 55355)["status"], "unavailable")

    def test_invalid_ports_and_unowned_endpoint_never_open_socket(self):
        with patch.object(self.backend, "_socket") as factory:
            for port in (0, -1, 65536, "55355", True, None):
                self.assertEqual(self.backend.inspect(42, port)["status"], "unavailable")
            self.owner.return_value = None
            self.backend.inspect(42, 55355)
            factory.assert_not_called()

    def test_rejects_bad_old_timed_out_or_malformed_replies(self):
        for replies in ((b"not RetroArch",), (b"1.18.0",), (b"1.19.1", b"unexpected"),
                        (b"1.19.1", b"\xff"), (socket.timeout(),)):
            with self.subTest(replies=replies), patch.object(self.backend, "_socket", return_value=connection(*replies)):
                self.assertEqual(self.backend.inspect(42, 55355, force=True)["status"], "unavailable")

    def test_accepts_paused_and_contentless_replies(self):
        for reply in (b"GET_STATUS PAUSED n64,Game,crc32=12345678", b"GET_STATUS CONTENTLESS"):
            with patch.object(self.backend, "_socket", return_value=connection(b"1.20.0", reply)):
                self.assertEqual(self.backend.inspect(42, 55355, force=True)["status"], "ready")

    def test_changed_socket_during_probe_is_rejected(self):
        self.owner.side_effect = ["123", "456"]
        with patch.object(self.backend, "_socket", return_value=connection()):
            self.assertEqual(self.backend.inspect(42, 55355)["status"], "unavailable")

    def test_each_allowlisted_action_is_sent_once_after_fresh_probe(self):
        for action, command in COMMANDS.items():
            with self.subTest(action=action):
                probe, send = connection(), connection()
                with patch.object(self.backend, "_socket", side_effect=[probe, send]):
                    self.backend.execute(self.session(action), action)
                send.send.assert_called_once_with((command + "\n").encode("ascii"))
                self.assertEqual(self.backend._cache, {})

    def test_send_failure_is_not_retried(self):
        send = connection()
        send.send.side_effect = OSError("uncertain send")
        with patch.object(self.backend, "_socket", side_effect=[connection(), send]) as factory:
            with self.assertRaises(OSError):
                self.backend.execute(self.session(), "save_state")
            self.assertEqual(factory.call_count, 2)
        self.assertEqual(send.send.call_count, 1)

    def test_changed_inode_before_dispatch_and_arbitrary_commands_are_rejected(self):
        for mutate in (lambda s: s.actions["save_state"].update(command_inode="old"),
                       lambda s: s.actions["save_state"].update(command="QUIT\nSAVE_STATE"),
                       lambda s: setattr(s, "emulator", "cemu")):
            session = self.session()
            mutate(session)
            with patch.object(self.backend, "_socket", return_value=connection()) as factory:
                with self.assertRaises(ValueError):
                    self.backend.execute(session, "save_state")
                self.assertLessEqual(factory.call_count, 1)
        self.owner.side_effect = ["123", "123", "456"]
        send = connection()
        with patch.object(self.backend, "_socket", side_effect=[connection(), send]):
            with self.assertRaises(ValueError):
                self.backend.execute(self.session(), "save_state")
        send.send.assert_not_called()

    def test_engine_never_uses_keyboard_fallback_or_reports_confirmed_execution(self):
        native = Mock()
        engine = ActionEngine(frontend_input=True, native_commands=native, debounce_ms=0)
        result = asyncio.run(engine.execute(self.session(), "save_state"))
        self.assertTrue(result.ok)
        self.assertEqual(result.dispatch, "retroarch_udp")
        self.assertIsNone(result.keys)
        self.assertIn("execution not confirmed", result.message)
        native.execute.side_effect = OSError("unavailable")
        result = asyncio.run(engine.execute(self.session(), "save_state"))
        self.assertFalse(result.ok)
        self.assertEqual(result.dispatch, "none")
        self.assertIsNone(result.keys)

    def test_nul_bindings_restored_only_when_native_is_ready_without_file_writes(self):
        store = ProfileStore(ROOT / "defaults/emulators")
        store.load()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / ".config/retroarch/retroarch.cfg"
            path.parent.mkdir(parents=True)
            text = "\n".join(f'{setting} = "nul"' for setting in HOTKEY_SETTINGS.values())
            path.write_text(text, encoding="utf-8")
            reader = RetroArchHotkeyConfig(home, home / "proc")
            for profile_id in ("retroarch", "fbneo"):
                original = store.get(profile_id)
                process = ProcessInfo(42, "retroarch", ("retroarch", "/roms/n64/game.n64"))
                effective = reader(original, process)
                snapshot = deepcopy(effective)
                self.assertEqual(effective["capabilities"], [])
                with patch.object(self.backend, "inspect", return_value={"status": "ready", "port": 55355, "inode": "123"}):
                    result = self.backend.apply(original, effective, process)
                for action in set(original["capabilities"]) - {"rewind"}:
                    self.assertIn(action, result["capabilities"])
                    self.assertEqual(result["actions"][action]["method"], "retroarch_udp")
                    self.assertNotIn("keys", result["actions"][action])
                    self.assertNotIn("mode", result["actions"][action])
                self.assertIn("menu_confirm", result["capabilities"])
                self.assertNotIn("rewind", result["capabilities"])
                self.assertEqual(effective, snapshot)
                self.assertEqual(path.read_text(encoding="utf-8"), text)
                with patch.object(self.backend, "inspect", return_value={"status": "unavailable"}):
                    self.assertEqual(self.backend.apply(original, effective, process)["capabilities"], [])

    def test_other_profiles_unchanged(self):
        original = {"hotkey_config_format": "duckstation"}
        effective = deepcopy(original)
        self.assertIs(self.backend.apply(original, effective, ProcessInfo(1, "test", ())), effective)

    def test_native_session_preserves_slot_but_removes_disc_controls_without_playlist(self):
        store = ProfileStore(ROOT / "defaults/emulators")
        store.load()
        profile = deepcopy(store.get("retroarch"))
        profile["capabilities"].append("disk_eject")
        profile["actions"]["disk_eject"] = {"method": "retroarch_udp"}
        manager = SessionManager(store, process_provider=lambda: [ProcessInfo(42, "retroarch", ("retroarch", "game.n64"))],
                                 profile_provider=lambda *_: profile)
        session = manager.refresh()
        self.assertNotIn("disk_eject", session.capabilities)
        session.slot = 5
        self.assertIs(manager.refresh(), session)
        self.assertEqual(session.slot, 5)
        self.assertNotIn("next_disc", session.capabilities)


if __name__ == "__main__":
    unittest.main()
