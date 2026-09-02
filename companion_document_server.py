from __future__ import annotations

import mimetypes
import secrets
import threading
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from companion_documents import DOCUMENT_EXTENSIONS


class DocumentServer:
    """Serve explicitly registered documents to Steam's HTTP-only browser."""

    def __init__(self) -> None:
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._documents: OrderedDict[str, Path] = OrderedDict()
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._server is not None:
            return
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                owner._handle(self)

            def do_HEAD(self) -> None:
                owner._handle(self, head_only=True)

            def log_message(self, format: str, *args: object) -> None:
                del format, args

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        server, thread = self._server, self._thread
        self._server = None
        self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=2)
        with self._lock:
            self._documents.clear()

    def url_for(self, path: Path) -> str | None:
        if self._server is None:
            return None
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_file() or resolved.suffix.casefold() not in DOCUMENT_EXTENSIONS:
                return None
        except (OSError, RuntimeError):
            return None
        token = secrets.token_urlsafe(24)
        with self._lock:
            self._documents[token] = resolved
            while len(self._documents) > 64:
                self._documents.popitem(last=False)
        return f"http://127.0.0.1:{self._server.server_port}/document/{token}"

    def _handle(self, request: BaseHTTPRequestHandler, head_only: bool = False) -> None:
        route = unquote(urlsplit(request.path).path)
        prefix = "/document/"
        if not route.startswith(prefix):
            request.send_error(404)
            return
        token = route[len(prefix):]
        with self._lock:
            path = self._documents.get(token)
        if path is None:
            request.send_error(404)
            return
        try:
            size = path.stat().st_size
            start, end = self._range(request.headers.get("Range"), size)
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if path.suffix.casefold() in {".txt", ".md", ".markdown", ".html", ".htm"}:
                content_type = "text/plain; charset=utf-8"
            request.send_response(206 if start != 0 or end != size - 1 else 200)
            request.send_header("Content-Type", content_type)
            request.send_header("Content-Length", str(max(0, end - start + 1)))
            request.send_header("Accept-Ranges", "bytes")
            request.send_header("Cache-Control", "no-store")
            request.send_header("X-Content-Type-Options", "nosniff")
            request.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(path.name)}")
            if start != 0 or end != size - 1:
                request.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            request.end_headers()
            if head_only:
                return
            with path.open("rb") as stream:
                stream.seek(start)
                remaining = max(0, end - start + 1)
                while remaining:
                    chunk = stream.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    request.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            return
        except OSError:
            if not request.wfile.closed:
                request.send_error(404)

    @staticmethod
    def _range(value: str | None, size: int) -> tuple[int, int]:
        if not value or not value.startswith("bytes=") or size == 0:
            return 0, max(0, size - 1)
        try:
            raw_start, raw_end = value[6:].split("-", 1)
            if not raw_start:
                length = min(size, int(raw_end))
                return size - length, size - 1
            start = int(raw_start)
            end = min(size - 1, int(raw_end)) if raw_end else size - 1
            if start < 0 or start > end or start >= size:
                raise ValueError
            return start, end
        except (TypeError, ValueError):
            return 0, max(0, size - 1)
