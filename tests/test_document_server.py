import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from companion_document_server import DocumentServer


class DocumentServerTests(unittest.TestCase):
    def test_serves_registered_pdf_and_byte_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            manual = Path(directory) / "Manual français.pdf"
            manual.write_bytes(b"%PDF-test")
            server = DocumentServer()
            server.start()
            try:
                url = server.url_for(manual)
                self.assertIsNotNone(url)
                assert url is not None
                with urlopen(url) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), b"%PDF-test")
                with urlopen(Request(url, method="HEAD")) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers["Content-Length"], "9")
                    self.assertEqual(response.read(), b"")
                request = Request(url, headers={"Range": "bytes=1-3"})
                with urlopen(request) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.headers["Content-Range"], "bytes 1-3/9")
                    self.assertEqual(response.read(), b"PDF")
            finally:
                server.stop()

    def test_rejects_unregistered_and_unsupported_files(self):
        with tempfile.TemporaryDirectory() as directory:
            server = DocumentServer()
            server.start()
            try:
                unsupported = Path(directory) / "program.exe"
                unsupported.touch()
                self.assertIsNone(server.url_for(unsupported))
            finally:
                server.stop()

    def test_repeated_start_and_stop_is_fast_and_idempotent(self):
        server = DocumentServer()
        for _ in range(3):
            server.start()
            first = server.diagnostics()
            self.assertTrue(first["running"])
            self.assertIsInstance(first["port"], int)

            started = time.monotonic()
            server.stop()
            self.assertLess(time.monotonic() - started, 0.3)
            self.assertEqual(
                server.diagnostics(),
                {"running": False, "port": None, "registered_documents": 0},
            )
            server.stop()


if __name__ == "__main__":
    unittest.main()
