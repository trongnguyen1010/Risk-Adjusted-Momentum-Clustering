"""Complete-only C8 consolidation and independent CafeF session audits."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from delta_t1.ingestion.cafef_market_semantics import enrich_observed_row
from delta_t1.ingestion.sources.cafef import map_trade_history_row

C8_ARTIFACT_ID = "cafef-c8-complete-only-v1"
C8_DATA_VERSION = "CAFEF_C8_COMPLETE_ONLY_V1"
C8_EXECUTION_VERSION = "c8-complete-only-v1"
SNAPSHOT_DATE = "2026-08-28"
TARGET_START = "2020-01-01"
DEFERRED_DECISION = "DEFERRED_EXPANSION_ACQUISITION"
REQUIRED_FEATURES = (
    "mom_21", "mom_63", "mom_126", "mom_252", "vol_63", "mdd_126",
    "beta_126", "liquidity_21",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_manifest_outputs(directory: Path) -> dict:
    manifest = read_json(directory / "manifest.json")
    bad = [name for name, digest in manifest.get("outputs", {}).items()
           if not (directory / name).is_file() or sha256_file(directory / name) != digest]
    if bad:
        raise ValueError("manifest output hash mismatch: " + ",".join(sorted(bad)))
    return manifest


def current_security_rows(rows: list[dict], snapshot: str = SNAPSHOT_DATE) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["security_id"]].append(row)
    current = []
    for security_id, intervals in grouped.items():
        matches = [row for row in intervals if row["valid_from"] <= snapshot
                   and (not row.get("valid_to") or snapshot <= row["valid_to"])]
        if len(matches) != 1:
            raise ValueError(f"current identity interval is not unique: {security_id}")
        current.append(matches[0])
    return sorted(current, key=lambda row: row["ticker"])


def build_scope(root: Path) -> dict:
    c5 = root / "artifacts/cafef_primary/cafef-tradehistory-500-data-gate-v2"
    c7 = root / "artifacts/cafef_primary/cafef-expansion-c7-partial-consolidation-v1"
    expansion_config = root / "configs/data/cafef_expansion_v1"
    verify_manifest_outputs(c7)
    baseline_intervals = list(iter_jsonl(c5 / "clean/securities.jsonl"))
    baseline = current_security_rows(baseline_intervals)
    inventory = read_csv(c7 / "acquisition_inventory.csv")
    universe = read_json(expansion_config / "universe.json")["securities"]
    expansion_by_ticker = {row["ticker"]: row for row in universe}
    if len(baseline) != 500 or len(inventory) != 600 or len(expansion_by_ticker) != 600:
        raise ValueError("frozen baseline/expansion counts do not match 500/600")
    complete_inventory = [row for row in inventory if row["acquisition_status"] == "COMPLETE"]
    deferred_inventory = [row for row in inventory if row["acquisition_status"] != "COMPLETE"]
    if len(complete_inventory) != 452 or len(deferred_inventory) != 148:
        raise ValueError("C7 complete/deferred counts do not match 452/148")

    baseline_tickers = {row["ticker"] for row in baseline}
    baseline_ids = {row["security_id"] for row in baseline}
    expansion = []
    for item in complete_inventory:
        source = expansion_by_ticker[item["ticker"]]
        expansion.append({
            "security_id": source["security_id"], "ticker": source["ticker"],
            "exchange": source["exchange"], "company_name": source["company_name"],
            "candidate_source": "C7_COMPLETE_EXPANSION",
            "acquisition_status": "COMPLETE", "audit_start": item["oldest_observed_date"],
            "boundary_basis": "TARGET_START" if item["oldest_observed_date"] <= TARGET_START
            else "PROVIDER_OBSERVED_HISTORY_BOUNDARY_NOT_LISTING_PROOF",
            "worker_id": item["worker_id"], "source_zip": item["source_zip"],
            "source_zip_sha256": item["source_zip_sha256"],
        })
    expansion_tickers = {row["ticker"] for row in expansion}
    expansion_ids = {row["security_id"] for row in expansion}
    if len(expansion_tickers) != 452 or len(expansion_ids) != 452:
        raise ValueError("duplicate identity inside complete expansion")
    if baseline_tickers & expansion_tickers or baseline_ids & expansion_ids:
        raise ValueError("baseline/expansion ticker or security_id collision")

    identity_rows = read_csv(root / "docs/crawl/plans/cafef_c1_prep_v1/cafef_c1_candidate_universe.csv")
    reviewed_aliases = set(baseline_tickers)
    for row in identity_rows:
        current = str(row.get("current_ticker", "")).upper()
        if current:
            reviewed_aliases.add(current)
        try:
            intervals = json.loads(row.get("historical_identity_intervals") or "[]")
        except json.JSONDecodeError:
            intervals = []
        reviewed_aliases.update(str(interval.get("ticker", "")).upper() for interval in intervals)
    reviewed_aliases.discard("")
    if reviewed_aliases & expansion_tickers:
        raise ValueError("reviewed historical alias collision with complete expansion")

    candidates = [{
        "security_id": row["security_id"], "ticker": row["ticker"],
        "exchange": row["exchange"], "company_name": row.get("company_name", ""),
        "candidate_source": "C5_BASELINE_500", "acquisition_status": "BASELINE_C5",
        "audit_start": max(TARGET_START, row["valid_from"]),
        "boundary_basis": "REVIEWED_BASELINE_IDENTITY_INTERVAL",
        "worker_id": "", "source_zip": "", "source_zip_sha256": "",
    } for row in baseline] + expansion
    if len(candidates) != 952 or len({row["ticker"] for row in candidates}) != 952 \
            or len({row["security_id"] for row in candidates}) != 952:
        raise ValueError("combined candidate universe is not an exact unique 952")

    deferred = []
    for item in deferred_inventory:
        source = expansion_by_ticker[item["ticker"]]
        deferred.append({
            "ticker": item["ticker"], "security_id": item["security_id"],
            "exchange": source["exchange"], "worker_id": item["worker_id"],
            "c7_acquisition_status": item["acquisition_status"],
            "current_c8_decision": DEFERRED_DECISION,
        })
    expected = Counter({"ACQUISITION_PARTIAL": 3, "NOT_YET_ACQUIRED": 138,
                        "ACQUISITION_FAILED": 7})
    if Counter(row["c7_acquisition_status"] for row in deferred) != expected:
        raise ValueError("deferred acquisition breakdown mismatch")
    return {
        "baseline_intervals": baseline_intervals, "baseline": baseline,
        "complete_inventory": complete_inventory, "expansion": expansion,
        "candidates": sorted(candidates, key=lambda row: row["ticker"]),
        "deferred": sorted(deferred, key=lambda row: row["ticker"]),
        "inventory": inventory, "universe": universe,
    }


def attrition_rows(scope: dict) -> list[dict]:
    universe_by_ticker = {row["ticker"]: row for row in scope["universe"]}
    dimensions = (("exchange", lambda row: universe_by_ticker[row["ticker"]]["exchange"]),
                  ("worker", lambda row: row["worker_id"]))
    output = []
    for dimension, key in dimensions:
        selected = Counter(key(row) for row in scope["inventory"])
        complete = Counter(key(row) for row in scope["complete_inventory"])
        for value in sorted(selected):
            output.append({
                "dimension": dimension, "value": value,
                "selected_expansion": selected[value], "complete_expansion": complete[value],
                "deferred_expansion": selected[value] - complete[value],
                "completion_rate": round(complete[value] / selected[value], 6),
                "representativeness_claim": "NOT_ASSESSED",
            })
    return output


def row_quality(mapped: dict) -> str:
    prices = (mapped.get("cafef_close_price"), mapped.get("cafef_adjust_price"))
    if any(value is None or not math.isfinite(value) or value <= 0 for value in prices):
        return "INVALID_PROVIDER_ROW"
    for key in ("matched_volume", "put_through_volume", "matched_value", "put_through_value"):
        value = mapped.get(key)
        if value is not None and (not math.isfinite(value) or value < 0):
            return "INVALID_PROVIDER_ROW"
    bands = (mapped.get("floor_price"), mapped.get("reference_price"), mapped.get("ceiling_price"))
    if all(value is not None for value in bands) and not bands[0] <= bands[1] <= bands[2]:
        return "INVALID_PROVIDER_ROW"
    return "OBSERVED_VALID"


def canonical_market_row(mapped: dict, provenance: dict) -> dict:
    base = {
        "security_id": mapped["security_id"], "ticker": mapped["ticker"],
        "exchange": mapped["exchange"], "trade_date": mapped["trade_date"],
        "raw_open": None, "raw_high": None, "raw_low": None,
        "raw_close": mapped["cafef_close_price"],
        "reference_price": mapped["reference_price"],
        "ceiling_price": mapped["ceiling_price"], "floor_price": mapped["floor_price"],
        "adj_close": mapped["cafef_adjust_price"], "adjustment_basis": "vendor_adjusted",
        "matched_volume_shares": mapped["matched_volume"],
        "negotiated_volume_shares": mapped["put_through_volume"],
        "matched_value_vnd": mapped["matched_value"],
        "negotiated_value_vnd": mapped["put_through_value"],
        "available_at": mapped["trade_date"] + "T17:00:00+07:00",
        "source": "cafef", "source_endpoint": "TradeHistoryNew.ashx",
        "source_run_id": provenance["handoff_run_id"], "raw_path": provenance["raw_path"],
        "raw_sha256": provenance["raw_sha256"], "fetched_at": provenance.get("fetched_at"),
        "data_version": C8_DATA_VERSION,
    }
    return enrich_observed_row(base)


def resolve_observations(observations: list[dict]) -> tuple[list[dict], list[dict]]:
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in observations:
        by_key[(row["security_id"], row["trade_date"])].append(row)
    clean, conflicts = [], []
    values = ("raw_close", "adj_close", "reference_price", "ceiling_price", "floor_price",
              "matched_volume_shares", "negotiated_volume_shares", "matched_value_vnd",
              "negotiated_value_vnd")
    for key, rows in sorted(by_key.items()):
        signatures = {tuple(row.get(field) for field in values) for row in rows}
        if len(signatures) == 1:
            clean.append(rows[0])
        else:
            conflicts.append({
                "security_id": key[0], "ticker": rows[0]["ticker"], "trade_date": key[1],
                "classification": "CONFLICTING_PROVIDER_OBSERVATION",
                "observation_count": len(rows),
            })
    return clean, conflicts


def calendar_by_exchange(calendar: list[dict], snapshot: str = SNAPSHOT_DATE) -> dict[str, list[str]]:
    output: dict[str, list[str]] = defaultdict(list)
    for row in calendar:
        if row.get("is_open") and row["trade_date"] <= snapshot:
            output[row["exchange"]].append(row["trade_date"])
    return {exchange: sorted(set(days)) for exchange, days in output.items()}


def build_session_audits(candidates: list[dict], calendar: list[dict], valid_keys: set[tuple[str, str]],
                         conflict_keys: set[tuple[str, str]], invalid_keys: set[tuple[str, str]],
                         zero_volume_keys: set[tuple[str, str]] | None = None,
                         snapshot: str = SNAPSHOT_DATE) -> tuple[list[dict], list[dict]]:
    calendars = calendar_by_exchange(calendar, snapshot)
    zero_volume_keys = zero_volume_keys or set()
    full_rows, latest_rows = [], []
    for candidate in sorted(candidates, key=lambda row: row["ticker"]):
        sid, start = candidate["security_id"], candidate["audit_start"]
        exchange_days = calendars[candidate["exchange"]]
        full_days = [day for day in exchange_days if start <= day <= snapshot]
        boundary_days = [day for day in exchange_days if TARGET_START <= day < start]
        latest_days = exchange_days[-253:]

        def counts(days: list[str]) -> Counter:
            result = Counter()
            for day in days:
                key = (sid, day)
                if day < start:
                    result["IDENTITY_OR_LISTING_BOUNDARY" if candidate["candidate_source"] == "C5_BASELINE_500"
                           else "DEFERRED_REVIEW"] += 1
                elif key in conflict_keys:
                    result["CONFLICTING_PROVIDER_OBSERVATION"] += 1
                elif key in invalid_keys:
                    result["INVALID_PROVIDER_ROW"] += 1
                elif key in zero_volume_keys:
                    result["OBSERVED_ZERO_VOLUME"] += 1
                elif key in valid_keys:
                    result["OBSERVED_VALID"] += 1
                else:
                    result["MISSING_ON_TRADEHISTORYNEW"] += 1
            return result

        full = counts(full_days)
        latest = counts(latest_days)
        full_observed = full["OBSERVED_VALID"] + full["OBSERVED_ZERO_VOLUME"]
        latest_observed = latest["OBSERVED_VALID"] + latest["OBSERVED_ZERO_VOLUME"]
        full_complete = bool(full_days) and full_observed == len(full_days)
        latest_complete = len(latest_days) == 253 and latest_observed == 253
        full_rows.append({
            "security_id": sid, "ticker": candidate["ticker"], "exchange": candidate["exchange"],
            "audit_start": start, "snapshot_date": snapshot, "expected_sessions": len(full_days),
            "observed_valid": full["OBSERVED_VALID"],
            "observed_zero_volume": full["OBSERVED_ZERO_VOLUME"],
            "missing_on_tradehistorynew": full["MISSING_ON_TRADEHISTORYNEW"],
            "invalid_provider_row": full["INVALID_PROVIDER_ROW"],
            "conflicting_provider_observation": full["CONFLICTING_PROVIDER_OBSERVATION"],
            "identity_or_listing_boundary": len(boundary_days)
            if candidate["candidate_source"] == "C5_BASELINE_500" else 0,
            "calendar_uncertain": 0,
            "deferred_review": len(boundary_days)
            if candidate["candidate_source"] != "C5_BASELINE_500" else 0,
            "full_history_complete": full_complete,
            "boundary_basis": candidate["boundary_basis"],
        })
        latest_rows.append({
            "security_id": sid, "ticker": candidate["ticker"], "exchange": candidate["exchange"],
            "snapshot_date": snapshot, "expected_sessions_253": len(latest_days),
            "observed_valid_253": latest["OBSERVED_VALID"],
            "observed_zero_volume_253": latest["OBSERVED_ZERO_VOLUME"],
            "missing_sessions_253": latest["MISSING_ON_TRADEHISTORYNEW"],
            "invalid_sessions_253": latest["INVALID_PROVIDER_ROW"],
            "conflicting_sessions_253": latest["CONFLICTING_PROVIDER_OBSERVATION"],
            "boundary_sessions_253": latest["IDENTITY_OR_LISTING_BOUNDARY"] + latest["DEFERRED_REVIEW"],
            "latest253_complete": latest_complete,
        })
    return full_rows, latest_rows


def apply_snapshot_cutoff(rows, snapshot: str = SNAPSHOT_DATE) -> list[dict]:
    return [row for row in rows if row["trade_date"] <= snapshot]


def readiness_rows(candidates: list[dict], latest_features: dict[str, dict],
                   full_audit: list[dict], latest_audit: list[dict],
                   snapshot_rows: dict[str, dict]) -> list[dict]:
    full_by = {row["security_id"]: row for row in full_audit}
    latest_by = {row["security_id"]: row for row in latest_audit}
    output = []
    for candidate in sorted(candidates, key=lambda row: row["ticker"]):
        sid = candidate["security_id"]
        feature = latest_features.get(sid, {})
        observation = snapshot_rows.get(sid)
        activity = observation.get("trading_activity_status") if observation else "UNKNOWN"
        missing = [name for name in REQUIRED_FEATURES if feature.get(name) is None]
        market_ready = bool(feature.get("market_feature_ready"))
        output.append({
            "security_id": sid, "ticker": candidate["ticker"], "snapshot_date": SNAPSHOT_DATE,
            "feature_complete": bool(feature.get("feature_complete")),
            "market_feature_ready_v2": market_ready,
            "trading_activity_status": activity,
            "tradability_eligible": observation.get("tradability_eligible") if observation else None,
            "historical_identity_ready": bool(feature.get("historical_identity_ready")),
            "research_ready": bool(feature.get("research_ready")),
            "full_history_complete": full_by[sid]["full_history_complete"],
            "latest253_complete": latest_by[sid]["latest253_complete"],
            "missing_required_features": "|".join(missing),
        })
    return output
