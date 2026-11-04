"""Freeze offline nhu cầu/cache cho bounded local job; không có network path."""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions.hnx_local_supplement import (
    TICKERS, PREP, CONFIG, read, rows, write, hashes, runtime, validate)
from delta_t1.ingestion.corporate_action_sources import sha
from delta_t1.ingestion.corporate_action_cache_audit import document_view


def pinned_file(folder, name):
    manifest = read(folder / "manifest.json")
    path = folder / name
    if sha(path.read_bytes()) != manifest["files"][name]:
        raise ValueError("INPUT_HASH_MISMATCH: " + str(path))
    return path


def main():
    out = ROOT / PREP
    if out.exists():
        raise FileExistsError("REFUSE_OVERWRITE_PREPARATION")
    queue_root = ROOT / "tmp/ca_supplement_plan_20261102_v1"
    cache_root = ROOT / "tmp/ca_cache_inventory_20261102_v4"
    queue_path = pinned_file(queue_root, "missing_event_fields_602.jsonl")
    audit_path = pinned_file(cache_root, "field_cache_audit.jsonl")
    raw_index = pinned_file(cache_root, "raw_document_index.jsonl")
    queue, audits = rows(queue_path), rows(audit_path)
    canonical_path = "artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl"
    securities = rows(ROOT / canonical_path)
    sec = {s["ticker"]: s for s in securities}
    if len(securities) != 1522 or len(sec) != 1522:
        raise ValueError("EXACT_C8_V2_1522_REQUIRED")
    incident_path = ROOT / "tmp/ca_hnx_round2_four_shard_incident_20261102_v1/audit.json"
    incident = read(incident_path)
    normalized_root = ROOT / "tmp/ca_offline_reconciliation_20261102_v1"
    normalized_path = pinned_file(normalized_root, "source_evidence_used.jsonl")
    normalized = [r for r in rows(normalized_path) if r["ticker"] in TICKERS]
    if any(r["source_type"] == "HNX" for r in normalized):
        raise ValueError("NORMALIZED_HNX_CACHE_REQUIRES_OFFLINE_REVIEW")
    hnx = {t: {"discovery_ids": set(), "detail_ids": set(), "checkpoint": None} for t in TICKERS}
    archive_evidence = []
    for shard in incident["shards"]:
        path = Path(shard["archive_path"])
        if sha(path.read_bytes()) != shard["archive_sha256"]:
            raise ValueError("STOPPED_ZIP_CHANGED")
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            checkpoint_name = sorted(n for n in names if n.endswith("/collection/checkpoint.json"))[-1]
            checkpoint = json.loads(archive.read(checkpoint_name))
            result_name = checkpoint_name.removesuffix("checkpoint.json") + "result.json"
            result = json.loads(archive.read(result_name))
            if result.get("resumable") is not False:
                raise ValueError("OLD_STOP_STATE_NOT_PRESERVED")
            for t in TICKERS:
                if t in checkpoint["states"]:
                    hnx[t]["checkpoint"] = checkpoint["states"][t]
            for name in names:
                if not name.endswith(("discovered_articles.jsonl", "detail_responses.jsonl")):
                    continue
                for row in map(json.loads, archive.read(name).decode("utf-8").splitlines()):
                    ticker = row["ticker_filter"]
                    if ticker in hnx:
                        key = "discovery_ids" if name.endswith("discovered_articles.jsonl") else "detail_ids"
                        hnx[ticker][key].add(row["provider_article_id"])
            archive_evidence.append({"path": str(path), "sha256": shard["archive_sha256"],
                "latest_checkpoint": checkpoint_name, "checkpoint_sha256": sha(archive.read(checkpoint_name)),
                "resumable": result["resumable"], "status": result["status"]})
    # The remaining local HNX pilots are small, known directories, not a repository recrawl.
    local_roots = [ROOT / "tmp" / n for n in (
        "hnx_discovery_pilot_20261101_230806", "hnx_detail_pilot_20261101_231720",
        "hnx_batch_first_two_20261101_v1", "hnx_details_parsed_20261101_v1")]
    local_roots += [ROOT / "data/corporate_actions/work" / n for n in (
        "hnx_local_recheck_20261103_v1", "hnx_pvs_local_pilot_v1", "hnx_acv_local_pilot_v1")]
    local_files = {}
    for root in local_roots:
        for pattern, key in (("discovered_articles.jsonl", "discovery_ids"), ("detail_responses.jsonl", "detail_ids")):
            for path in root.rglob(pattern):
                local_files[str(path)] = sha(path.read_bytes())
                for row in rows(path):
                    if row["ticker_filter"] in hnx:
                        hnx[row["ticker_filter"]][key].add(row["provider_article_id"])
    targets, chosen_audits, offline_only = [], [], []
    for ticker in TICKERS:
        state = hnx[ticker]
        if (state["checkpoint"] is None or state["checkpoint"]["discovery"] is not None
                or state["checkpoint"]["handled"] or state["checkpoint"]["quarantined"]
                or state["discovery_ids"] or state["detail_ids"]):
            raise ValueError("TARGET_HAS_HNX_CACHE_REVIEW_OFFLINE_FIRST: " + ticker)
        options = []
        for task in queue:
            if task["ticker"] != ticker:
                continue
            audit = next(a for a in audits if a["bucket"] == "MISSING_FIELDS"
                and a["vci_payload_sha256"] == task["vci_payload_sha256"])
            if any(f["status"] != "ONLY_OTHER_OR_UNLINKED_CACHED_DOCUMENTS" for f in audit["fields"].values()):
                offline_only.append({"ticker": ticker, "payload": task["vci_payload_sha256"], "audit": audit,
                    "action": "OFFLINE_REVIEW_NO_NEW_REQUEST_FOR_THIS_PAYLOAD"})
                continue
            options.append((task, audit))
        # One row/window per ticker: maximize actual field need, then latest public-date hint.
        task, audit = max(options, key=lambda p: (len(p[0]["missing_fields"]),
            p[0]["original_sdk_row"]["public_date"], p[0]["vci_payload_sha256"]))
        hint = datetime.fromisoformat(task["original_sdk_row"]["public_date"].replace("Z", "+00:00"))
        hint = hint.astimezone(timezone(timedelta(hours=7))).date()
        target = {"ticker": ticker, "exchange": sec[ticker]["exchange"],
            "queue": str(queue_path.relative_to(ROOT)), "queue_payload_sha256": task["vci_payload_sha256"],
            "original_sdk_row": task["original_sdk_row"], "missing_fields": task["missing_fields"],
            "event_type_hint": audit["category"], "search_hint_date": hint.isoformat(),
            "published_start": max(date(2019, 1, 31), hint - timedelta(days=120)).isoformat(),
            "published_end": min(date(2025, 12, 31), hint + timedelta(days=120)).isoformat(),
            "hint_semantics": "RETRIEVAL_ONLY_NOT_EVENT_MATCH_PUBLICATION_OR_PIT_PROOF",
            "cache_field_status": {f: v["status"] for f, v in audit["fields"].items()},
            "vsdc_declared_ticker_cached_articles": audit["all_declared_ticker_cached_article_count"],
            "hnx_cached_discovery_articles": len(state["discovery_ids"]),
            "hnx_cached_successful_details": len(state["detail_ids"]), "cached_successful_article_ids": [],
            "request_reason": "Missing event fields; no HNX discovery/detail cache for pending ticker; VSDC cache has no supported dated field anchor for this payload. Not a PIT/identity retry."}
        targets.append(target)
        chosen_audits.append(audit)
    # Independently verify and re-inspect only cached VSDC documents of the selected tickers.
    raw_evidence = []
    for doc in rows(raw_index):
        if doc.get("ticker") not in TICKERS:
            continue
        path = ROOT / doc["raw_path"]
        body = path.read_bytes()
        if sha(body) != doc["source_hash"]:
            raise ValueError("CACHED_RAW_CHANGED")
        view = document_view(body, doc["source_url"], ("RIGHTS_ISSUE", "STOCK_DIVIDEND", "BONUS_SHARE"))
        for key in ("ticker", "record_dates", "ex_dates", "components"):
            if view[key] != doc[key]:
                raise ValueError("CACHED_REPARSE_DIFF_REQUIRES_OFFLINE_REVIEW")
        raw_evidence.append({"ticker": doc["ticker"], "path": str(path), "sha256": doc["source_hash"],
            "document_id": doc["document_id"], "source_url": doc["source_url"],
            "record_dates": view["record_dates"], "ex_dates": view["ex_dates"], "components": view["components"]})
    inputs = [queue_path, audit_path, raw_index, incident_path, normalized_path, ROOT / canonical_path,
        ROOT / "data/corporate_actions/work/hnx_pvs_local_pilot_review_20261103_v1/audit.json",
        ROOT / "data/corporate_actions/work/hnx_acv_local_pilot_review_20261103_v1/audit.json"]
    plan = {"stage": "HNX_LOCAL_SUPPLEMENT10_PREPARATION", "canonical_path": canonical_path,
        "canonical_sha256": sha((ROOT / canonical_path).read_bytes()), "inventory_tickers": 1522,
        "queue_rows": len(queue), "queue_tickers": len({t["ticker"] for t in queue}),
        "hnx_upcom_queue_rows": sum(sec.get(t["ticker"], {}).get("exchange") in {"HNX", "UPCOM"} for t in queue),
        "targets": targets, "selected_payloads": 10, "selected_field_tasks": sum(len(t["missing_fields"]) for t in targets),
        "canonical_fields_applied": 0, "network_requests_preparation": 0,
        "cache_scope": "VSDC audited raw inventory, prior normalized source inventory, four latest cumulative HNX ZIPs and named local HNX pilots; no full-history absence claim",
        "manual_review_required": "PIT/historical identity/source selection/final freeze; unchanged and not applied"}
    validate(read(ROOT / CONFIG), plan)
    out.mkdir(parents=True)
    for name, value in (("plan.json", plan), ("selected_cache_audits.json", chosen_audits),
            ("offline_only_payloads.json", offline_only), ("cached_raw_reparse.json", raw_evidence),
            ("prior_normalized_evidence.json", normalized),
            ("hnx_cache_scan.json", {"archives": archive_evidence, "local_files": local_files,
                "selected_ticker_states": {t: hnx[t]["checkpoint"] for t in TICKERS}}),
            ("inputs.json", {str(p): sha(p.read_bytes()) for p in inputs}),
            ("runtime.json", runtime(ROOT)),
            ("checkpoint_template.json", {"status": "PREPARED_NOT_RUN", "resumable": False,
                "requests_total": 0, "completed_units": [], "old_checkpoint_resume": False})):
        write(out / name, value)
    write(out / "manifest.json", {"artifact_type": "hnx-local-supplement10-preparation-v1", "files": hashes(out)})
    print(json.dumps({"output": str(out), "tickers": list(TICKERS), "field_tasks": plan["selected_field_tasks"],
        "vsdc_cached_raw_reparsed": len(raw_evidence), "offline_only_payloads": len(offline_only), "requests": 0}))


if __name__ == "__main__":
    main()
