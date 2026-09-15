"""Small dependency-free HTTP edge for the product bundle and web shell."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .repository import ProductRepository


def make_handler(repository, web_root):
    web_root = Path(web_root).resolve()

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status, value):
            body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path == "/api/v1/health":
                return self._json(200, {"status": "ok", "bundle": repository.manifest})
            if path == "/api/v1/companies":
                return self._json(200, repository.list_companies())
            prefix = "/api/v1/companies/"
            if path.startswith(prefix):
                try:
                    return self._json(200, repository.get_company(path[len(prefix):]))
                except (KeyError, ValueError):
                    return self._json(404, {"error": "company_not_found"})

            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            candidate = (web_root / relative).resolve()
            if web_root not in candidate.parents and candidate != web_root:
                return self._json(404, {"error": "not_found"})
            if not candidate.is_file():
                candidate = web_root / "index.html"
            if not candidate.is_file():
                return self._json(404, {"error": "web_shell_not_found"})
            body = candidate.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    return Handler


def serve(bundle_dir, web_root, host="127.0.0.1", port=8000):
    repository = ProductRepository(bundle_dir)
    server = ThreadingHTTPServer((host, port), make_handler(repository, web_root))
    print(f"Delta Intelligence: http://{host}:{server.server_address[1]}")
    server.serve_forever()
