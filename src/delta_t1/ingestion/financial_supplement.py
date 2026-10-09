"""Acquire explicitly discovered public issuer evidence, without source preference."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from .cafef_financial import digest, encoded, immutable_write, now
from .cafef_financial_detail import PublicEvidenceClient
from .sources.base import AccessControlError, RateLimitError, SemanticValidationError


def collect(config, output_root, client=None):
    items = config["requests"]
    hosts = set(config["approved_hosts"])
    if (config.get("financial_features_allowed") is not False or not 1 <= len(items) <= 20
            or type(config["max_bytes"]) is not int or not 1 <= config["max_bytes"] <= 50_000_000):
        raise ValueError("invalid supplemental bounds")
    for item in items:
        if (not re.fullmatch(r"[A-Z0-9]{1,10}", item["symbol"]) or item["kind"] not in {"html", "pdf"}
                or type(item["year"]) is not int or not 1900 <= item["year"] <= 2100):
            raise ValueError("invalid supplemental identity/type")
        uri = urlsplit(item["url"])
        if uri.scheme != "https" or uri.username or uri.password or uri.hostname not in hosts:
            raise ValueError("supplemental host/URL not approved")
    client = client or PublicEvidenceClient(approved_hosts=hosts, max_bytes=config["max_bytes"])
    run = Path(output_root) / ("run-" + now().replace(":", "").replace("+", "-") + "-" + uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    immutable_write(run / "config.json", encoded(config))
    results, stopped = [], False
    for index, item in enumerate(items):
        record = dict(item, published_at=None, available_at=None, financial_features_allowed=False)
        if stopped:
            record["status"] = "NOT_REQUESTED_HARD_STOP"
        else:
            try:
                body, status = client.get(item["url"])
                if item["kind"] == "pdf" and not body.startswith(b"%PDF"):
                    raise SemanticValidationError("supplement is not PDF")
                name = f"{index:02d}-{item['symbol']}-{item['year']}." + ("pdf" if item["kind"] == "pdf" else "html")
                immutable_write(run / name, body)
                record.update(status="DOWNLOADED", path=str((run / name).resolve()), sha256=digest(body),
                              fetched_at=now(), http_status=status)
            except (AccessControlError, RateLimitError) as exc:
                stopped = True
                record.update(status="HARD_STOP", error=str(exc))
            except (ValueError, OSError) as exc:
                record.update(status="FAILED", error=str(exc))
        results.append(record)
    result = {"requests": results, "financial_features_allowed": False, "financial_pit_gate": "NOT_READY"}
    immutable_write(run / "inventory.json", encoded(result))
    immutable_write(run / "collector.py", Path(__file__).read_bytes())
    immutable_write(run / "manifest.json", encoded({"files": {p.relative_to(run).as_posix(): digest(p.read_bytes())
                    for p in sorted(run.rglob("*")) if p.is_file()}}))
    return run, result
