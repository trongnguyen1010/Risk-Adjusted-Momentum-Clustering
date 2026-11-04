"""Acquire at most two observed public detail requests for layout inspection."""
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import urlencode

from .corporate_action_sources import Document, PublicTransport, SourceLimitation, now, sha
from .hnx_announcement_discovery import DETAIL_URL


def load_selection(discovery, article_ids):
    if not 1 <= len(article_ids) <= 2 or len(set(article_ids)) != len(article_ids):
        raise ValueError("SELECT_ONE_OR_TWO_DISTINCT_ARTICLE_IDS")
    if any(not re.fullmatch(r"[0-9]+", value) for value in article_ids):
        raise ValueError("INVALID_ARTICLE_ID")
    discovery = discovery.resolve()
    manifest_path = discovery / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("artifact_type") not in {"hnx-disclosure-discovery-pilot-v1", "hnx-disclosure-discovery-v1"}:
        raise ValueError("UNSUPPORTED_DISCOVERY_ARTIFACT")
    required = {"discovered_articles.jsonl", "requests.json", "plan.json", "result.json"}
    if not required.issubset(manifest["files"]):
        raise ValueError("DISCOVERY_MANIFEST_INCOMPLETE")
    for name, digest in manifest["files"].items():
        path = (discovery / name).resolve()
        if not path.is_relative_to(discovery) or sha(path.read_bytes()) != digest:
            raise ValueError("DISCOVERY_CHECKSUM_MISMATCH: " + name)
    result = json.loads((discovery / "result.json").read_text(encoding="utf-8"))
    if result.get("limitations") or result.get("status") != "PARTIAL_DISCOVERY_ONLY":
        raise ValueError("DISCOVERY_REQUIRES_REVIEW_BEFORE_DETAIL_PILOT")
    rows = [json.loads(s) for s in (discovery / "discovered_articles.jsonl").read_text(encoding="utf-8").splitlines() if s]
    requests = json.loads((discovery / "requests.json").read_text(encoding="utf-8"))
    selected = []
    for article_id in article_ids:
        matches = [r for r in rows if r["provider_article_id"] == article_id]
        if len(matches) != 1:
            raise ValueError("ARTICLE_ID_NOT_UNIQUE_IN_DISCOVERY: " + article_id)
        row = matches[0]
        request = row["detail_request"]
        form = request.get("form", {})
        if (request.get("url") != DETAIL_URL or request.get("method") != "POST"
                or set(form) != {"pArticlesID", "pFileAttach"}
                or form["pArticlesID"] != article_id or form["pFileAttach"] != str(row["file_attach"])
                or not re.fullmatch(r"[0-9]+", form["pFileAttach"])):
            raise ValueError("DETAIL_REQUEST_OUTSIDE_OBSERVED_PUBLIC_UI")
        receipt = row["list_receipt"]
        raw = (discovery / receipt["path"]).resolve()
        if (receipt not in requests or receipt.get("status") != 200 or not raw.is_relative_to(discovery)
                or receipt["path"] not in manifest["files"] or sha(raw.read_bytes()) != receipt["source_hash"]):
            raise ValueError("DISCOVERY_LIST_RECEIPT_MISMATCH")
        selected.append(row)
    return selected, sha(manifest_path.read_bytes())


def acquire_details(discovery, article_ids, output, *, dry_run=False, transport_factory=PublicTransport):
    if output.exists():
        raise FileExistsError("REFUSE_OVERWRITE: " + str(output))
    rows, origin_hash = load_selection(discovery, article_ids)
    plan = {"stage": "HNX_DISCOVERED_DETAIL_ACCESS_PILOT", "origin_discovery": str(discovery.resolve()),
            "origin_manifest_sha256": origin_hash, "selected_articles": rows,
            "max_requests": len(rows), "interval_seconds": 2, "timeout_seconds": 15,
            "tls_verification": True, "follow_redirects": False,
            "scope": "RAW_DETAIL_RESPONSES_ONLY_NO_EVENT_OR_PIT_CERTIFICATION"}
    if dry_run:
        return dict(plan, status="DRY_RUN", network_requests=0)
    output.mkdir(parents=True, exist_ok=False)
    client = transport_factory(output, max_requests=len(rows), interval=2, timeout=15)
    acquired, limitations = [], []
    for row in rows:
        try:
            html, receipt = client.fetch(DETAIL_URL, urlencode(row["detail_request"]["form"]).encode(),
                                         content_type="application/x-www-form-urlencoded; charset=UTF-8")
            text_path = "readable/" + row["provider_article_id"] + ".txt"
            (output / "readable").mkdir(exist_ok=True)
            (output / text_path).write_text(Document(html).root.text(), encoding="utf-8")
            acquired.append({"provider_article_id": row["provider_article_id"],
                             "ticker_filter": row["ticker_filter"], "exchange_filter": row["exchange_filter"],
                             "receipt": receipt, "readable_text_path": text_path,
                             "article_content_verified": False})
        except SourceLimitation as exc:
            limitations.append({"provider_article_id": row["provider_article_id"], "reason": str(exc)})
            break
    with (output / "detail_responses.jsonl").open("x", encoding="utf-8") as stream:
        for item in acquired:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    result = {"status": "PARTIAL_RAW_DETAILS_ONLY" if not limitations else "FAILED_OR_DEFERRED",
              "network_requests": len(client.requests), "selected_articles": len(rows),
              "successful_public_responses": len(acquired), "article_contents_verified": 0,
              "limitations": limitations, "normalized_observations": 0, "canonical_build": False,
              "pit_status": "NOT_EVALUATED", "next_step": "Inspect saved raw detail layout before extraction."}
    for name, value in [("plan.json", plan), ("requests.json", client.requests), ("result.json", result)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    files = {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    code_files = [Path(__file__), Path(__file__).with_name("corporate_action_sources.py"),
                  Path(__file__).with_name("hnx_announcement_discovery.py")]
    manifest = {"artifact_type": "hnx-discovered-detail-access-pilot-v1", "created_at": now(),
                "origin_manifest_sha256": origin_hash, "status": result["status"], "files": files,
                "code_hashes": {p.name: sha(p.read_bytes()) for p in code_files}}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
