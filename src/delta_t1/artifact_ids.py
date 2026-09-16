"""Generate compact, sortable IDs for new immutable artifacts."""
from datetime import datetime, timezone
import re
import uuid


_PREFIX = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")
_TOKEN = re.compile(r"[0-9a-f]{8}")


def new_artifact_id(prefix: str, *, at=None, token: str | None = None) -> str:
    if not isinstance(prefix, str) or not _PREFIX.fullmatch(prefix):
        raise ValueError("prefix must use lowercase ASCII letters, digits, and hyphens")
    instant = datetime.now(timezone.utc) if at is None else at
    if not isinstance(instant, datetime) or instant.tzinfo is None:
        raise ValueError("at must be a timezone-aware datetime")
    value = uuid.uuid4().hex[:8] if token is None else token
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise ValueError("token must be exactly 8 lowercase hexadecimal characters")
    timestamp = instant.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{timestamp}-{value}"
