"""Offline, manual-first Q11 collection. No prices, network or model imports."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from delta_t1.contracts import coerce, schema

TABLE = "corporate_actions_v1"
VERSION = "1.0.0"
FIELDS = tuple(k for k in schema(TABLE)["fields"] if k != "normalization_inputs")
TERMS = {
    "CASH_DIVIDEND": ("cash_dividend_per_share", "currency"),
    "STOCK_DIVIDEND": ("stock_dividend_ratio",),
    "BONUS_SHARE": ("bonus_ratio",),
    "STOCK_SPLIT": ("split_multiplier",),
    "REVERSE_SPLIT": ("split_multiplier",),
    "RIGHTS_ISSUE": ("rights_ratio", "rights_subscription_price", "currency"),
    "OTHER": ("notes",),
}
NUMBERS = ("cash_dividend_per_share", "stock_dividend_ratio", "bonus_ratio",
           "split_multiplier", "rights_ratio", "rights_subscription_price")
RATIOS = {"stock_dividend_ratio", "bonus_ratio", "rights_ratio"}
AUTHORITIES = {"VSDC", "HOSE", "HNX", "ISSUER_IR"}
OFFICIAL_DOMAINS = {"VSDC": ("vsdc.vn", "vsd.vn"), "HOSE": ("hsx.vn", "hose.vn"),
                    "HNX": ("hnx.vn",)}
COVERAGE_FIELDS = (
    "security_id", "ticker", "exchange", "reviewed_start_date", "reviewed_end_date",
    "review_status", "reviewed_event_types", "primary_source_type", "primary_source_url",
    "coverage_evidence", "reviewer", "last_checked_at", "notes",
)


def read_csv(path: Path, fields: tuple[str, ...] | None = None) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        if not header or len(header) != len(set(header)):
            raise ValueError("CSV_HEADER: missing or duplicate column")
        if fields is not None and set(header) != set(fields):
            raise ValueError(f"CSV_HEADER: missing={sorted(set(fields)-set(header))}; "
                             f"unknown={sorted(set(header)-set(fields))}")
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("CSV_WIDTH: quote commas/newlines inside cells")
    return rows


def csv_text(fields, rows) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as stream:
        stream.write(content)


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(value: str) -> datetime:
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
        raise ValueError("timestamp must include date, time and timezone")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone required")
    return result


def valid_url(value) -> bool:
    try:
        parsed = urlsplit(value or "")
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username
    except ValueError:
        return False


def authoritative_url(source_type, value) -> bool:
    if source_type not in AUTHORITIES or not valid_url(value):
        return False
    domains = OFFICIAL_DOMAINS.get(source_type)
    hostname = urlsplit(value).hostname.lower()
    return domains is None or any(hostname == d or hostname.endswith("." + d) for d in domains)


def number(value: str, field: str, semantics: str) -> float:
    """Percent is explicit; OLD:NEW requires an explicit source interpretation."""
    value = value.strip()
    try:
        if ":" in value:
            if field not in RATIOS | {"split_multiplier"} or semantics != "OLD:NEW":
                raise ValueError("colon ratio requires ratio_semantics=OLD:NEW")
            old, new = [Decimal(part.strip()) for part in value.split(":")]
            if not old.is_finite() or not new.is_finite() or old <= 0 or new <= 0:
                raise ValueError("ratio components must be finite and positive")
            result = new / old
        elif value.endswith("%"):
            if field not in RATIOS:
                raise ValueError("percent only accepted for new-share ratios")
            result = Decimal(value[:-1]) / 100
        else:
            result = Decimal(value)
        if not result.is_finite() or result < 0 or (field != "rights_subscription_price" and result == 0):
            raise ValueError("expected finite positive value (subscription price may be explicit 0)")
        converted = float(result)
        if converted == float("inf") or (result > 0 and converted == 0):
            raise ValueError("numeric overflow/underflow")
        return converted
    except (InvalidOperation, ArithmeticError) as exc:
        raise ValueError("invalid decimal/percentage") from exc


def validate(rows: list[dict]) -> dict:
    records, issues = [], []
    for index, raw in enumerate(rows, 2):
        local = []

        def issue(code, field="", invalid=False):
            local.append({"row": index, "event_id": raw.get("event_id", ""),
                          "code": code, "field": field,
                          "severity": "INVALID" if invalid else "MANUAL_REVIEW"})

        values = {key: (value.strip() if isinstance(value, str) else value)
                  for key, value in raw.items()}
        if set(values) != set(FIELDS):
            issue("SCHEMA_FIELDS", invalid=True)
        # Never invent timestamps, identity, missing financial terms or verification.
        for field in NUMBERS:
            if values.get(field) not in (None, ""):
                try:
                    values[field] = number(str(values[field]), field, values.get("ratio_semantics", ""))
                except ValueError:
                    issue("INVALID_NUMBER", field, True)
                    values[field] = None
        normalized = {}
        for field, spec in schema(TABLE)["fields"].items():
            if field == "normalization_inputs":
                continue
            try:
                normalized[field] = coerce(values.get(field), spec)
            except (ValueError, TypeError, OverflowError):
                normalized[field] = None
                issue("SCHEMA_VALUE", field, True)
        event = normalized
        if event.get("raw_terms") is not None:
            event["raw_terms"] = raw["raw_terms"]
        if event.get("schema_version") != VERSION:
            issue("SCHEMA_VERSION", "schema_version", True)
        for field in ("security_id", "ticker", "exchange", "event_id", "event_group_id", "raw_terms"):
            if not event.get(field):
                issue("REQUIRED_FIELD", field, True)
        kind = event.get("event_type")
        for field in (*TERMS.get(kind, ()), "ex_date", "available_at", "announcement_date",
                      "primary_source_url", "available_at_evidence"):
            if event.get(field) is None or event.get(field) == "":
                issue("REQUIRED_EVIDENCE", field)
        for field in ("primary_source_url", "secondary_source_url", "identity_source_url"):
            if event.get(field) and not valid_url(event[field]):
                issue("SOURCE_URL", field, True)
        if event.get("primary_source_type") not in AUTHORITIES:
            issue("AUTHORITATIVE_SOURCE_REQUIRED", "primary_source_type")
        elif not authoritative_url(event.get("primary_source_type"), event.get("primary_source_url")):
            issue("SOURCE_AUTHORITY_URL_MISMATCH", "primary_source_url")
        if event.get("identity_status") != "VERIFIED" or not event.get("identity_source_url"):
            issue("HISTORICAL_IDENTITY_UNVERIFIED", "security_id")
        if kind == "OTHER":
            issue("OTHER_REQUIRES_REVIEW", "event_type")
        if event.get("conflict_notes"):
            issue("SOURCE_CONFLICT", "conflict_notes")
        if event.get("revision_status") != "ORIGINAL" or event.get("revision_of_event_id"):
            issue("REVISION_REQUIRES_REVIEW", "revision_status")
        if event.get("verification_status") != "VERIFIED":
            issue("NOT_HUMAN_VERIFIED", "verification_status",
                  event.get("verification_status") == "INVALID")
        if not event.get("verified_by") or not event.get("verified_at"):
            issue("REVIEW_ATTESTATION_REQUIRED", "verified_by")
        parsed = {}
        for field in ("available_at", "created_at", "verified_at"):
            if event.get(field):
                try:
                    parsed[field] = timestamp(event[field])
                except ValueError:
                    issue("TIMESTAMP_WITH_TIMEZONE_REQUIRED", field, True)
        published = event.get("primary_source_published_at")
        if published:
            try:
                if len(published) == 10:
                    if date.fromisoformat(published).isoformat() != published:
                        raise ValueError("date")
                    if "available_at" in parsed and parsed["available_at"].date() < date.fromisoformat(published):
                        issue("AVAILABLE_BEFORE_PUBLICATION", "available_at", True)
                else:
                    publication = timestamp(published)
                    if "available_at" in parsed and parsed["available_at"] < publication:
                        issue("AVAILABLE_BEFORE_PUBLICATION", "available_at", True)
            except ValueError:
                issue("PUBLICATION_DATE_FORMAT", "primary_source_published_at", True)
        if "available_at" in parsed:
            available = parsed["available_at"]
            if event.get("announcement_date") and available.date() < date.fromisoformat(event["announcement_date"]):
                issue("AVAILABLE_BEFORE_ANNOUNCEMENT", "available_at", True)
            if event.get("ex_date") and available.date() >= date.fromisoformat(event["ex_date"]):
                issue("LATE_OR_INTRADAY_KNOWLEDGE_PIT_REVIEW", "available_at")
            for field in ("created_at", "verified_at"):
                if field in parsed and parsed[field] < available:
                    issue("COLLECTION_BEFORE_AVAILABILITY", field, True)
        for before, after in (("announcement_date", "ex_date"), ("ex_date", "record_date"),
                              ("record_date", "payment_date"), ("ex_date", "payment_date")):
            if event.get(before) and event.get(after) and event[before] > event[after]:
                issue("DATE_ORDER", before, True)
        for field in RATIOS:
            if event.get(field) is not None and event[field] > 1:
                issue("UNUSUAL_RATIO_GT_100_PERCENT", field)
        multiplier = event.get("split_multiplier")
        if multiplier is not None and ((kind == "STOCK_SPLIT" and multiplier <= 1)
                                       or (kind == "REVERSE_SPLIT" and multiplier >= 1)):
            issue("SPLIT_DIRECTION", "split_multiplier", True)
        allowed = set(TERMS.get(kind, ()))
        for field in NUMBERS:
            if event.get(field) is not None and field not in allowed:
                issue("UNRELATED_TERM_MIXED_ROW", field, True)
        if event.get("source_hash") and not re.fullmatch(r"[0-9a-f]{64}", event["source_hash"]):
            issue("SOURCE_HASH_FORMAT", "source_hash", True)
        event["normalization_inputs"] = {key: raw.get(key) for key in (*NUMBERS, "ratio_semantics")}
        records.append({"row": index, "raw": raw, "normalized": event, "issues": local})

    ids, keys, groups, same_day = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for record in records:
        event = record["normalized"]
        ids[event.get("event_id")].append(record)
        key = (event.get("security_id"), event.get("ex_date"), event.get("event_type"))
        keys[key].append(record)
        groups[event.get("event_group_id")].append(record)
        same_day[(event.get("security_id"), event.get("ex_date"))].append(record)

    def flag(members, code, severity):
        for record in members:
            record["issues"].append({"row": record["row"], "event_id": record["raw"].get("event_id"),
                                     "field": "", "code": code, "severity": severity})

    for members in ids.values():
        if len(members) > 1:
            flag(members, "DUPLICATE_EVENT_ID", "INVALID")
    for members in keys.values():
        if len(members) > 1:
            terms = {tuple(record["normalized"].get(k) for k in NUMBERS) for record in members}
            flag(members, "TERM_CONFLICT" if len(terms) > 1 else "DUPLICATE_EVENT_KEY", "MANUAL_REVIEW")
    for members in groups.values():
        if len({(r["normalized"].get("security_id"), r["normalized"].get("ticker"),
                 r["normalized"].get("exchange"), r["normalized"].get("ex_date")) for r in members}) > 1:
            flag(members, "GROUP_IDENTITY_DATE_CONFLICT", "INVALID")
    for members in same_day.values():
        if len({r["normalized"].get("event_group_id") for r in members}) > 1:
            flag(members, "SAME_DAY_GROUP_MISMATCH", "MANUAL_REVIEW")
    # A correction can affect a different ex-date; never leave its old row eligible.
    revised_ids = {r["normalized"].get("revision_of_event_id") for r in records
                   if r["normalized"].get("revision_of_event_id")}
    for event_id in revised_ids:
        flag(ids.get(event_id, []), "REVISION_TARGET_REQUIRES_REVIEW", "MANUAL_REVIEW")
    for members in groups.values():
        if len(members) > 1 and any(r["issues"] for r in members):
            flag(members, "INCOMPLETE_OR_UNRESOLVED_EVENT_GROUP", "MANUAL_REVIEW")
    for record in records:
        levels = {item["severity"] for item in record["issues"]}
        status = "INVALID" if "INVALID" in levels else "MANUAL_REVIEW" if levels else "VERIFIED"
        record["normalized"]["verification_status"] = status
        issues.extend(record["issues"])
    counts = Counter(record["normalized"]["verification_status"] for record in records)
    return {"status": "PASS" if not issues else "PARTIAL", "row_count": len(rows),
            "counts": dict(counts), "issues": issues, "records": records}


def validate_file(path: Path) -> dict:
    return validate(read_csv(path, FIELDS))


def universe(path: Path) -> list[dict]:
    rows = read_csv(path)
    required = {"security_id", "ticker", "exchange"}
    if not rows or any(not required <= row.keys() for row in rows):
        raise ValueError("UNIVERSE: explicit nonempty security_id,ticker,exchange scope required")
    result, seen = [], set()
    for row in rows:
        item = {field: row[field].strip() for field in required}
        key = tuple(item[field] for field in ("security_id", "ticker", "exchange"))
        if not all(key) or item["exchange"] not in {"HOSE", "HNX", "UPCOM"} or key in seen:
            raise ValueError("UNIVERSE: empty/duplicate/invalid identity")
        seen.add(key)
        result.append(item)
    return result


def init_template(output: Path, coverage_output: Path | None = None,
                  universe_path: Path | None = None) -> None:
    paths = [output] + ([coverage_output] if coverage_output else [])
    if len(set(p.resolve() for p in paths)) != len(paths) or any(p.exists() for p in paths):
        raise ValueError("OUTPUT_EXISTS_OR_COLLISION: choose new paths")
    scoped = universe(universe_path) if universe_path else []
    if coverage_output and not scoped:
        raise ValueError("UNIVERSE: --universe required for coverage queue")
    write_new(output, csv_text(FIELDS, []))
    if coverage_output:
        rows = [dict.fromkeys(COVERAGE_FIELDS, "") | row | {"review_status": "NOT_YET_REVIEWED"}
                for row in scoped]
        write_new(coverage_output, csv_text(COVERAGE_FIELDS, rows))


def build(input_path: Path, output: Path) -> dict:
    # A fresh directory is mandatory. Never overwrite or promote review rows.
    input_hash = digest(input_path)
    result = validate_file(input_path)
    if digest(input_path) != input_hash:
        raise ValueError("INPUT_CHANGED_DURING_VALIDATION: save input and retry with a new run")
    if output.exists():
        raise ValueError("OUTPUT_EXISTS: use a new version/run directory")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(input_path, output / "input.csv")
    if digest(output / "input.csv") != input_hash:
        raise ValueError("INPUT_CHANGED_DURING_BUILD: incomplete run retained; use a new output")
    verified = [r["normalized"] for r in result["records"]
                if r["normalized"]["verification_status"] == "VERIFIED"]
    review = [r for r in result["records"] if r["normalized"]["verification_status"] != "VERIFIED"]
    write_new(output / "corporate_actions_v1.jsonl",
              "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in verified))
    write_new(output / "review_queue.json", json_text(review))
    summary = {k: v for k, v in result.items() if k != "records"}
    write_new(output / "validation.json", json_text(summary))
    manifest = {"schema_version": VERSION, "table": TABLE, "status": result["status"],
                "verified_event_count": len(verified), "review_row_count": len(review),
                "q11_status": "STILL_OPEN", "price_only_series": "NOT_BUILT",
                "input_sha256": input_hash,
                "code_sha256": digest(Path(__file__)),
                "schema_sha256": digest(Path(__file__).parents[1] / "schemas/corporate_actions_v1.json"),
                "files": {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}}
    write_new(output / "manifest.json", json_text(manifest))
    return manifest


def coverage_report(input_path: Path, coverage_path: Path, universe_path: Path,
                    start: str, end: str) -> dict:
    if date.fromisoformat(start).isoformat() != start or date.fromisoformat(end).isoformat() != end or start > end:
        raise ValueError("COVERAGE_WINDOW: invalid start/end")
    input_hashes = {p: digest(p) for p in (input_path, coverage_path, universe_path)}
    scoped = universe(universe_path)
    checked = read_csv(coverage_path, COVERAGE_FIELDS)
    result = validate_file(input_path)
    identity = lambda r: tuple(r.get(k) for k in ("security_id", "ticker", "exchange"))
    scope_keys = {identity(r) for r in scoped}
    coverage, events = defaultdict(list), defaultdict(list)
    for row in checked:
        coverage[identity(row)].append(row)
    unscoped = []
    for record in result["records"]:
        event = record["normalized"]
        if identity(event) not in scope_keys:
            unscoped.append(record["row"])
        # Missing ex-date cannot disappear from window coverage.
        if not event.get("ex_date") or start <= event["ex_date"] <= end:
            events[identity(event)].append(event)
    reports = []
    for item in scoped:
        key = identity(item)
        candidates = coverage[key]
        review = candidates[0] if len(candidates) == 1 else {}
        rows = events[key]
        counts = Counter(row["verification_status"] for row in rows)
        reasons = []
        attested = False
        if len(candidates) > 1:
            reasons.append("DUPLICATE_COVERAGE_IDENTITY")
        if review.get("review_status") == "REVIEWED":
            try:
                a, b = review["reviewed_start_date"], review["reviewed_end_date"]
                if date.fromisoformat(a).isoformat() != a or date.fromisoformat(b).isoformat() != b:
                    raise ValueError("date")
                checked_at = timestamp(review["last_checked_at"])
                if not (a <= start <= end <= b) or checked_at.date() < date.fromisoformat(end):
                    raise ValueError("window not fully reviewed")
                if (review["reviewed_event_types"] != "ALL_V1" or not review["reviewer"].strip()
                        or not review["coverage_evidence"].strip()
                        or not authoritative_url(review["primary_source_type"], review["primary_source_url"])):
                    raise ValueError("attestation missing")
                attested = True
            except (ValueError, KeyError):
                reasons.append("INCOMPLETE_COVERAGE_ATTESTATION")
        elif review.get("review_status", "NOT_YET_REVIEWED") != "NOT_YET_REVIEWED":
            reasons.append("COVERAGE_REVIEW_REQUIRED")
        if counts["MANUAL_REVIEW"] or counts["INVALID"]:
            reasons.append("UNRESOLVED_EVENT_ROWS")
        status = ("MANUAL_REVIEW_REQUIRED" if reasons else "NOT_YET_REVIEWED" if not attested
                  else "HAS_VERIFIED_EVENTS" if rows else "NO_EVENT_CONFIRMED")
        reports.append(item | {"required_start_date": start, "required_end_date": end,
                              "event_count": len(rows), "verified_event_count": counts["VERIFIED"],
                              "manual_review_count": counts["MANUAL_REVIEW"], "invalid_count": counts["INVALID"],
                              "last_checked_at": review.get("last_checked_at") or None,
                              "coverage_status": status, "reasons": reasons})
    extra_coverage = [list(key) for key in coverage if key not in scope_keys]
    if any(digest(p) != checksum for p, checksum in input_hashes.items()):
        raise ValueError("INPUT_CHANGED_DURING_REPORT: save all inputs and retry")
    return {"schema_version": VERSION, "required_start_date": start, "required_end_date": end,
            "scope_source": str(universe_path), "scope_sha256": input_hashes[universe_path],
            "input_sha256": input_hashes[input_path], "coverage_sha256": input_hashes[coverage_path],
            "scope_identity_claim": "USER_SUPPLIED_NOT_HISTORICALLY_PROMOTED",
            "coverage_pass": (bool(reports) and not unscoped and not extra_coverage and
                              all(r["coverage_status"] in {"HAS_VERIFIED_EVENTS", "NO_EVENT_CONFIRMED"}
                                  for r in reports)),
            "unscoped_event_rows": unscoped, "unscoped_coverage_identities": extra_coverage,
            "rows": reports, "q11_status": "STILL_OPEN"}
