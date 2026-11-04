"""Khảo sát một thông báo HNX công khai; không parse canonical hoặc đổi PIT."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from .corporate_action_sources import Document, PublicTransport, SourceLimitation, now, sha


class HnxAnnouncementTransport(PublicTransport):
    # Both official hostnames are explicit; redirects remain disabled.
    HOSTS = {"hnx.vn", "www.hnx.vn"}


def probe(url, output: Path, *, dry_run=False, transport_factory=HnxAnnouncementTransport):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in HnxAnnouncementTransport.HOSTS
            or parts.username or parts.password or parts.port not in {None, 443}
            or not parts.path.startswith("/vi-vn/") or "/tin-tuc/" not in parts.path
            or not parts.path.endswith(".html") or parts.query or parts.fragment):
        raise ValueError("URL_NOT_PUBLIC_HNX_ANNOUNCEMENT")
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    plan = {"stage": "HNX_ANNOUNCEMENT_ACCESS_PILOT", "source_url": url,
            "max_requests": 1, "interval_seconds": 2, "timeout_seconds": 15,
            "tls_verification": True, "follow_redirects": False,
            "scope": "ONE_PUBLIC_PAGE_ONLY_NOT_HISTORY_COVERAGE"}
    if dry_run:
        return dict(plan, status="DRY_RUN", network_requests=0)
    output.mkdir(parents=True, exist_ok=False)
    transport = transport_factory(output, max_requests=1, interval=2, timeout=15)
    received, reason = False, None
    try:
        html, _ = transport.fetch(url)
        (output / "readable_text.txt").write_text(Document(html).root.text(), encoding="utf-8")
        received = True
    except SourceLimitation as exc:
        reason = str(exc)
    result = dict(plan, status="PARTIAL" if received else "FAILED_OR_DEFERRED",
                  public_response_received=received, limitation=reason,
                  network_requests=len(transport.requests),
                  article_parser_status="NOT_RUN_BY_ACCESS_PROBE", pit_status="NOT_EVALUATED",
                  canonical_build=False, next_step="Inspect raw article/layout before implementing extraction.")
    for name, value in [("plan.json", plan), ("requests.json", transport.requests), ("result.json", result)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"artifact_type": "hnx-announcement-access-pilot-v1", "created_at": now(),
                "status": result["status"], "source_url": url,
                "code_hashes": {p.name: sha(p.read_bytes()) for p in [Path(__file__), Path(__file__).with_name("corporate_action_sources.py")]},
                "files": {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
