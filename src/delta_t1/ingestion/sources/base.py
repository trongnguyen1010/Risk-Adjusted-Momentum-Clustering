"""Common source interface plus bounded CSV/HTTP transport helpers."""
from abc import ABC, abstractmethod
import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class SourceNotVerifiedError(ValueError):
    pass


class SourceAdapter(ABC):
    source_id: str
    verification_status: str = "DISCOVERED"

    def require_verified_semantics(self) -> None:
        if self.verification_status not in ("SEMANTICS_VERIFIED", "PILOT_APPROVED", "PRODUCTION_APPROVED"):
            raise SourceNotVerifiedError(
                f"{self.source_id} endpoint semantics and data rights are not verified"
            )

    @abstractmethod
    def acquire(self, request: dict) -> dict:
        """Return an immutable provider envelope, never a canonical row."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpClient:
    def __init__(self, timeout=30, attempts=3, min_interval=2.0, max_bytes=20_000_000):
        if timeout <= 0 or attempts < 1 or min_interval < 0 or max_bytes < 1:
            raise ValueError("invalid HTTP limits")
        self.timeout, self.attempts = timeout, attempts
        self.min_interval, self.max_bytes = min_interval, max_bytes
        self.last_request = 0.0
        self.opener = build_opener(NoRedirect())

    def get(self, url, token_env=None):
        parsed = urlsplit(url)
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1")):
            raise ValueError("HTTPS required outside loopback")
        if parsed.username or parsed.password:
            raise ValueError("credentials must be supplied through an environment variable")
        headers = {"User-Agent": "DeltaT1Research/0.1", "Accept": "application/json"}
        if token_env:
            token = os.environ.get(token_env)
            if not token:
                raise ValueError("missing token environment variable: " + token_env)
            headers["Authorization"] = "Bearer " + token
        for attempt in range(self.attempts):
            time.sleep(max(0, self.min_interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                with self.opener.open(Request(url, headers=headers), timeout=self.timeout) as response:
                    data = response.read(self.max_bytes + 1)
                    if len(data) > self.max_bytes:
                        raise ValueError("response exceeds max_bytes; reduce batch size")
                    return data
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504):
                    raise ValueError(f"HTTP {exc.code}; request stopped") from None
                delay = float(2 ** attempt)
                retry_after = exc.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        delay = max(delay, (parsedate_to_datetime(retry_after)
                                            - datetime.now(timezone.utc)).total_seconds())
                if delay > 60:
                    raise ValueError("server requests a long cooldown; resume this run later") from None
            except (URLError, TimeoutError, ConnectionError):
                delay = float(2 ** attempt)
            if attempt + 1 < self.attempts:
                time.sleep(delay)
        raise ValueError("HTTP retry limit reached")


def parse_csv(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def json_page(data, items_key="items", next_key="next_cursor"):
    payload = json.loads(data)
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict) or not isinstance(payload.get(items_key), list):
        raise ValueError("expected JSON array or object containing items array")
    cursor = payload.get(next_key)
    if cursor is not None and not isinstance(cursor, (str, int)):
        raise ValueError("next cursor must be scalar or null")
    return payload[items_key], cursor


def page_url(endpoint, params, cursor, cursor_param="cursor"):
    if urlsplit(endpoint).query or urlsplit(endpoint).fragment:
        raise ValueError("endpoint must not contain query or fragment; use params")
    query = dict(params)
    if cursor is not None:
        query[cursor_param] = cursor
    return endpoint + ("?" + urlencode(query) if query else "")


def contained_file(root, relative):
    """Reject paths escaping a manifest root, including symlinks."""
    from pathlib import Path
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("manifest path escapes run directory")
    return path
