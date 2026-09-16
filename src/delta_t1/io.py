"""Deterministic serialization and atomic writes; never mutate downloaded raw."""
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPLACE_MAX_ATTEMPTS = 6
REPLACE_BACKOFF_DELAYS = (0.05, 0.10, 0.20, 0.40, 0.80)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        for attempt in range(REPLACE_MAX_ATTEMPTS):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if attempt == REPLACE_MAX_ATTEMPTS - 1:
                    raise
                time.sleep(REPLACE_BACKOFF_DELAYS[attempt])
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def write_json(path, value):
    atomic_write(path, encoded(value) + b"\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_rows(path, rows):
    atomic_write(path, b"".join(encoded(row) + b"\n" for row in rows))


def read_rows(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]
