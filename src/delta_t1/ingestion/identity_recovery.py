"""Stage A6 — evidence-backed historical identity recovery.

Offline and fail-closed: current tickers and company names are never entity keys.
Without a reviewed local evidence bundle, observations remain provisional.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
import io
import json
from pathlib import Path
import re

from ..artifact_ids import new_artifact_id
from ..io import atomic_write, digest, encoded, now, read_json, read_rows, write_json, write_rows
from .primary_recovery import _git_commit, _inside, _verify_artifacts

STAGE = "A6 — Historical Identity Recovery"
IDENTITY_HISTORY_COLUMNS = (
    "security_id", "ticker", "exchange", "effective_from", "effective_to",
    "evidence_source", "evidence_reference", "identity_confidence",
)
CANDIDATE_COLUMNS = (
    "candidate_id", "security_id", "from_ticker", "from_exchange", "to_ticker",
    "to_exchange", "effective_date", "recovery_type", "evidence_source",
    "evidence_reference", "identity_confidence", "evidence_document",
    "evidence_sha256", "from_provider_symbol", "to_provider_symbol",
    "decision", "reason",
)
EXCHANGES = {"HOSE", "HNX", "UPCOM"}
RECOVERY_TYPES = {"EXCHANGE_TRANSFER", "TICKER_RENAME", "PROVIDER_SYMBOL_CHANGE"}
EVIDENCE_SOURCES = {
    "LISTING_NOTICE", "EXCHANGE_TRANSFER_DISCLOSURE", "CORPORATE_REGISTRY",
    "PROVIDER_PROFILE",
}
CONFIDENCE_BY_SOURCE = {
    "LISTING_NOTICE": "HIGH", "EXCHANGE_TRANSFER_DISCLOSURE": "HIGH",
    "CORPORATE_REGISTRY": "HIGH", "PROVIDER_PROFILE": "MEDIUM",
}
_TICKER = re.compile(r"^[A-Z0-9]{1,12}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _iso(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be canonical YYYY-MM-DD")
    return parsed


def _ticker(value, field):
    if not isinstance(value, str) or not _TICKER.fullmatch(value):
        raise ValueError(f"{field} must be an uppercase exchange ticker")
    return value


def _csv_bytes(rows, columns):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _load_records(path):
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        rows = value if isinstance(value, list) else value.get("transitions")
    elif path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    elif path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
    else:
        raise ValueError("evidence file must be JSON, JSONL, or CSV")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("evidence file must contain a list of objects")
    return rows


def validate_evidence_record(raw, review, *, canonical_ids, evidence_dir, row_number, cutoff):
    """Validate a transition and its immutable local source document."""
    required = (
        "security_id", "from_ticker", "from_exchange", "to_ticker", "to_exchange",
        "from_effective_from", "effective_date", "recovery_type", "evidence_source",
        "evidence_id", "evidence_reference", "evidence_document", "evidence_sha256",
        "match_method",
    )
    missing = [name for name in required if raw.get(name) in (None, "")]
    if missing:
        raise ValueError("missing evidence fields: " + ",".join(missing))
    security_id = raw["security_id"]
    if security_id not in canonical_ids:
        raise ValueError(f"unknown canonical security_id: {security_id}")
    if raw["match_method"] != "STABLE_SECURITY_ID_DOCUMENTED":
        raise ValueError("ticker/name-only identity matching is forbidden")
    assertion_hash = digest(encoded(raw))
    if not isinstance(review, dict) or review.get("decision") != "APPROVED":
        raise ValueError("evidence lacks independent APPROVED review")
    if review.get("assertion_sha256") != assertion_hash:
        raise ValueError("review assertion_sha256 mismatch")
    if not str(review.get("reviewer_id", "")).strip():
        raise ValueError("reviewer_id is required")
    try:
        reviewed = date.fromisoformat(str(review["reviewed_at"])[:10])
    except ValueError as exc:
        raise ValueError("reviewed_at must begin with an ISO date") from exc
    if reviewed > date.today():
        raise ValueError("reviewed_at cannot be in the future")
    recovery_type, source = raw["recovery_type"], raw["evidence_source"]
    if recovery_type not in RECOVERY_TYPES:
        raise ValueError(f"unsupported recovery_type: {recovery_type}")
    if source not in EVIDENCE_SOURCES:
        raise ValueError(f"unsupported evidence_source: {source}")
    reference = str(raw["evidence_reference"]).strip()
    if not reference or "NAME_ONLY" in reference.upper() or "SIMILAR" in reference.upper():
        raise ValueError("evidence_reference cannot be name-similarity evidence")
    from_ticker, to_ticker = _ticker(raw["from_ticker"], "from_ticker"), _ticker(raw["to_ticker"], "to_ticker")
    if raw["from_exchange"] not in EXCHANGES or raw["to_exchange"] not in EXCHANGES:
        raise ValueError("from_exchange/to_exchange must be HOSE, HNX, or UPCOM")
    start, effective = _iso(raw["from_effective_from"], "from_effective_from"), _iso(raw["effective_date"], "effective_date")
    if start >= effective:
        raise ValueError("from_effective_from must precede effective_date")
    if effective > cutoff:
        raise ValueError(f"effective_date exceeds canonical cutoff {cutoff.isoformat()}")
    if from_ticker == to_ticker and raw["from_exchange"] == raw["to_exchange"]:
        if recovery_type != "PROVIDER_SYMBOL_CHANGE":
            raise ValueError("identity transition does not change ticker or exchange")
    if recovery_type == "EXCHANGE_TRANSFER" and (from_ticker != to_ticker or raw["from_exchange"] == raw["to_exchange"]):
        raise ValueError("EXCHANGE_TRANSFER must preserve ticker and change exchange")
    if recovery_type == "TICKER_RENAME" and (from_ticker == to_ticker or raw["from_exchange"] != raw["to_exchange"]):
        raise ValueError("TICKER_RENAME must change ticker and preserve exchange")
    if recovery_type == "PROVIDER_SYMBOL_CHANGE":
        if (from_ticker, raw["from_exchange"]) != (to_ticker, raw["to_exchange"]):
            raise ValueError("PROVIDER_SYMBOL_CHANGE cannot alter market ticker/exchange")
        if not raw.get("from_provider_symbol") or not raw.get("to_provider_symbol"):
            raise ValueError("PROVIDER_SYMBOL_CHANGE requires provider symbols")
        if raw["from_provider_symbol"] == raw["to_provider_symbol"]:
            raise ValueError("provider symbol transition must change symbol")
    document = _inside(evidence_dir / str(raw["evidence_document"]), evidence_dir, "evidence document")
    if not document.is_file():
        raise ValueError(f"evidence document not found: {raw['evidence_document']}")
    expected = raw["evidence_sha256"]
    if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
        raise ValueError("evidence_sha256 must be lowercase SHA-256")
    actual = digest(document.read_bytes())
    if actual != expected:
        raise ValueError(f"evidence document checksum mismatch: {raw['evidence_document']}")
    if review.get("document_sha256") != actual:
        raise ValueError("review document_sha256 mismatch")
    if not str(review.get("issuer_identifier", "")).strip() or not str(review.get("document_locator", "")).strip():
        raise ValueError("review requires issuer_identifier and document_locator")
    bindings = review.get("field_bindings")
    bound_fields = {"security_id", "from_ticker", "from_exchange", "to_ticker",
                    "to_exchange", "from_effective_from", "effective_date"}
    if not isinstance(bindings, dict) or not bound_fields <= set(bindings) or any(
            not str(bindings[field]).strip() for field in bound_fields):
        raise ValueError("review field_bindings must locate every identity assertion")
    return {
        "candidate_id": str(raw["evidence_id"]), "security_id": security_id,
        "from_ticker": from_ticker, "from_exchange": raw["from_exchange"],
        "to_ticker": to_ticker, "to_exchange": raw["to_exchange"],
        "from_effective_from": start.isoformat(), "effective_date": effective.isoformat(),
        "recovery_type": recovery_type, "evidence_source": source,
        "evidence_reference": reference, "identity_confidence": CONFIDENCE_BY_SOURCE[source],
        "evidence_document": document.relative_to(evidence_dir).as_posix(),
        "evidence_sha256": actual, "from_provider_symbol": raw.get("from_provider_symbol", ""),
        "to_provider_symbol": raw.get("to_provider_symbol", ""),
        "review_status": "APPROVED", "reviewer": str(review["reviewer_id"]).strip(),
        "reviewed_at": str(review["reviewed_at"]), "review_policy_id": review["review_policy_id"],
        "issuer_identifier": review["issuer_identifier"], "document_locator": review["document_locator"],
        "field_bindings": bindings, "match_method": raw["match_method"],
        "raw_record_sha256": assertion_hash,
    }


def load_evidence_bundle(path, review_path=None, scope_path=None, *, root, canonical_ids, cutoff):
    if path is None:
        if review_path is not None or scope_path is not None:
            raise ValueError("evidence, review manifest and candidate scope must be supplied together")
        return [], [], {}, None
    if review_path is None or scope_path is None:
        raise ValueError("evidence file requires independent review manifest and candidate scope")
    root, evidence_path = Path(root).resolve(), _inside(path, Path(root).resolve(), "identity evidence file")
    review_path = _inside(review_path, root, "identity review manifest")
    scope_path = _inside(scope_path, root, "identity candidate scope")
    if not evidence_path.is_file():
        raise FileNotFoundError(evidence_path)
    if not review_path.is_file():
        raise FileNotFoundError(review_path)
    if not scope_path.is_file():
        raise FileNotFoundError(scope_path)
    scope_rows = _load_records(scope_path)
    scope_ids = [row.get("security_id") for row in scope_rows]
    if None in scope_ids or len(set(scope_ids)) != len(scope_ids):
        raise ValueError("candidate scope security_id values must be present and unique")
    if not set(scope_ids) <= canonical_ids:
        raise ValueError("candidate scope contains unknown canonical security_id")
    for row in scope_rows:
        if not all(str(row.get(field, "")).strip() for field in
                   ("scope_reason", "scope_source", "scope_reference")):
            raise ValueError("candidate scope requires reason, source and reference")
    review_manifest = read_json(review_path)
    if review_manifest.get("review_policy_id") != "A6_MANUAL_IDENTITY_REVIEW_V1":
        raise ValueError("unsupported identity review policy")
    if review_manifest.get("scope_complete") is not True:
        raise ValueError("identity review scope is not complete")
    reviews = review_manifest.get("reviews")
    if not isinstance(reviews, list) or any(not isinstance(item, dict) for item in reviews):
        raise ValueError("review manifest reviews must be a list")
    review_by_id = {item.get("evidence_id"): item for item in reviews}
    if None in review_by_id or len(review_by_id) != len(reviews):
        raise ValueError("review evidence_id values must be unique")
    accepted, rejected, document_hashes = [], [], {}
    rows = _load_records(evidence_path)
    evidence_ids = [row.get("evidence_id") for row in rows]
    if None in evidence_ids or len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError("evidence_id values must be present and unique")
    if set(evidence_ids) != set(review_by_id):
        raise ValueError("review scope must cover every evidence candidate exactly")
    dispositions = review_manifest.get("scope_dispositions")
    if not isinstance(dispositions, list) or any(not isinstance(row, dict) for row in dispositions):
        raise ValueError("review manifest requires scope_dispositions")
    disposition_by_id = {row.get("security_id"): row for row in dispositions}
    if None in disposition_by_id or len(disposition_by_id) != len(dispositions) or set(disposition_by_id) != set(scope_ids):
        raise ValueError("scope_dispositions must cover candidate scope exactly")
    allowed_dispositions = {"TRANSITION_ASSERTED", "NO_VERIFIED_TRANSITION", "REJECTED"}
    for security_id, disposition in disposition_by_id.items():
        if disposition.get("disposition") not in allowed_dispositions:
            raise ValueError(f"invalid scope disposition: {security_id}")
        if not str(disposition.get("reviewer_id", "")).strip() or not str(disposition.get("reason", "")).strip():
            raise ValueError("scope disposition requires reviewer_id and reason")
    evidence_scope = {row.get("security_id") for row in rows}
    if not evidence_scope <= set(scope_ids):
        raise ValueError("transition assertion falls outside candidate scope")
    for security_id in scope_ids:
        has_assertion = security_id in evidence_scope
        disposition = disposition_by_id[security_id]["disposition"]
        if disposition == "TRANSITION_ASSERTED" and not has_assertion:
            raise ValueError("TRANSITION_ASSERTED scope item has no assertion")
        if disposition == "NO_VERIFIED_TRANSITION" and has_assertion:
            raise ValueError("NO_VERIFIED_TRANSITION scope item cannot have assertion")
    for index, raw in enumerate(rows, 1):
        try:
            review = {**review_by_id[raw["evidence_id"]],
                      "review_policy_id": review_manifest["review_policy_id"]}
            event = validate_evidence_record(raw, review, canonical_ids=canonical_ids,
                                             evidence_dir=evidence_path.parent, row_number=index,
                                             cutoff=cutoff)
            accepted.append(event)
            document_hashes[event["evidence_document"]] = event["evidence_sha256"]
        except (KeyError, TypeError, ValueError, OSError) as exc:
            rejected.append({"candidate_id": str(raw.get("evidence_id") or f"A6-CAND-{index:05d}"),
                             "security_id": raw.get("security_id", ""),
                             "decision": "REJECTED", "reason": f"{type(exc).__name__}: {exc}",
                             "raw_record_sha256": digest(encoded(raw)), "raw_record": raw})
    return accepted, rejected, document_hashes, {
        "path": evidence_path.relative_to(root).as_posix(),
        "sha256": digest(evidence_path.read_bytes()), "rows": len(rows),
        "review_manifest_path": review_path.relative_to(root).as_posix(),
        "review_manifest_sha256": digest(review_path.read_bytes()),
        "candidate_scope_path": scope_path.relative_to(root).as_posix(),
        "candidate_scope_sha256": digest(scope_path.read_bytes()),
        "scope_security_ids": scope_ids, "scope_dispositions": dispositions,
        "scope_complete": True,
    }


def validate_intervals(rows):
    by_security = defaultdict(list)
    by_symbol = defaultdict(list)
    for row in rows:
        if not row.get("security_id"):
            raise ValueError("identity interval missing security_id")
        _ticker(row.get("ticker"), "ticker")
        if row.get("exchange") not in EXCHANGES:
            raise ValueError("identity interval has invalid exchange")
        start = _iso(row.get("effective_from"), "effective_from")
        if row.get("effective_to") is not None:
            end = _iso(row["effective_to"], "effective_to")
            if start > end:
                raise ValueError("effective_from must not follow effective_to")
        if row.get("identity_confidence") not in {"HIGH", "MEDIUM", "PROVISIONAL"}:
            raise ValueError("identity interval has invalid confidence")
        if not row.get("evidence_source") or not row.get("evidence_reference"):
            raise ValueError("identity interval requires evidence provenance")
        by_security[row["security_id"]].append(row)
        by_symbol[(row["ticker"], row["exchange"])].append(row)
    for security_id, values in by_security.items():
        values.sort(key=lambda row: row["effective_from"])
        for left, right in zip(values, values[1:]):
            if left["effective_to"] is None:
                raise ValueError(f"open identity interval precedes another: {security_id}")
            if left["effective_to"] >= right["effective_from"]:
                raise ValueError(f"overlapping identity intervals: {security_id}")
    for (ticker, exchange), values in by_symbol.items():
        values.sort(key=lambda row: row["effective_from"])
        for left, right in zip(values, values[1:]):
            left_end = left["effective_to"] or "9999-12-31"
            if left["security_id"] != right["security_id"] and left_end >= right["effective_from"]:
                raise ValueError(f"cross-entity ticker interval collision: {ticker}/{exchange}")


def build_identity_history(securities, accepted_events):
    canonical = {row["security_id"]: row for row in securities}
    if len(canonical) != len(securities):
        raise ValueError("duplicate canonical security_id")
    grouped, all_by_security, issuer_to_ids = defaultdict(list), defaultdict(list), defaultdict(set)
    for event in accepted_events:
        all_by_security[event["security_id"]].append(event)
        issuer_to_ids[event["issuer_identifier"]].add(event["security_id"])
        if event["recovery_type"] != "PROVIDER_SYMBOL_CHANGE":
            grouped[event["security_id"]].append(event)
    rows, confirmed, rejected_chains = [], set(), []
    for security_id, security in sorted(canonical.items()):
        events = sorted(grouped.get(security_id, []), key=lambda row: row["effective_date"])
        all_events = all_by_security.get(security_id, [])
        issuers = {event["issuer_identifier"] for event in all_events}
        issuer_conflict = (len(issuers) > 1 or any(
            len(issuer_to_ids[issuer]) > 1 for issuer in issuers))
        if issuer_conflict:
            rejected_chains.extend({**event, "decision": "REJECTED",
                                    "reason": "ISSUER_IDENTIFIER_NOT_ONE_TO_ONE"}
                                   for event in all_events)
            continue
        if not events:
            continue
        reason = ("INSUFFICIENT_CONFIDENCE_FOR_MARKET_IDENTITY"
                  if any(event["identity_confidence"] != "HIGH" for event in events) else None)
        for previous, current in zip(events, events[1:]):
            if (previous["to_ticker"], previous["to_exchange"]) != (current["from_ticker"], current["from_exchange"]):
                reason = "DISCONNECTED_MULTI_EVENT_CHAIN"
                break
            if current["from_effective_from"] != previous["effective_date"]:
                reason = "INCONSISTENT_EVENT_STATE_START"
                break
            if previous["effective_date"] >= current["effective_date"]:
                reason = "NON_INCREASING_EVENT_DATES"
                break
        final = events[-1]
        if not reason and (final["to_ticker"], final["to_exchange"]) != (security["ticker"], security["exchange"]):
            reason = "FINAL_IDENTITY_DOES_NOT_MATCH_CANONICAL"
        if reason:
            rejected_chains.extend({**event, "decision": "REJECTED", "reason": reason} for event in events)
            continue
        first = events[0]
        rows.append({"security_id": security_id, "ticker": first["from_ticker"],
                     "exchange": first["from_exchange"], "effective_from": first["from_effective_from"],
                     "effective_to": (date.fromisoformat(first["effective_date"]) - timedelta(days=1)).isoformat(),
                     "evidence_source": first["evidence_source"], "evidence_reference": first["evidence_reference"],
                     "identity_confidence": first["identity_confidence"]})
        for index, event in enumerate(events):
            next_date = events[index + 1]["effective_date"] if index + 1 < len(events) else None
            end = ((date.fromisoformat(next_date) - timedelta(days=1)).isoformat()
                   if next_date else security.get("valid_to"))
            rows.append({"security_id": security_id, "ticker": event["to_ticker"],
                         "exchange": event["to_exchange"], "effective_from": event["effective_date"],
                         "effective_to": end, "evidence_source": event["evidence_source"],
                         "evidence_reference": event["evidence_reference"],
                         "identity_confidence": event["identity_confidence"]})
        confirmed.add(security_id)
    rows.sort(key=lambda row: (row["security_id"], row["effective_from"]))
    validate_intervals(rows)
    return rows, confirmed, rejected_chains


def _write_identity_parquet(path, rows):
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Stage A6 requires pyarrow to preserve nullable effective_to") from exc
    table = pa.table({column: pa.array([row.get(column) for row in rows], type=pa.string())
                      for column in IDENTITY_HISTORY_COLUMNS})
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    pq.write_table(table, temporary, compression="snappy", version="2.6")
    temporary.replace(path)


def _candidate_row(event, decision="VERIFIED", reason=""):
    extra = {"decision": decision, "reason": reason}
    return {column: extra.get(column, event.get(column, "")) for column in CANDIDATE_COLUMNS}


def _report(manifest):
    m = manifest["metrics"]
    return "\n".join([
        "# Stage A6 — Historical Identity Recovery", "", f"- Run ID: `{manifest['run_id']}`",
        f"- Stage result: `{manifest['status']}`", "- Canonical mutations: `0`", "- Network requests: `0`", "",
        "## Kết quả", "", "| Metric | Count |", "|---|---:|",
        f"| Canonical securities | {m['total_securities']} |",
        f"| Independently reviewed candidate scope | {m['reviewed_scope_size']} |",
        f"| Evidence candidates | {m['evidence_candidates']} |",
        f"| Verified transition events | {m['verified_transition_events']} |",
        f"| Rejected transition events | {m['rejected_transition_events']} |",
        f"| Identities liberated from provisional | {m['identities_liberated']} |",
        f"| Exchange transfers verified | {m['exchange_transfers_verified']} |",
        f"| Ticker renames verified | {m['ticker_renames_verified']} |",
        f"| Provider symbol changes verified | {m['provider_symbol_changes_verified']} |",
        f"| Identity intervals | {m['total_intervals']} |", "", "## Fail-closed policy", "",
        "Không dùng company-name similarity hoặc current ticker để resolve entity. Evidence phải chỉ rõ canonical security_id, document local, SHA-256 và human review.",
        "", "## STOP", "", "Chờ audit Stage A6; không tự động chuyển sang Workstream B.",
    ])


def build_stage_a6(canonical, a1_artifact, a2_artifact, a3_artifact, a4_artifact, *, root,
                   evidence_path=None, review_manifest_path=None, candidate_scope_path=None,
                   output_dir=None, progress=None):
    root, base = Path(root).resolve(), Path(root).resolve() / "artifacts" / "data_enrichment"
    canonical = _inside(canonical, root / "data" / "canonical", "canonical baseline")
    stage_paths = [_inside(value, base, label) for value, label in
                   ((a1_artifact, "A1 artifact"), (a2_artifact, "A2 artifact"),
                    (a3_artifact, "A3 artifact"), (a4_artifact, "A4 artifact"))]
    paths = [canonical, *stage_paths]
    cm, m1, m2, m3, m4 = [read_json(path / "manifest.json") for path in paths]
    if cm.get("run_id") != canonical.name or cm.get("canonical_promotion_status") != "PASS" or cm.get("synthetic") is not False:
        raise ValueError("A6 requires the named real approved canonical baseline")
    if m1.get("status") != "PASS" or m1.get("canonical_run_id") != cm["run_id"]:
        raise ValueError("A6 requires matching A1 PASS evidence")
    if m2.get("status") != "PASS" or (m2.get("canonical_run_id"), m2.get("a1_run_id")) != (cm["run_id"], m1["run_id"]):
        raise ValueError("A6 requires matching A2 PASS evidence")
    if (m3.get("stage") != "A3 — Primary Provider Recovery Pilot" or m3.get("status") not in {"PASS", "PARTIAL"}
            or (m3.get("canonical_run_id"), m3.get("a1_run_id"), m3.get("a2_run_id")) != (cm["run_id"], m1["run_id"], m2["run_id"])):
        raise ValueError("A6 requires matching A3 evidence")
    if (m4.get("stage") != "A4 — Secondary Source Recovery Pilot" or m4.get("status") not in {"PASS", "PARTIAL"}
            or (m4.get("canonical_run_id"), m4.get("a1_run_id"), m4.get("a2_run_id"), m4.get("a3_run_id"))
            != (cm["run_id"], m1["run_id"], m2["run_id"], m3["run_id"])):
        raise ValueError("A6 requires matching A4 evidence")
    for path, manifest, label in zip(paths, (cm, m1, m2, m3, m4), ("canonical", "A1", "A2", "A3", "A4")):
        _verify_artifacts(path, manifest, label)
    cutoff_value = cm.get("collection_end")
    if not cutoff_value:
        raise ValueError("canonical manifest lacks collection_end cutoff")
    cutoff = _iso(cutoff_value, "canonical collection_end")
    securities = read_rows(canonical / "clean" / "securities.jsonl")
    accepted, rejected, document_hashes, evidence_input = load_evidence_bundle(
        evidence_path, review_manifest_path, candidate_scope_path, root=root,
        canonical_ids={row["security_id"] for row in securities}, cutoff=cutoff)
    history, confirmed, chain_rejections = build_identity_history(securities, accepted)
    rejected.extend(chain_rejections)
    rejected_ids = {row.get("candidate_id") for row in chain_rejections}
    verified = [row for row in accepted if row["candidate_id"] not in rejected_ids]
    # A security cannot simultaneously publish a recovered identity and retain
    # rejected evidence.  Collapse such mixed evidence to the fail-closed
    # REJECTED outcome and revoke every interval/event that would liberate it.
    rejected_security_ids = {row.get("security_id") for row in rejected if row.get("security_id")}
    mixed_security_ids = {row["security_id"] for row in verified} & rejected_security_ids
    if mixed_security_ids:
        rejected.extend(
            {**row, "decision": "REJECTED", "reason": "MIXED_VERIFIED_AND_REJECTED_EVIDENCE"}
            for row in verified if row["security_id"] in mixed_security_ids
        )
        verified = [row for row in verified if row["security_id"] not in mixed_security_ids]
        history = [row for row in history if row["security_id"] not in mixed_security_ids]
        confirmed.difference_update(mixed_security_ids)
    candidates = [_candidate_row(row) for row in verified]
    candidates.extend(_candidate_row(row, "REJECTED", row.get("reason", "REJECTED")) for row in rejected)
    candidates.sort(key=lambda row: row["candidate_id"])
    evidence_rows = [{"record_type": "IDENTITY_INTERVAL", **row} for row in history]
    evidence_rows.extend({"record_type": "TRANSITION_EVIDENCE", **row, "decision": "VERIFIED"} for row in verified)
    evidence_rows.extend({"record_type": "REJECTED_EVIDENCE", **row} for row in rejected)
    evidence_rows.extend({"record_type": "UNRESOLVED_IDENTITY", "security_id": row["security_id"],
                          "status": "UNRESOLVED", "reason": "NO_VERIFIED_IDENTITY_EFFECTIVE_INTERVAL"}
                         for row in securities if row["security_id"] not in confirmed)
    run_id = new_artifact_id("m1-a6-identity-recovery")
    output = base / run_id if output_dir is None else _inside(output_dir, base, "A6 output")
    if not output.name.startswith("m1-a6-identity-recovery-"):
        raise ValueError("A6 output directory must use m1-a6-identity-recovery prefix")
    run_id = output.name
    output.mkdir(parents=True, exist_ok=False)
    preserved_documents = {}
    if evidence_input:
        bundle = output / "identity_evidence_bundle"
        source_evidence = root / evidence_input["path"]
        source_review = root / evidence_input["review_manifest_path"]
        source_scope = root / evidence_input["candidate_scope_path"]
        atomic_write(bundle / ("evidence_input" + source_evidence.suffix.lower()), source_evidence.read_bytes())
        atomic_write(bundle / "review_manifest.json", source_review.read_bytes())
        atomic_write(bundle / ("candidate_scope" + source_scope.suffix.lower()), source_scope.read_bytes())
        for relative, sha256 in sorted(document_hashes.items()):
            source = _inside(source_evidence.parent / relative, source_evidence.parent, "evidence document")
            target = bundle / "documents" / (sha256 + source.suffix.lower())
            atomic_write(target, source.read_bytes())
            preserved_documents[relative] = target.relative_to(output).as_posix()
    _write_identity_parquet(output / "security_identity_history.parquet", history)
    atomic_write(output / "identity_recovery_candidates.csv", _csv_bytes(candidates, CANDIDATE_COLUMNS))
    write_rows(output / "identity_recovery_evidence.jsonl", evidence_rows)
    counts = Counter(row["recovery_type"] for row in verified)
    metrics = {"total_securities": len(securities), "reviewed_scope_size": len(evidence_input["scope_security_ids"]) if evidence_input else 0,
               "evidence_candidates": len(candidates),
               "verified_transition_events": len(verified), "rejected_transition_events": len(rejected),
               "identities_liberated": len(confirmed), "identities_provisional": len(securities) - len(confirmed),
               "exchange_transfers_verified": counts["EXCHANGE_TRANSFER"],
               "ticker_renames_verified": counts["TICKER_RENAME"],
               "provider_symbol_changes_verified": counts["PROVIDER_SYMBOL_CHANGE"],
               "total_intervals": len(history)}
    scope_complete = False
    if evidence_input:
        verified_ids = {row["security_id"] for row in verified}
        rejected_ids_by_security = {row.get("security_id") for row in rejected if row.get("security_id")}
        actual_dispositions = {
            security_id: (
                "TRANSITION_ASSERTED" if security_id in verified_ids and security_id not in rejected_ids_by_security
                else "REJECTED" if security_id in rejected_ids_by_security and security_id not in verified_ids
                else "NO_VERIFIED_TRANSITION" if security_id not in verified_ids and security_id not in rejected_ids_by_security
                else "MIXED_INVALID_OUTCOME"
            )
            for security_id in evidence_input["scope_security_ids"]
        }
        scope_complete = all(
            actual_dispositions[item["security_id"]] == item["disposition"]
            for item in evidence_input["scope_dispositions"]
        )
    status = "PASS" if evidence_input and scope_complete else "PARTIAL"
    manifest = {"run_id": run_id, "stage": STAGE, "status": status, "created_at": now(),
                "git_commit": _git_commit(root), "config_hash": digest(encoded({"schema": "2.0.0", "evidence": evidence_input, "documents": document_hashes})),
                "canonical_run_id": cm["run_id"], "a1_run_id": m1["run_id"], "a2_run_id": m2["run_id"],
                "a3_run_id": m3["run_id"], "a4_run_id": m4["run_id"],
                "input_artifact_ids": [cm["run_id"], m1["run_id"], m2["run_id"], m3["run_id"], m4["run_id"]],
                "input_hashes": {label: digest((path / "manifest.json").read_bytes()) for label, path in
                                 zip(("canonical_manifest", "a1_manifest", "a2_manifest", "a3_manifest", "a4_manifest"), paths)},
                "identity_evidence_input": evidence_input, "evidence_document_hashes": document_hashes,
                "preserved_evidence_documents": preserved_documents,
                "network_requests": 0, "canonical_mutations": 0, "synthetic_rows": 0, "imputed_rows": 0,
                "canonical_cutoff": cutoff.isoformat(), "scope_review_complete": scope_complete,
                "metrics": metrics, "limitations": ([] if evidence_input and scope_complete else
                    ["Reviewed candidate scope is absent or incomplete; unresolved identities are not emitted as historical intervals"])}
    atomic_write(output / "stage_a6_report.md", _report(manifest).encode("utf-8"))
    manifest["artifacts"] = {path.relative_to(output).as_posix(): digest(path.read_bytes())
                             for path in sorted(output.rglob("*")) if path.is_file()}
    write_json(output / "manifest.json", manifest)
    if progress:
        progress(f"A6={status} verified={len(verified)} rejected={len(rejected)} network=0")
    return output, manifest
