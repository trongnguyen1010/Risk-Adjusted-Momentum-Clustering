"""Semiautomatic candidate/review workflow, isolated from market/M2/M3 engines."""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from delta_t1.contracts import validate_rows
from . import corporate_actions_v1 as base
from .corporate_action_sources import (
    PublicTransport, SourceLimitation, discover_vsdc, hnx_market_context, now, parse_hnx, parse_vsdc, sha,
)

VERSION = "1.1.0"
REVIEW_EDITABLE = ("review_status", "reviewed_by", "reviewed_at", "review_decision", "review_note")
QUEUE_FIELDS = ("candidate_id", "ticker", "event_type", "ex_date", "review_reason",
                "candidate_value", "conflicting_value", "primary_source_url", "secondary_source_url",
                "recommended_check", *REVIEW_EDITABLE)
CANDIDATE_FIELDS = ("candidate_id", "ticker", "security_id", "exchange", "event_type", "ex_date",
                    "record_date", "verification_status", "confidence_score", "review_reason",
                    "primary_source_url", "secondary_source_url", "raw_terms", "normalized_terms",
                    "candidate_json")
SOFT_REVIEW = {"SOURCE_CONFLICT", "DUPLICATE_SUSPECTED", "MANUAL_EVIDENCE_INPUT",
               "SOURCE_PUBLIC_TIME_UNVERIFIED", "LATE_OR_INTRADAY_KNOWLEDGE_PIT_REVIEW", "RATIO_PARSE_AMBIGUITY"}
REASONS = {"REQUIRED_EVIDENCE": "MISSING_REQUIRED_TERM", "TERM_CONFLICT": "SOURCE_CONFLICT",
           "HISTORICAL_IDENTITY_UNVERIFIED": "CROSS_SOURCE_IDENTITY_CONFLICT",
           "UNUSUAL_RATIO_GT_100_PERCENT": "RATIO_PARSE_AMBIGUITY",
           "OTHER_REQUIRES_REVIEW": "OTHER_MANUAL_REVIEW", "AUTHORITATIVE_SOURCE_REQUIRED": "SOURCE_AUTHORITY_UNCLEAR",
           "SOURCE_AUTHORITY_URL_MISMATCH": "SOURCE_AUTHORITY_UNCLEAR"}


def dump_jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_scope(path):
    rows = base.read_csv(path)
    if not rows or any(not {"ticker", "exchange"} <= r.keys() for r in rows):
        raise ValueError("SCOPE: nonempty ticker,exchange CSV required; identity may remain unresolved")
    for row in rows:
        if not re.fullmatch(r"[A-Z0-9]{2,12}", row["ticker"]) or row["exchange"] not in {"HOSE", "HNX", "UPCOM"}:
            raise ValueError("SCOPE: invalid ticker/exchange")
        if row.get("identity_status") == "VERIFIED":
            try:
                start, end = row["valid_from"], row["valid_to"]
                if not (date.fromisoformat(start).isoformat() == start < end == date.fromisoformat(end).isoformat()
                        and row.get("security_id") and row.get("isin") and base.valid_url(row.get("identity_source_url"))):
                    raise ValueError("identity interval/evidence")
            except (KeyError, ValueError):
                raise ValueError("SCOPE: VERIFIED requires security_id, ISIN, valid [from,to) interval and source URL") from None
    if len({(r.get("security_id", ""), r["ticker"], r["exchange"], r.get("valid_from"), r.get("valid_to")) for r in rows}) != len(rows):
        raise ValueError("SCOPE: duplicate interval")
    return rows


def resolve_identity(row, scope):
    point = row.get("ex_date") or row.get("record_date")
    matches = [s for s in scope if s["ticker"] == row.get("ticker") and s["exchange"] == row.get("exchange")
               and point and s.get("valid_from", "9999") <= point < s.get("valid_to", "0000")]
    verified = [s for s in matches if s.get("identity_status") == "VERIFIED" and s.get("security_id")
                and base.valid_url(s.get("identity_source_url")) and s.get("isin")
                and (not row.get("isin") or row.get("isin") == s["isin"])]
    if len(verified) == 1:
        return verified[0]
    # Keep unverified ID as a candidate reference only; never infer from ticker.
    fallback = [s for s in scope if s["ticker"] == row.get("ticker") and s["exchange"] == row.get("exchange")]
    return {"security_id": fallback[0].get("security_id", "") if len(fallback) == 1 else "",
            "identity_status": "UNVERIFIED", "identity_source_url": ""}


def combine(raw):
    """Unique matching HNX calendar may add explicit ex-date; preserve later knowledge."""
    calendars = [r for r in raw if r.get("parser") == "hnx-calendar-v1"]
    used, result = set(), []
    for row in [r for r in raw if r.get("parser") != "hnx-calendar-v1"]:
        row = dict(row)
        matches = [r for r in calendars if all(row.get(f) and row.get(f) == r.get(f)
                   for f in ("ticker", "exchange", "event_type", "record_date"))]
        if len(matches) == 1:
            other = matches[0]
            used.add(id(other))
            row["secondary_source_type"], row["secondary_source_url"] = "HNX", other["primary_source_url"]
            row["evidence"] = row.get("evidence", []) + other["evidence"]
            row["raw_terms"] += "\nHNX cross-check: " + other["raw_terms"]
            row["field_sources"] = {"ex_date": other["primary_source_url"]}
            for field in ("ex_date", "payment_date"):
                if row.get(field) and other.get(field) and row[field] != other[field]:
                    row.setdefault("parser_issues", []).append("SOURCE_CONFLICT")
                    row.setdefault("field_conflicts", {})[field] = {"candidate_value": row[field], "conflicting_value": other[field],
                                                                   "source_url": other["primary_source_url"]}
                elif not row.get(field) and other.get(field):
                    row[field] = other[field]
                    if not row.get("available_at") or base.timestamp(other["available_at"]) > base.timestamp(row["available_at"]):
                        row["available_at"] = other["available_at"]
                        row["available_at_evidence"] = "LATEST_REQUIRED_FIELD_FIRST_OBSERVED_AT"
                    row.setdefault("parser_issues", []).extend(other["parser_issues"])
        elif len(matches) > 1:
            row.setdefault("parser_issues", []).append("DUPLICATE_SUSPECTED")
        result.append(row)
    return result + [r for r in calendars if id(r) not in used]


def classify(raw, scope, created_at):
    result, seen = [], {}
    for source in combine(raw):
        identity = resolve_identity(source, scope)
        stable = {k: source.get(k) for k in ("primary_source_url", "ticker", "exchange", "event_type",
                  "record_date", "ex_date", "raw_terms", "revision_status", *base.NUMBERS, "currency")}
        candidate_id = "CA-" + sha(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode())[:24]
        exact_key = (source.get("primary_source_url"), source.get("source_hash"), source.get("event_type"),
                     source.get("record_date"), source.get("ex_date"), source.get("raw_terms"),
                     *(source.get(k) for k in (*base.NUMBERS, "currency")))
        if exact_key in seen:
            seen[exact_key]["duplicate_evidence_count"] += 1
            continue
        event = dict.fromkeys(base.FIELDS, "")
        event.update({k: v for k, v in source.items() if k in event})
        event.update({k: v for k, v in identity.items() if k in event})
        event.update(event_id=candidate_id, event_group_id="CAG-" + sha(json.dumps([
            event.get("security_id"), event.get("ticker"), event.get("exchange"),
            event.get("ex_date") or event.get("record_date")]).encode())[:24],
                     schema_version="1.0.0", created_at=created_at,
                     verification_status="VERIFIED", verified_by="AUTOMATIC_CONTRACT_CHECK_ONLY",
                     verified_at=created_at, revision_status=source.get("revision_status", "ORIGINAL"))
        if event.get("event_type") == "OTHER" and not event.get("notes"):
            event["notes"] = "Thông báo chưa phân loại chắc chắn; cần đọc source evidence."
        check = base.validate([event])["records"][0]
        reasons = set(source.get("parser_issues", []))
        invalid = False
        for issue in check["issues"]:
            code, field = issue["code"], issue["field"]
            if code == "REQUIRED_EVIDENCE" and field == "ex_date":
                reasons.add("MISSING_EX_DATE")
            elif code == "REQUIRED_EVIDENCE" and field == "available_at":
                reasons.add("MISSING_AVAILABLE_AT")
            elif code in {"SCHEMA_VALUE", "REQUIRED_FIELD"} and field == "security_id":
                reasons.add("CROSS_SOURCE_IDENTITY_CONFLICT")
            else:
                reasons.add(REASONS.get(code, code))
                invalid |= issue["severity"] == "INVALID"
        normalized = check["normalized"]
        normalized["verified_by"], normalized["verified_at"] = None, None
        status = "INVALID" if invalid else "MANUAL_REVIEW" if reasons else "AUTO_VERIFIED"
        candidate = dict(candidate_id=candidate_id, event=normalized, base_input=event,
                         verification_status=status, confidence_score=0.0 if invalid else .4 if reasons else .99 if source.get("secondary_source_url") else .95,
                         review_reasons=sorted(reasons), validation_issues=check["issues"],
                         source=source, duplicate_evidence_count=1)
        result.append(candidate)
        seen[exact_key] = candidate
    groups = defaultdict(list)
    for row in result:
        e = row["event"]
        groups[(e.get("security_id"), e.get("ticker"), e.get("exchange"), e.get("ex_date") or e.get("record_date"), e.get("event_type"))].append(row)
    for members in groups.values():
        if len(members) > 1:
            signatures = {tuple(r["event"].get(k) for k in (*base.NUMBERS, "record_date", "payment_date", "currency")) for r in members}
            reason = "SOURCE_CONFLICT" if len(signatures) > 1 else "DUPLICATE_SUSPECTED"
            for row in members:
                row["review_reasons"] = sorted(set(row["review_reasons"]) | {reason})
                if row["verification_status"] != "INVALID":
                    row["verification_status"] = "MANUAL_REVIEW"
                row["confidence_score"] = min(row["confidence_score"], .4)
    revisions = [r for r in result if r["event"].get("revision_status") != "ORIGINAL" or r["event"].get("revision_of_event_id")]
    for revision in revisions:
        urls = revision["source"].get("revision_reference_urls", [])
        reference = revision["event"].get("revision_of_event_id")
        peers = [r for r in result if r is not revision and all(r["event"].get(f) == revision["event"].get(f) for f in ("ticker", "exchange"))]
        targets = [r for r in peers if r["source"].get("primary_source_url") in urls or r["candidate_id"] == reference]
        # An unlinked correction cannot establish which original remains effective.
        for row in targets or peers:
            row["review_reasons"] = sorted(set(row["review_reasons"]) | {"REVISION_OR_CORRECTION_DETECTED"})
            if row["verification_status"] != "INVALID":
                row["verification_status"] = "MANUAL_REVIEW"
    # An unresolved mixed component prevents automatic promotion of its siblings.
    mixed = defaultdict(list)
    for row in result:
        mixed[row["event"]["event_group_id"]].append(row)
    for members in mixed.values():
        if len({r["event"]["event_type"] for r in members}) > 1 and any(r["review_reasons"] for r in members):
            for row in members:
                row["review_reasons"] = sorted(set(row["review_reasons"]) | {"MIXED_EVENT_AMBIGUITY"})
                if row["verification_status"] != "INVALID":
                    row["verification_status"] = "MANUAL_REVIEW"
    for row in result:
        row["event"]["verification_status"] = row["verification_status"]
        if row["verification_status"] == "MANUAL_REVIEW":
            row["confidence_score"] = min(row["confidence_score"], .4)
    return result


def queue_rows(candidates):
    result = []
    for candidate in candidates:
        if candidate["verification_status"] == "AUTO_VERIFIED":
            continue
        e = candidate["event"]
        peers = [other for other in candidates if other["candidate_id"] != candidate["candidate_id"]
                 and all(other["event"].get(f) == e.get(f) for f in ("ticker", "exchange", "ex_date", "event_type"))]
        result.append(dict(candidate_id=candidate["candidate_id"], ticker=e.get("ticker"),
                           event_type=e.get("event_type"), ex_date=e.get("ex_date"),
                           review_reason=";".join(candidate["review_reasons"]),
                           candidate_value=json.dumps(e, ensure_ascii=False, sort_keys=True),
                           conflicting_value=json.dumps({"other_candidates": [{"candidate_id": p["candidate_id"], "terms": p["event"]} for p in peers],
                                                         "field_conflicts": candidate["source"].get("field_conflicts", {})}, ensure_ascii=False, sort_keys=True),
                           primary_source_url=e.get("primary_source_url"),
                           secondary_source_url=candidate["source"].get("secondary_source_url", ""),
                           recommended_check="Kiểm ticker/identity interval, loại quyền, năm mốc, terms và mọi source; chọn USE_CANDIDATE hoặc REJECT_CANDIDATE. Thiếu term/identity cần manual supplement; revisions giữ review.",
                           review_status="PENDING", reviewed_by="", reviewed_at="", review_decision="", review_note=""))
    return result


def write_manifest(root, extra):
    extra.update(schema_version=VERSION, q11_status="STILL_OPEN", price_return_adjusted_series="NOT_BUILT",
                 code_hashes={p.name: base.digest(p) for p in (Path(__file__), Path(__file__).with_name("corporate_action_sources.py"), Path(base.__file__))},
                 schema_hash=base.digest(Path(__file__).parents[1] / "schemas/corporate_actions_collection_v1.json"),
                 files={p.relative_to(root).as_posix(): base.digest(p) for p in sorted(root.rglob("*")) if p.is_file()})
    base.write_new(root / "manifest.json", base.json_text(extra))
    return extra


def collect(scope_path, output, start, end, max_pages=2, max_details=10, max_requests=30,
            sources=("VSDC", "HNX"), manual_input=None, dry_run=False, transport_factory=PublicTransport, transport_options=None):
    if date.fromisoformat(start).isoformat() != start or date.fromisoformat(end).isoformat() != end or start > end:
        raise ValueError("invalid collection window")
    if not 1 <= max_pages <= 20 or not 1 <= max_details <= 100 or not 1 <= max_requests <= 1000:
        raise ValueError("invalid collection budget")
    scope = load_scope(scope_path)
    if not set(sources) <= {"VSDC", "HNX"}:
        raise ValueError("source not implemented; use manual evidence fallback")
    if output.exists():
        raise ValueError("OUTPUT_EXISTS: use a new collection run")
    plan = dict(work_unit="BUILD_SEMIAUTOMATIC_CORPORATE_ACTIONS_V1_COLLECTION_PIPELINE", start=start, end=end,
                sources=list(sources), max_pages=max_pages, max_details=max_details, max_requests=max_requests,
                scope_sha256=base.digest(scope_path), scope=scope, created_at=now(), dry_run=dry_run,
                transport_options=transport_options or {})
    if dry_run:
        return plan | {"status": "DRY_RUN", "network_requests": 0}
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(scope_path, output / "scope.csv")
    if base.digest(output / "scope.csv") != plan["scope_sha256"]:
        raise ValueError("scope changed during collection")
    base.write_new(output / "plan.json", base.json_text(plan))
    client, raw, checks, limitations = transport_factory(output, max_requests=max_requests, **(transport_options or {})), [], [], []
    for ticker in dict.fromkeys(s["ticker"] for s in scope):
        first_request = len(client.requests)
        if "VSDC" in sources:
            try:
                links, check = discover_vsdc(client, ticker, max_pages, max_details)
                checks.append(check)
                for url in links:
                    try:
                        html, evidence = client.fetch(url)
                        parsed = parse_vsdc(html, evidence)
                        for row in parsed:
                            if row.get("ticker") != ticker:
                                row.setdefault("parser_issues", []).append("CROSS_SOURCE_IDENTITY_CONFLICT")
                        raw.extend(parsed)
                    except SourceLimitation as exc:
                        limitations.append(dict(ticker=ticker, source="VSDC", url=url, reason=str(exc)))
                        if "SOURCE_ACCESS_LIMITATION" in str(exc) or "BUDGET" in str(exc):
                            break
            except SourceLimitation as exc:
                limitations.append(dict(ticker=ticker, source="VSDC", reason=str(exc)))
        if "HNX" in sources and any(s["ticker"] == ticker and s["exchange"] in {"HNX", "UPCOM"} for s in scope):
            try:
                url = f"https://www.hnx.vn/vi-vn/m-tim-kiem-{ticker}.html"
                for page in range(1, max_pages+1):
                    body = None if page == 1 else urlencode(dict(StockCode=ticker, MarketCode=market_code, Page=page)).encode()
                    html, evidence = client.fetch(url if page == 1 else "https://www.hnx.vn/ModuleMobile/MobileIssuer/ChangePageTHQ",
                                                  body, "application/x-www-form-urlencoded")
                    if page == 1:
                        market_code, exchange = hnx_market_context(html, ticker)
                        if not any(s["ticker"] == ticker and s["exchange"] == exchange for s in scope):
                            raise SourceLimitation("HNX_SCOPE_EXCHANGE_CONFLICT")
                    rows, last = parse_hnx(html, evidence, ticker, exchange)
                    raw.extend(rows)
                    if last <= page:
                        break
                checks.append(dict(ticker=ticker, source="HNX", status="PARTIAL", reason="CALENDAR_NOT_FULL_ANNOUNCEMENT_OR_REVISION_ARCHIVE"))
            except SourceLimitation as exc:
                limitations.append(dict(ticker=ticker, source="HNX", reason=str(exc)))
        for request in client.requests[first_request:]:
            request["ticker"] = ticker
    if manual_input:
        shutil.copyfile(manual_input, output / "manual_input.csv")
        for row in base.read_csv(output / "manual_input.csv", base.FIELDS):
            raw.append(row | dict(parser="manual-input-v1", parser_issues=["MANUAL_EVIDENCE_INPUT"], evidence=[],
                                 available_at=row.get("available_at"), isin=next((s.get("isin", "") for s in scope if s["ticker"] == row["ticker"] and s.get("security_id") == row["security_id"]), "")))
    base.write_new(output / "raw_candidates.jsonl", dump_jsonl(raw))
    candidates = store_candidates(output, raw, scope, start, end, now())
    base.write_new(output / "requests.json", base.json_text(client.requests))
    base.write_new(output / "source_checks.json", base.json_text(dict(checks=checks, limitations=limitations)))
    return write_manifest(output, dict(status="PARTIAL", artifact_type="corporate-action-collection",
                                      network_requests=len(client.requests), candidate_count=len(candidates),
                                      classifications=dict(Counter(r["verification_status"] for r in candidates)),
                                      live_source_validation="BLOCKED" if not raw and limitations else "PARTIAL"))


def store_candidates(output, raw, scope, start, end, created_at):
    all_candidates = classify(raw, scope, created_at)
    outside = [r for r in all_candidates if r["event"].get("ex_date") and not start <= r["event"]["ex_date"] <= end]
    candidates = [r for r in all_candidates if r not in outside]
    base.write_new(output / "out_of_window.jsonl", dump_jsonl(outside))
    base.write_new(output / "candidates.jsonl", dump_jsonl(candidates))
    csv_rows = []
    for row in candidates:
        e = row["event"]
        csv_rows.append({k: e.get(k) for k in ("ticker", "security_id", "exchange", "event_type", "ex_date", "record_date", "primary_source_url", "raw_terms")} | dict(
            candidate_id=row["candidate_id"], verification_status=row["verification_status"], confidence_score=row["confidence_score"],
            review_reason=";".join(row["review_reasons"]), secondary_source_url=row["source"].get("secondary_source_url", ""),
            normalized_terms=json.dumps({k: e.get(k) for k in base.NUMBERS}, sort_keys=True), candidate_json=json.dumps(row, ensure_ascii=False, sort_keys=True)))
    base.write_new(output / "corporate_actions_candidates.csv", base.csv_text(CANDIDATE_FIELDS, csv_rows))
    base.write_new(output / "manual_review_queue.csv", base.csv_text(QUEUE_FIELDS, queue_rows(candidates)))
    return candidates


def verify_collection_files(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("artifact_type") != "corporate-action-collection" or manifest.get("schema_version") != VERSION:
        raise ValueError("unsupported collection artifact")
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or base.digest(path) != expected:
            raise ValueError("COLLECTION_CHECKSUM_MISMATCH: " + name)
    return manifest


def replay_collection(root, output):
    """Reclassify archived parsed evidence in a new run; no network or overwrite."""
    original = verify_collection_files(root)
    if output.exists():
        raise ValueError("OUTPUT_EXISTS")
    output.mkdir(parents=True, exist_ok=False)
    for name in original["files"]:
        if name.startswith("raw/") or name in {"raw_candidates.jsonl", "scope.csv", "requests.json", "source_checks.json", "manual_input.csv"}:
            dest = output / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, dest)
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    plan.update(replay_of_manifest_sha256=base.digest(root / "manifest.json"), created_at=now())
    base.write_new(output / "plan.json", base.json_text(plan))
    rows = store_candidates(output, read_jsonl(output / "raw_candidates.jsonl"), load_scope(output / "scope.csv"), plan["start"], plan["end"], now())
    return write_manifest(output, dict(artifact_type="corporate-action-collection", status="PARTIAL",
                                      network_requests=0, reused_response_count=len(json.loads((output / "requests.json").read_text(encoding="utf-8"))),
                                      candidate_count=len(rows), classifications=dict(Counter(r["verification_status"] for r in rows)),
                                      replay_of_manifest_sha256=plan["replay_of_manifest_sha256"], live_source_validation="REPLAYED_OFFLINE"))


def load_collection(root):
    verify_collection_files(root)
    # Re-derive classifications from archived inputs; never trust edited statuses.
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    existing = read_jsonl(root / "candidates.jsonl")
    regenerated = classify(read_jsonl(root / "raw_candidates.jsonl"), load_scope(root / "scope.csv"),
                           existing[0]["base_input"]["created_at"] if existing else now())
    regenerated = [r for r in regenerated if not r["event"].get("ex_date") or plan["start"] <= r["event"]["ex_date"] <= plan["end"]]
    if existing != regenerated:
        raise ValueError("CANDIDATE_REDERIVATION_MISMATCH")
    return existing, plan


def decisions(candidates, reviews=None):
    expected = {r["candidate_id"]: r for r in queue_rows(candidates)}
    supplied = {}
    if reviews:
        for row in base.read_csv(reviews, QUEUE_FIELDS):
            key = row["candidate_id"]
            if key not in expected or key in supplied:
                raise ValueError("REVIEW: unknown/duplicate candidate_id")
            if any(str(expected[key].get(k) or "") != row[k] for k in QUEUE_FIELDS if k not in REVIEW_EDITABLE):
                raise ValueError("REVIEW: candidate evidence fields edited; use manual supplement in a new run")
            if row["review_status"] not in {"PENDING", "APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"}:
                raise ValueError("REVIEW: invalid review_status")
            if row["review_status"] in {"APPROVED", "REJECTED"}:
                if not all(row[k].strip() for k in ("reviewed_by", "reviewed_at", "review_decision", "review_note")):
                    raise ValueError("REVIEW: signed decision and note required")
                base.timestamp(row["reviewed_at"])
                expected_decision = "USE_CANDIDATE" if row["review_status"] == "APPROVED" else "REJECT_CANDIDATE"
                if row["review_decision"] != expected_decision:
                    raise ValueError("REVIEW: decision must be " + expected_decision)
            supplied[key] = row
    output = []
    for candidate in candidates:
        row = dict(candidate)
        review = supplied.get(row["candidate_id"], expected.get(row["candidate_id"], {}))
        row["review"] = review
        if review.get("review_status") in {"APPROVED", "REJECTED"}:
            if base.timestamp(review["reviewed_at"]) < base.timestamp(row["event"]["created_at"]):
                raise ValueError("REVIEW: reviewed_at precedes collection")
            if review["review_status"] == "REJECTED":
                row["verification_status"] = "REJECTED"
            elif row["verification_status"] != "INVALID" and set(row["review_reasons"]) <= SOFT_REVIEW:
                row["verification_status"] = "MANUALLY_VERIFIED"
        output.append(row)
    # Unresolved alternatives or mixed components block promotion of the whole group.
    groups = defaultdict(list)
    for row in output:
        groups[row["event"]["event_group_id"]].append(row)
    for members in groups.values():
        active = [r for r in members if r["verification_status"] != "REJECTED"]
        type_counts = Counter(r["event"]["event_type"] for r in active)
        unresolved = any(r["verification_status"] not in {"AUTO_VERIFIED", "MANUALLY_VERIFIED"} for r in active)
        if unresolved or any(n > 1 for n in type_counts.values()):
            for row in active:
                if row["verification_status"] in {"AUTO_VERIFIED", "MANUALLY_VERIFIED"}:
                    row["verification_status"] = "MANUAL_REVIEW"
                    row["review_reasons"] = sorted(set(row["review_reasons"]) | {"UNRESOLVED_EVENT_GROUP"})
    return output


def build_collection(root, output, reviews=None):
    review_hash = base.digest(reviews) if reviews else None
    candidates, plan = load_collection(root)
    resolved = decisions(candidates, reviews)
    if reviews and base.digest(reviews) != review_hash:
        raise ValueError("REVIEW_CHANGED_DURING_BUILD")
    if output.exists():
        raise ValueError("OUTPUT_EXISTS: canonical run is immutable")
    verified = []
    for row in resolved:
        if row["verification_status"] not in {"AUTO_VERIFIED", "MANUALLY_VERIFIED"}:
            continue
        e, source, review = dict(row["event"]), row["source"], row["review"]
        e.update(schema_version=VERSION, verification_status=row["verification_status"],
                 secondary_source_type=source.get("secondary_source_type"), secondary_source_url=source.get("secondary_source_url"),
                 normalized_terms={k: e.get(k) for k in base.NUMBERS}, confidence_score=row["confidence_score"],
                 review_status=review.get("review_status", "NOT_REQUIRED"), reviewed_by=review.get("reviewed_by") or None,
                 reviewed_at=review.get("reviewed_at") or None, review_decision=review.get("review_decision") or None,
                 review_note=review.get("review_note") or None, updated_at=review.get("reviewed_at") or e["created_at"],
                 source_evidence=source.get("evidence", []), field_sources=source.get("field_sources", {}),
                 verification_limitations=row["review_reasons"], revision_number=None, is_latest_revision=None)
        verified.append(e)
    validate_rows("corporate_actions_collection_v1", verified)
    output.mkdir(parents=True, exist_ok=False)
    base.write_new(output / "corporate_actions_v1.jsonl", dump_jsonl(verified))
    base.write_new(output / "candidate_decisions.jsonl", dump_jsonl(resolved))
    if reviews:
        shutil.copyfile(reviews, output / "reviews.csv")
        if base.digest(output / "reviews.csv") != review_hash:
            raise ValueError("REVIEW_CHANGED_DURING_BUILD: incomplete run retained")
    base.write_new(output / "collection_manifest.json", (root / "manifest.json").read_text(encoding="utf-8"))
    return write_manifest(output, dict(artifact_type="corporate-actions-v1-canonical", collection_path=str(root.resolve()),
                                      collection_manifest_sha256=base.digest(root / "manifest.json"),
                                      verified_event_count=len(verified), status="PASS" if all(r["verification_status"] in {"AUTO_VERIFIED", "MANUALLY_VERIFIED", "REJECTED"} for r in resolved) else "PARTIAL",
                                      reviews_sha256=review_hash,
                                      required_start_date=plan["start"], required_end_date=plan["end"]))


def coverage(root, reviews=None, attestation=None):
    review_hash = base.digest(reviews) if reviews else None
    attestation_hash = base.digest(attestation) if attestation else None
    candidates, plan = load_collection(root)
    resolved = decisions(candidates, reviews)
    scope, checks = load_scope(root / "scope.csv"), json.loads((root / "source_checks.json").read_text(encoding="utf-8"))
    attest = base.read_csv(attestation, base.COVERAGE_FIELDS) if attestation else []
    rows = []
    for s in scope:
        own = [r for r in resolved if r["event"].get("ticker") == s["ticker"] and r["event"].get("exchange") == s["exchange"]
               and (r["event"].get("security_id") or "") == s.get("security_id", "")]
        verified = sum(r["verification_status"] in {"AUTO_VERIFIED", "MANUALLY_VERIFIED"} for r in own)
        manual = sum(r["verification_status"] == "MANUAL_REVIEW" for r in own)
        invalid = sum(r["verification_status"] == "INVALID" for r in own)
        checked = {source: any(c["ticker"] == s["ticker"] and c["source"] == source for c in checks["checks"]) for source in ("VSDC", "HNX", "HOSE", "ISSUER_IR")}
        confirmation = [r for r in attest if all((r.get(k) or "") == (s.get(k) or "") for k in ("ticker", "security_id", "exchange"))]
        confirmed = False
        if len(confirmation) == 1:
            a = confirmation[0]
            try:
                confirmed = (a["review_status"] == "REVIEWED" and a["reviewed_start_date"] <= plan["start"] <= plan["end"] <= a["reviewed_end_date"]
                             and date.fromisoformat(a["reviewed_start_date"]).isoformat() == a["reviewed_start_date"]
                             and date.fromisoformat(a["reviewed_end_date"]).isoformat() == a["reviewed_end_date"]
                             and base.timestamp(a["last_checked_at"]).date() >= date.fromisoformat(plan["end"])
                             and a["reviewed_event_types"] == "ALL_V1" and bool(a["reviewer"].strip()) and bool(a["coverage_evidence"].strip())
                             and base.authoritative_url(a["primary_source_type"], a["primary_source_url"]))
            except ValueError:
                confirmed = False
        status = "MANUAL_REVIEW_REQUIRED" if manual or invalid or len(confirmation) > 1 else "HAS_VERIFIED_EVENTS" if verified else "NOT_YET_REVIEWED"
        if confirmed and not manual and not invalid:
            status = "HAS_VERIFIED_EVENTS" if verified else "NO_EVENT_CONFIRMED"
        complete = confirmed and not manual and not invalid and s.get("identity_status") == "VERIFIED"
        rows.append(dict(ticker=s["ticker"], security_id=s.get("security_id"), exchange=s["exchange"],
                         required_start_date=plan["start"], required_end_date=plan["end"],
                         source_checked_vsd=checked["VSDC"], source_checked_hose=checked["HOSE"], source_checked_hnx=checked["HNX"], source_checked_ir=checked["ISSUER_IR"],
                         candidate_event_count=len(own), verified_event_count=verified, manual_review_count=manual,
                         invalid_count=invalid, rejected_count=sum(r["verification_status"] == "REJECTED" for r in own),
                         last_checked_at=max((r["fetched_at"] for r in json.loads((root / "requests.json").read_text(encoding="utf-8")) if r.get("ticker") == s["ticker"]), default=None),
                         coverage_status=status, completeness_status="COVERAGE_COMPLETE" if complete else "COVERAGE_INCOMPLETE"))
    unscoped = [r["candidate_id"] for r in resolved if not any(r["event"].get("ticker") == s["ticker"] and r["event"].get("exchange") == s["exchange"]
                 and (r["event"].get("security_id") or "") == s.get("security_id", "") for s in scope)]
    if reviews and base.digest(reviews) != review_hash or attestation and base.digest(attestation) != attestation_hash:
        raise ValueError("INPUT_CHANGED_DURING_COVERAGE")
    return dict(rows=rows, coverage_pass=bool(rows) and not unscoped and all(r["completeness_status"] == "COVERAGE_COMPLETE" for r in rows),
                unscoped_candidates=unscoped, source_limitations=checks["limitations"], q11_status="STILL_OPEN",
                m3_exact_runtime_window="MANUAL_REVIEW_REQUIRED", collection_manifest_sha256=base.digest(root / "manifest.json"),
                reviews_sha256=review_hash, attestation_sha256=attestation_hash)
