"""Stage A3 bounded primary-provider recovery pilot.

Planning is deterministic and offline. Network access occurs only inside
``build_stage_a3`` through the explicitly supplied provider, which lets the CLI
require an ``--execute`` acknowledgement and lets unit tests remain offline.
Recovered rows are evidence artifacts only; this module never mutates or
promotes the canonical baseline.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime
import io
import json
from pathlib import Path

from ..artifact_ids import new_artifact_id
from ..io import atomic_write, digest, encoded, now, read_json, read_rows, write_json, write_rows
from .local_salvage import write_text_parquet
from .representative_pilot import _valid_kbs
from .representative_pilot_canonical import AVAILABILITY_TIME
from .session_audit import build_a1_audit
from .sources.base import AccessControlError, RateLimitError, SemanticValidationError
from .sources.vnstock import ADAPTER_VERSION as KBS_ADAPTER_VERSION, map_kbs_wire_ohlcv_row


STAGE = "A3 — Primary Provider Recovery Pilot"
REQUIRED_EXCHANGES = {"HOSE", "HNX", "UPCOM"}
REQUIRED_PRIORITIES = {"P0", "P1", "P2"}
_WINDOWS = (21, 63, 126, 252)
_CANDIDATE_COLUMNS = (
    "candidate_id", "request_id", "security_id", "ticker", "exchange",
    "trade_date", "provider", "source_symbol", "raw_path", "raw_sha256",
    "raw_row_sha256", "fetched_at", "available_at", "decision_at",
    "adapter_version", "price_basis", "price_unit", "volume_unit",
    "normalized_row_json", "raw_row_json", "decision", "rejection_reason",
    "reconciliation_rule_id",
)
_RESULT_FIELDS = (
    "request_id", "security_id", "ticker", "exchange", "trade_date",
    "status", "reason", "raw_path", "raw_sha256", "candidate_id",
)


def _inside(path, parent, label):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if not path.is_relative_to(parent):
        raise ValueError(f"{label} escapes {parent}")
    return path


def _verify_artifacts(directory, manifest, label):
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError(f"{label} has no artifact checksums")
    for relative, expected in artifacts.items():
        path = _inside(directory / relative, directory, f"{label} artifact")
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError(f"{label} artifact checksum mismatch: {relative}")


def _git_commit(root):
    dotgit = root / ".git"
    if dotgit.is_file():
        marker = dotgit.read_text(encoding="utf-8").strip()
        if not marker.startswith("gitdir:"):
            return "UNRESOLVED"
        dotgit = (root / marker.split(":", 1)[1].strip()).resolve()
    head = dotgit / "HEAD"
    if not head.is_file():
        return "UNRESOLVED"
    value = head.read_text(encoding="utf-8").strip()
    if not value.startswith("ref: "):
        return value
    ref = value[5:]
    loose = dotgit / ref
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip()
    return "UNRESOLVED"


def _csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _load_priorities(a1_directory):
    with (a1_directory / "recovery_priority.csv").open(encoding="utf-8", newline="") as stream:
        return {row["security_id"]: row for row in csv.DictReader(stream)}


def group_missing_ranges(missing_dates, *, max_dates_per_range=5,
                         max_calendar_span_days=10, max_ranges=3):
    """Group real missing dates into short, bounded, deterministic requests."""
    if not 1 <= max_dates_per_range <= 20 or not 1 <= max_calendar_span_days <= 31:
        raise ValueError("invalid bounded recovery range limits")
    if not 1 <= max_ranges <= 10:
        raise ValueError("max_ranges must be between 1 and 10")
    days = sorted({date.fromisoformat(value) for value in missing_dates})
    groups = []
    for day in days:
        if not groups:
            groups.append([day])
            continue
        current = groups[-1]
        span = (day - current[0]).days + 1
        gap = (day - current[-1]).days
        if (len(current) < max_dates_per_range and span <= max_calendar_span_days
                and gap <= 3):
            current.append(day)
        else:
            groups.append([day])
    groups = groups[-max_ranges:]
    return [{"start": group[0].isoformat(), "end": group[-1].isoformat(),
             "targeted_dates": [value.isoformat() for value in group]}
            for group in groups]


def select_pilot(symbol_rows, *, sample_size=12, explicit_symbols=(),
                 high_priority_symbols=()):
    """Choose a deterministic 10–20 security pilot without inventing strata."""
    if not 10 <= sample_size <= 20:
        raise ValueError("A3 pilot sample_size must be between 10 and 20")
    candidates = {row["ticker"].upper(): dict(row) for row in symbol_rows
                  if row["missing_sessions_total"] > 0 and not row["market_feature_ready"]}
    if len(candidates) < sample_size:
        raise ValueError("not enough non-ready securities for A3 pilot")
    explicit = tuple(dict.fromkeys(value.upper() for value in explicit_symbols))
    high = tuple(dict.fromkeys(value.upper() for value in high_priority_symbols))
    unknown = (set(explicit) | set(high)) - set(candidates)
    if unknown:
        raise ValueError("unknown or non-missing A3 symbols: " + ",".join(sorted(unknown)))
    if explicit and not 10 <= len(explicit) <= 20:
        raise ValueError("explicit A3 pilot must contain 10–20 unique symbols")
    if len(high) > sample_size:
        raise ValueError("high-priority symbols exceed pilot sample size")

    roles = defaultdict(set)
    selected = []

    def add(ticker, role):
        roles[ticker].add(role)
        if ticker not in selected:
            selected.append(ticker)

    if explicit:
        for ticker in explicit:
            add(ticker, "EXPLICIT_USER_SELECTION")
        sample_size = len(explicit)
    else:
        for priority in ("P0", "P1", "P2"):
            pool = sorted((row for row in candidates.values()
                           if row.get("recovery_priority") == priority),
                          key=lambda row: (row["missing_last_252"],
                                           row["missing_sessions_total"], row["ticker"]))
            if pool:
                add(pool[0]["ticker"], f"{priority}_STRATUM")
        for ticker in high:
            add(ticker, "HIGH_MARKET_PRIORITY_USER_DECLARED")
        for exchange in sorted(REQUIRED_EXCHANGES):
            pool = sorted((row for row in candidates.values() if row["exchange"] == exchange),
                          key=lambda row: (row["missing_last_252"],
                                           row["missing_sessions_total"], row["ticker"]))
            if pool:
                add(pool[0]["ticker"], f"{exchange}_CONTROL")
        sparse = sorted(candidates.values(),
                        key=lambda row: (row["coverage_ratio"],
                                         -row["missing_sessions_total"], row["ticker"]))[:2]
        for row in sparse:
            add(row["ticker"], "SPARSE_P4_CONTROL")
        normal = sorted(candidates.values(),
                        key=lambda row: (row["missing_last_252"],
                                         row["missing_sessions_total"], row["ticker"]))
        for row in normal:
            if len(selected) >= sample_size:
                break
            add(row["ticker"], "NORMAL_CONTROL")
    if len(selected) > sample_size:
        raise ValueError("required A3 selection roles exceed sample_size")
    if len(selected) < sample_size:
        raise ValueError("unable to fill deterministic A3 pilot")
    for ticker in high:
        if ticker in selected:
            roles[ticker].add("HIGH_MARKET_PRIORITY_USER_DECLARED")

    result = []
    for ticker in selected:
        row = dict(candidates[ticker])
        row["selection_roles"] = sorted(roles[ticker])
        result.append(row)
    included_priorities = {row.get("recovery_priority") for row in result}
    available_priorities = {row.get("recovery_priority") for row in candidates.values()}
    contract = {
        "sample_size": len(result),
        "exchanges_included": sorted({row["exchange"] for row in result}),
        "required_exchanges_missing": sorted(
            REQUIRED_EXCHANGES - {row["exchange"] for row in result}),
        "priorities_available": sorted(REQUIRED_PRIORITIES & available_priorities),
        "priorities_included": sorted(REQUIRED_PRIORITIES & included_priorities),
        "required_priorities_unavailable": sorted(REQUIRED_PRIORITIES - available_priorities),
        "required_priorities_available_but_missing": sorted(
            (REQUIRED_PRIORITIES & available_priorities) - included_priorities),
        "high_priority_input": list(high),
        "high_priority_included": sorted(set(high) & set(selected)),
        "sparse_controls": sorted(row["ticker"] for row in result
                                   if "SPARSE_P4_CONTROL" in row["selection_roles"]),
        "market_priority_semantics": "USER_DECLARED_ACQUISITION_PRIORITY_ONLY",
    }
    if contract["required_exchanges_missing"]:
        raise ValueError("A3 pilot must cover HOSE, HNX and UPCOM")
    if contract["required_priorities_available_but_missing"]:
        raise ValueError("available P0/P1/P2 strata were omitted")
    if not contract["high_priority_included"]:
        contract["limitations"] = ["no frozen HIGH market-priority evidence was supplied"]
    else:
        contract["limitations"] = []
    if contract["required_priorities_unavailable"]:
        contract["limitations"].append(
            "A1 contains no " + ", ".join(contract["required_priorities_unavailable"])
            + " securities; no proxy priority was invented")
    return result, contract


def build_request_plan(selected, detail, *, max_dates_per_range=5,
                       max_calendar_span_days=10, max_ranges_per_symbol=3):
    by_security = defaultdict(list)
    for row in detail:
        by_security[row["security_id"]].append(row["trading_date"])
    requests = []
    for security in selected:
        ranges = group_missing_ranges(
            by_security[security["security_id"]],
            max_dates_per_range=max_dates_per_range,
            max_calendar_span_days=max_calendar_span_days,
            max_ranges=max_ranges_per_symbol,
        )
        for index, bounded in enumerate(ranges, 1):
            requests.append({
                "request_id": f"kbs-{security['ticker']}-{index:02d}-{bounded['start']}-{bounded['end']}",
                "provider": "kbs", "acquisition_path": "kbs_delta_public_http",
                "security_id": security["security_id"], "ticker": security["ticker"],
                "exchange": security["exchange"],
                "a1_recovery_priority": security.get("recovery_priority"),
                "selection_roles": security["selection_roles"],
                "start": bounded["start"], "end": bounded["end"],
                "targeted_dates": bounded["targeted_dates"],
                "expected_target_rows": len(bounded["targeted_dates"]),
                "strategy": "PRIMARY_PROVIDER_RETRY_CURRENT_CLIENT",
            })
    if not requests:
        raise ValueError("A3 request plan is empty")
    return requests


def _candidate(request, raw, mapped, metadata, decision_at, status, reason=""):
    raw_row_hash = digest(encoded(raw))
    candidate_id = digest(encoded([request["request_id"], mapped.get("trade_date"), raw_row_hash]))[:24]
    available_at = f"{mapped['trade_date']}T{AVAILABILITY_TIME}"
    return {
        "candidate_id": candidate_id, "request_id": request["request_id"],
        "security_id": request["security_id"], "ticker": request["ticker"],
        "exchange": request["exchange"], "trade_date": mapped["trade_date"],
        "provider": "kbs", "source_symbol": mapped.get("symbol", ""),
        "raw_path": metadata["raw_path"], "raw_sha256": metadata["sha256"],
        "raw_row_sha256": raw_row_hash, "fetched_at": metadata["fetched_at"],
        "available_at": available_at, "decision_at": decision_at,
        "adapter_version": metadata["adapter_client_version"],
        "price_basis": mapped.get("price_basis", ""),
        "price_unit": mapped.get("price_unit", ""),
        "volume_unit": mapped.get("volume_unit", ""),
        "normalized_row_json": encoded(mapped).decode("utf-8"),
        "raw_row_json": encoded(raw).decode("utf-8"),
        "decision": status, "rejection_reason": reason,
        "reconciliation_rule_id": "A3_EXACT_REQUEST_IDENTITY_DATE_UNIT_BASIS_V1",
    }


def _mapping_reject_candidate(request, raw, metadata, decision_by_key, reason):
    raw_date = raw.get("t") if isinstance(raw, dict) else None
    trade_date = ""
    if isinstance(raw_date, str):
        try:
            trade_date = date.fromisoformat(raw_date[:10]).isoformat()
        except ValueError:
            pass
    raw_row_hash = digest(encoded(raw))
    candidate_id = digest(encoded([request["request_id"], trade_date, raw_row_hash]))[:24]
    return {
        "candidate_id": candidate_id, "request_id": request["request_id"],
        "security_id": request["security_id"], "ticker": request["ticker"],
        "exchange": request["exchange"], "trade_date": trade_date,
        "provider": "kbs", "source_symbol": request["ticker"],
        "raw_path": metadata["raw_path"], "raw_sha256": metadata["sha256"],
        "raw_row_sha256": raw_row_hash, "fetched_at": metadata["fetched_at"],
        "available_at": f"{trade_date}T{AVAILABILITY_TIME}" if trade_date else "",
        "decision_at": decision_by_key.get((request["exchange"], trade_date), ""),
        "adapter_version": metadata["adapter_client_version"],
        "price_basis": "", "price_unit": "", "volume_unit": "",
        "normalized_row_json": "", "raw_row_json": encoded(raw).decode("utf-8"),
        "decision": "REJECT", "rejection_reason": reason,
        "reconciliation_rule_id": "A3_ROW_MAPPING_FAIL_CLOSED_V1",
    }


def execute_request_plan(requests, *, provider, output, root, decision_by_key,
                         progress=None):
    """Execute bounded requests through a supplied provider and preserve raw bytes."""
    raw_directory = output / "primary_recovery_raw"
    raw_directory.mkdir(parents=True, exist_ok=False)
    candidates, results, request_status = [], [], []
    total = len(requests)
    for position, request in enumerate(requests, 1):
        if progress:
            progress(f"[{position:02d}/{total:02d}] {request['ticker']} "
                     f"{request['start']}..{request['end']}")
        base_result = {key: request[key] for key in ("request_id", "security_id", "ticker", "exchange")}
        metadata, metadata_path = None, None
        try:
            response = provider.acquire_ohlcv(
                request["ticker"], request["start"], request["end"], is_index=False)
            body = response.get("body")
            payload = response.get("payload")
            if not isinstance(body, bytes):
                raise SemanticValidationError("KBS response envelope is incomplete")
            raw_path = raw_directory / f"{request['request_id']}.json"
            metadata_path = raw_directory / f"{request['request_id']}.metadata.json"
            if raw_path.exists() or metadata_path.exists():
                raise ValueError("immutable A3 raw artifact collision")
            atomic_write(raw_path, body)
            fetched_at = now()
            metadata = {
                "provider": "kbs", "symbol": request["ticker"],
                "request_id": request["request_id"], "request": {
                    "symbol": request["ticker"], "exchange": request["exchange"],
                    "date_range": {"start": request["start"], "end": request["end"]},
                    "targeted_dates": request["targeted_dates"],
                },
                "acquisition_client": "delta_public_http",
                "adapter_client_version": KBS_ADAPTER_VERSION,
                "endpoint_method": "GET", "url": response.get("url"),
                "http_status": response.get("status"), "fetched_at": fetched_at,
                "rights_status": "RIGHTS_NOT_VERIFIED",
                "execution_policy": "ACCEPTED_RESEARCH_RISK",
                "raw_path": raw_path.relative_to(output).as_posix(),
                "sha256": digest(body), "bytes": len(body),
            }
            try:
                try:
                    decoded_body = json.loads(body)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise SemanticValidationError("KBS raw body is not valid JSON") from exc
                if not isinstance(payload, dict):
                    raise SemanticValidationError("KBS parsed payload is not an object")
                if decoded_body != payload:
                    raise SemanticValidationError("KBS parsed payload differs from preserved raw body")
                if (response.get("status") != 200
                        or not str(response.get("url") or "").startswith("https://")):
                    raise SemanticValidationError("KBS response provenance is incomplete")
                if (str(payload.get("symbol") or "").upper() != request["ticker"]
                        or not isinstance(payload.get("data_day"), list)):
                    raise SemanticValidationError("KBS response identity/schema mismatch")
            except (OSError, TypeError, ValueError, SemanticValidationError) as exc:
                metadata.update(validation_status="REJECTED_ENVELOPE",
                                validation_error=f"{type(exc).__name__}: {exc}")
                write_json(metadata_path, metadata)
                raise
            metadata.update(validation_status="ACCEPTED_ENVELOPE", validation_error=None)
            write_json(metadata_path, metadata)
            raw_by_date, mapping_rejects = defaultdict(list), defaultdict(list)
            for raw_index, raw in enumerate(payload["data_day"]):
                try:
                    mapped = map_kbs_wire_ohlcv_row(
                        raw, request["ticker"], request["exchange"])
                except (KeyError, OSError, OverflowError, TypeError, ValueError,
                        SemanticValidationError) as exc:
                    reason = f"ROW_MAPPING_OR_DATE_INVALID:{type(exc).__name__}"
                    rejected = _mapping_reject_candidate(
                        request, raw, metadata, decision_by_key, reason)
                    candidates.append(rejected)
                    if rejected["trade_date"] in request["targeted_dates"]:
                        mapping_rejects[rejected["trade_date"]].append(rejected)
                    continue
                if mapped["trade_date"] in request["targeted_dates"]:
                    raw_by_date[mapped["trade_date"]].append((raw, mapped))
            for trade_date in request["targeted_dates"]:
                matches = raw_by_date.get(trade_date, [])
                result = {**base_result, "trade_date": trade_date,
                          "raw_path": metadata["raw_path"], "raw_sha256": metadata["sha256"],
                          "candidate_id": ""}
                if not matches:
                    rejected = mapping_rejects.get(trade_date, [])
                    if rejected:
                        results.append({**result, "status": "REJECT",
                                        "reason": "ROW_MAPPING_OR_DATE_INVALID",
                                        "candidate_id": rejected[0]["candidate_id"]})
                    else:
                        results.append({**result, "status": "UNRESOLVED",
                                        "reason": "PRIMARY_PROVIDER_RETURNED_NO_TARGET_ROW"})
                    continue
                if len(matches) != 1:
                    for raw, mapped in matches:
                        decision = decision_by_key.get((request["exchange"], trade_date), "")
                        candidates.append(_candidate(request, raw, mapped, metadata, decision,
                                                     "REJECT", "DUPLICATE_PROVIDER_ROWS"))
                    results.append({**result, "status": "REJECT",
                                    "reason": "DUPLICATE_PROVIDER_ROWS"})
                    continue
                raw, mapped = matches[0]
                decision_at = decision_by_key.get((request["exchange"], trade_date))
                reasons = []
                if mapped["symbol"] != request["ticker"]:
                    reasons.append("IDENTITY_CONFLICT")
                if mapped["price_unit"] != "VND_PER_SHARE" or mapped["volume_unit"] != "SHARES":
                    reasons.append("UNIT_CONFLICT")
                if mapped["price_basis"] != "VENDOR_ADJUSTED":
                    reasons.append("PRICE_BASIS_CONFLICT")
                if not _valid_kbs([mapped]):
                    reasons.append("INVALID_REQUIRED_MARKET_ROW")
                if not decision_at:
                    reasons.append("DECISION_AT_MISSING")
                else:
                    available_at = datetime.fromisoformat(
                        f"{trade_date}T{AVAILABILITY_TIME}")
                    decision = datetime.fromisoformat(decision_at)
                    if available_at.tzinfo is None or decision.tzinfo is None:
                        reasons.append("PIT_TIMESTAMP_UNZONED")
                    elif available_at > decision:
                        reasons.append("AVAILABLE_AFTER_DECISION")
                status = "REJECT" if reasons else "RECOVERED"
                candidate = _candidate(request, raw, mapped, metadata, decision_at or "",
                                       status, ";".join(sorted(reasons)))
                candidates.append(candidate)
                results.append({**result, "status": status,
                                "reason": candidate["rejection_reason"],
                                "candidate_id": candidate["candidate_id"]})
            request_status.append({"request_id": request["request_id"], "status": "SUCCESS",
                                   "raw_path": metadata["raw_path"], "sha256": metadata["sha256"]})
            if progress:
                recovered = sum(row["request_id"] == request["request_id"]
                                and row["status"] == "RECOVERED" for row in results)
                progress(f"    success; recovered={recovered}/{len(request['targeted_dates'])}")
        except (AccessControlError, RateLimitError, OSError, TypeError, ValueError,
                SemanticValidationError) as exc:
            reason = f"{type(exc).__name__}: {exc}"
            raw_path_value = metadata["raw_path"] if metadata else ""
            raw_sha_value = metadata["sha256"] if metadata else ""
            request_status.append({"request_id": request["request_id"], "status": "FAILED",
                                   "reason": reason, "raw_path": raw_path_value,
                                   "sha256": raw_sha_value})
            for trade_date in request["targeted_dates"]:
                results.append({**base_result, "trade_date": trade_date,
                                "status": "UNRESOLVED", "reason": "REQUEST_FAILED: " + reason,
                                "raw_path": raw_path_value, "raw_sha256": raw_sha_value,
                                "candidate_id": ""})
            if progress:
                progress("    failed; preserved as unresolved")
    return candidates, results, request_status


def _newly_complete(per_symbol, observed, expected, recovered_keys, latest_date):
    windows, newly_252 = {window: [] for window in _WINDOWS}, []
    for row in per_symbol:
        security_id = row["security_id"]
        before = observed[security_id]
        after = before | {day for sid, day in recovered_keys if sid == security_id}
        ordered = sorted(day for day in expected[security_id] if day <= latest_date)
        for window in _WINDOWS:
            required = set(ordered[-window:])
            if len(required) == window and not required <= before and required <= after:
                windows[window].append(row["ticker"])
        required_252 = set(ordered[-252:])
        if len(required_252) == 252 and not required_252 <= before and required_252 <= after:
            newly_252.append(row["ticker"])
    return windows, sorted(newly_252)


def _stage_status(selection_contract, request_status):
    successful = sum(row["status"] == "SUCCESS" for row in request_status)
    if successful == 0:
        return "FAIL"
    if (successful != len(request_status) or selection_contract["limitations"]
            or selection_contract["required_priorities_available_but_missing"]):
        return "PARTIAL"
    return "PASS"


def _report_markdown(manifest):
    metrics = manifest["metrics"]
    lines = [
        "# A3 — Primary Provider Recovery Pilot", "",
        f"Run: `{manifest['run_id']}`  ", f"Generated: `{manifest['created_at']}`  ",
        f"Canonical baseline (read-only): `{manifest['canonical_run_id']}`", "",
        "## Scope", "",
        "Pilot chỉ retry KBS trên bounded date ranges cho 10–20 securities. Không refetch toàn bộ "
        "lịch sử, không imputation, không zero-fill và không ghi canonical.", "",
        "## Metrics", "", "| Metric | Value |", "|---|---:|",
        f"| Requests attempted | {metrics['requests_attempted']} |",
        f"| Requests successful | {metrics['requests_successful']} |",
        f"| Rows requested | {metrics['rows_requested']} |",
        f"| Rows recovered | {metrics['rows_recovered']} |",
        f"| Rows unresolved/rejected | {metrics['rows_unresolved']} |",
        f"| Recovery rate | {metrics['recovery_rate']:.4f} |",
        f"| Securities improved | {metrics['securities_improved']} |",
        f"| Securities newly latest-252 complete | {metrics['securities_newly_latest252_complete']} |",
        f"| Securities newly ready confirmed | {metrics['securities_newly_ready_confirmed']} |", "",
        "`newly ready confirmed` giữ bằng 0 tại A3 vì stage này không merge canonical hoặc rebuild "
        "feature; latest-252 complete chỉ là recovery evidence candidate.", "",
        "## Pilot selection", "",
        f"Selected: {', '.join(manifest['selected_symbols'])}", "",
    ]
    contract = manifest["selection_contract"]
    if contract["limitations"]:
        lines.extend(["Limitations:", ""] + [f"- {value}" for value in contract["limitations"]] + [""])
    lines.extend(["## Newly complete windows (candidate evidence)", "",
                  "| Window | Count | Tickers |", "|---:|---:|---|"])
    for window in _WINDOWS:
        values = manifest["newly_complete_windows"][str(window)]
        lines.append(f"| {window} | {len(values)} | {', '.join(values) or '—'} |")
    lines.extend([
        "", "## Findings", "",
        "- Primary path: `KBS delta public HTTP` qua adapter hiện có.",
        "- Access-control/rate-limit/request failure dừng request tương ứng và giữ target rows là `UNRESOLVED`.",
        "- Không tự động chuyển secondary provider trong A3.", "",
        "## Artifacts", "", "- `primary_recovery_requests.jsonl`",
        "- `primary_recovery_raw/`", "- `primary_recovery_candidates.parquet`",
        "- `primary_recovery_results.csv`", "- `manifest.json`", "",
        "## Stage Result", "", f"`{manifest['status']}`", "", "## STOP", "",
        "Chờ independent audit trước Stage A4.",
    ])
    return "\n".join(lines).encode("utf-8")


def build_stage_a3(canonical_path, a1_artifact_path, a2_artifact_path, *, root,
                   provider, sample_size=12, explicit_symbols=(),
                   high_priority_symbols=(), max_dates_per_range=5,
                   max_calendar_span_days=10, max_ranges_per_symbol=3,
                   progress=None):
    """Execute A3 with an explicitly supplied KBS provider."""
    if provider is None:
        raise ValueError("A3 execution requires an explicit primary provider")
    root = Path(root).resolve()
    canonical_path = _inside(canonical_path, root / "data" / "canonical", "canonical path")
    a1_artifact_path = _inside(a1_artifact_path, root / "artifacts" / "data_enrichment", "A1 path")
    a2_artifact_path = _inside(a2_artifact_path, root / "artifacts" / "data_enrichment", "A2 path")
    canonical_manifest = read_json(canonical_path / "manifest.json")
    a1_manifest = read_json(a1_artifact_path / "manifest.json")
    a2_manifest = read_json(a2_artifact_path / "manifest.json")
    if (canonical_manifest.get("run_id") != canonical_path.name
            or canonical_manifest.get("canonical_promotion_status") != "PASS"
            or canonical_manifest.get("synthetic") is not False):
        raise ValueError("A3 requires a real approved canonical baseline")
    if (a1_manifest.get("status") != "PASS"
            or a1_manifest.get("canonical_run_id") != canonical_manifest["run_id"]):
        raise ValueError("A3 requires matching A1 PASS evidence")
    if (a2_manifest.get("status") != "PASS"
            or a2_manifest.get("canonical_run_id") != canonical_manifest["run_id"]
            or a2_manifest.get("a1_run_id") != a1_manifest["run_id"]):
        raise ValueError("A3 requires matching A2 PASS evidence")
    if a2_manifest.get("metrics", {}).get("accepted_rows") != 0:
        raise ValueError("A3 cannot exclude nonzero A2 accepted keys without a reviewed key sidecar")
    _verify_artifacts(canonical_path, canonical_manifest, "canonical")
    _verify_artifacts(a1_artifact_path, a1_manifest, "A1")
    _verify_artifacts(a2_artifact_path, a2_manifest, "A2")

    securities = read_rows(canonical_path / "clean" / "securities.jsonl")
    prices = read_rows(canonical_path / "clean" / "prices_daily.jsonl")
    calendar = read_rows(canonical_path / "clean" / "trading_calendar.jsonl")
    features = read_rows(canonical_path / "features" / "monthly.jsonl")
    detail, per_symbol, _, latest_date = build_a1_audit(
        securities, prices, calendar, features,
        collection_end=canonical_manifest["collection_end"])
    priorities = _load_priorities(a1_artifact_path)
    for row in per_symbol:
        evidence = priorities.get(row["security_id"], {})
        row["recovery_priority"] = evidence.get("recovery_priority")
        row["priority_reason"] = evidence.get("priority_reason")
    selected, selection_contract = select_pilot(
        per_symbol, sample_size=sample_size, explicit_symbols=explicit_symbols,
        high_priority_symbols=high_priority_symbols)
    requests = build_request_plan(
        selected, detail, max_dates_per_range=max_dates_per_range,
        max_calendar_span_days=max_calendar_span_days,
        max_ranges_per_symbol=max_ranges_per_symbol)

    decision_by_key = {}
    for row in calendar:
        if row.get("is_open"):
            key = (row["exchange"], row["trade_date"])
            value = row.get("decision_at")
            if not value:
                raise ValueError(f"canonical decision_at missing: {key}")
            if key in decision_by_key and decision_by_key[key] != value:
                raise ValueError(f"canonical decision_at conflict: {key}")
            decision_by_key[key] = value

    run_id = new_artifact_id("m1-a3-primary-recovery")
    output = root / "artifacts" / "data_enrichment" / run_id
    output.mkdir(parents=True, exist_ok=False)
    write_rows(output / "primary_recovery_requests.jsonl", requests)
    candidates, results, request_status = execute_request_plan(
        requests, provider=provider, output=output, root=root,
        decision_by_key=decision_by_key, progress=progress)
    candidates.sort(key=lambda row: (row["ticker"], row["trade_date"], row["candidate_id"]))
    results.sort(key=lambda row: (row["ticker"], row["trade_date"], row["request_id"]))
    write_text_parquet(output / "primary_recovery_candidates.parquet", candidates,
                       _CANDIDATE_COLUMNS, creator="delta-t1-a3-stdlib-parquet")
    atomic_write(output / "primary_recovery_results.csv", _csv_bytes(results, _RESULT_FIELDS))

    observed, expected = defaultdict(set), defaultdict(set)
    for row in prices:
        observed[row["security_id"]].add(row["trade_date"])
        expected[row["security_id"]].add(row["trade_date"])
    for row in detail:
        expected[row["security_id"]].add(row["trading_date"])
    recovered_keys = {(row["security_id"], row["trade_date"])
                      for row in candidates if row["decision"] == "RECOVERED"}
    windows, newly_252 = _newly_complete(
        per_symbol, observed, expected, recovered_keys, latest_date)
    successful = sum(row["status"] == "SUCCESS" for row in request_status)
    recovered = sum(row["status"] == "RECOVERED" for row in results)
    requested = len(results)
    status = _stage_status(selection_contract, request_status)
    created_at = now()
    config = {
        "sample_size": sample_size, "explicit_symbols": list(explicit_symbols),
        "high_priority_symbols": list(high_priority_symbols),
        "max_dates_per_range": max_dates_per_range,
        "max_calendar_span_days": max_calendar_span_days,
        "max_ranges_per_symbol": max_ranges_per_symbol,
        "provider": "kbs_delta_public_http", "adapter_version": KBS_ADAPTER_VERSION,
    }
    manifest = {
        "run_id": run_id, "stage": STAGE, "status": status, "created_at": created_at,
        "git_commit": _git_commit(root), "config_hash": digest(encoded(config)),
        "canonical_run_id": canonical_manifest["run_id"], "a1_run_id": a1_manifest["run_id"],
        "a2_run_id": a2_manifest["run_id"],
        "input_artifact_ids": [canonical_manifest["run_id"], a1_manifest["run_id"], a2_manifest["run_id"]],
        "input_hashes": {
            "canonical_manifest": digest((canonical_path / "manifest.json").read_bytes()),
            "a1_manifest": digest((a1_artifact_path / "manifest.json").read_bytes()),
            "a2_manifest": digest((a2_artifact_path / "manifest.json").read_bytes()),
        },
        "provider": "kbs", "provider_versions": {"kbs": KBS_ADAPTER_VERSION},
        "adapter_versions": {"kbs": KBS_ADAPTER_VERSION},
        "network_requests": len(requests), "canonical_mutations": 0,
        "synthetic_rows": 0, "imputed_rows": 0,
        "selected_symbols": [row["ticker"] for row in selected],
        "selection_contract": selection_contract, "request_status": request_status,
        "metrics": {
            "requests_attempted": len(requests), "requests_successful": successful,
            "rows_requested": requested, "rows_recovered": recovered,
            "rows_unresolved": requested - recovered,
            "recovery_rate": recovered / requested if requested else 0.0,
            "securities_improved": len({row["security_id"] for row in candidates
                                        if row["decision"] == "RECOVERED"}),
            "securities_newly_latest252_complete": len(newly_252),
            "securities_newly_ready_confirmed": 0,
        },
        "newly_complete_windows": {str(window): sorted(windows[window]) for window in _WINDOWS},
        "latest_completed_snapshot": latest_date,
        "limitations": [
            *selection_contract["limitations"],
            "A3 does not merge canonical or rebuild features; newly ready remains unconfirmed",
            "same-provider alternate acquisition path is not configured in this pilot",
        ],
    }
    atomic_write(output / "stage_a3_report.md", _report_markdown(manifest))
    manifest["artifacts"] = {
        path.relative_to(output).as_posix(): digest(path.read_bytes())
        for path in sorted(output.rglob("*")) if path.is_file()
    }
    write_json(output / "manifest.json", manifest)
    return output, manifest
