import tempfile
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


if __name__ == "__main__":
    unittest.main()
