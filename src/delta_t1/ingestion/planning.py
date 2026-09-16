"""M1 data-gate reports and read-only crawl planning.

Gate evidence is explicit and fail-closed. Synthetic evidence can exercise the
pipeline, but can never pass a real-source gate or unlock a scale plan.
"""
from datetime import date
from pathlib import Path

from ..io import digest, read_json
from .sources.vnstock import date_batches


SOURCE_SMOKE = "SOURCE_SMOKE"
REPRESENTATIVE_PILOT = "REPRESENTATIVE_PILOT"
M1_SCALE = "M1_SCALE"
EXTENDED_SCALE = "EXTENDED_SCALE"

REQUIRED_MARKET_FIELDS = {
    "open", "high", "low", "close", "reference_price", "ceiling_price",
    "floor_price", "volume", "traded_value",
}


def _evidence(value: dict | Path | str) -> tuple[dict, dict[str, str]]:
    if isinstance(value, dict):
        return value, dict(value.get("evidence_hashes", {}))
    path = Path(value).resolve()
    return read_json(path), {path.name: digest(path.read_bytes())}


def _report(gate: str, checks: dict[str, bool], scope: str,
            evidence_hashes: dict[str, str], *, pass_status: str = "PASS",
            failure_status: str = "BLOCKED", unlocks: tuple[str, ...] = ()) -> dict:
    blocking = [name for name, passed in checks.items() if not passed]
    return {
        "status": pass_status if not blocking else failure_status,
        "gate": gate,
        "checks": checks,
        "blocking_reasons": blocking,
        "scope": scope,
        "input_evidence_hashes": dict(sorted(evidence_hashes.items())),
        "unlocks": list(unlocks) if not blocking else [],
    }


def source_smoke_report(evidence: dict | Path | str) -> dict:
    """Assess source semantics and mechanics for 3–5 real symbols.

    A PASS only permits planning the representative pilot. It never permits an
    M1-scale or extended-scale crawl.
    """
    item, hashes = _evidence(evidence)
    fields = set(item.get("verified_market_fields", []))
    checks = {
        "real_data": item.get("synthetic") is False,
        "three_to_five_symbols": 3 <= item.get("symbol_count", 0) <= 5,
        "representative_exchange_or_documented_limit": bool(
            item.get("representative_exchange_evidence")
        ),
        "five_year_request_or_documented_source_limit": (
            item.get("requested_history_years", 0) >= 5
            or bool(item.get("source_history_limit_documented"))
        ),
        "required_market_fields_verified": REQUIRED_MARKET_FIELDS <= fields,
        "required_symbol_market_checks_passed": bool(
            item.get("required_symbol_market_checks_passed")
        ),
        "benchmark_passed": bool(item.get("benchmark_passed")),
        "history_depth_passed": bool(item.get("history_depth_passed")),
        "safe_anomaly_policy_applied": bool(item.get("safe_anomaly_policy_applied")),
        "volume_semantics_safe": bool(item.get("volume_semantics_safe")),
        "provenance_valid": bool(item.get("provenance_valid")),
        "cafef_window_evidence_hashed": bool(item.get("cafef_window_evidence_hashed")),
        "corporate_actions_inspected": item.get("corporate_actions_inspected", 0) >= 1,
        "shares_capital_structure_documented": bool(
            item.get("shares_capital_structure_documented")
        ),
        "quarterly_reports_inspected": item.get("quarterly_reports_inspected", 0) >= 3,
        "units_timezone_basis_pagination_rates_verified": bool(
            item.get("collection_semantics_verified")
        ),
        "rights_reviewed": bool(item.get("rights_reviewed")),
        "evidence_hashed": bool(hashes),
    }
    return _report(
        SOURCE_SMOKE,
        checks,
        "Xác minh source semantics/rights và mechanics; không phải production pilot.",
        hashes,
        failure_status="FAIL",
        unlocks=(REPRESENTATIVE_PILOT,),
    )


def representative_pilot_report(evidence: dict | Path | str,
                                source_smoke: dict) -> dict:
    """Assess the real 50–60 security market pilot, independently of financial PIT."""
    item, hashes = _evidence(evidence)
    hashes.update(source_smoke.get("input_evidence_hashes", {}))
    financial_pit_status = item.get("financial_pit_status", "PIT_UNRESOLVED")
    financial_features_allowed = (
        financial_pit_status == "PIT_READY"
        and item.get("financial_features_allowed") is True
    )
    provider_hashes = item.get("provider_artifact_hashes", {})
    provider_hashes_valid = bool(provider_hashes) and all(
        isinstance(path, str) and path
        and isinstance(value, str) and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
        for path, value in provider_hashes.items()
    )
    checks = {
        "source_smoke_passed": (
            source_smoke.get("gate") == SOURCE_SMOKE
            and source_smoke.get("status") == "PASS"
            and REPRESENTATIVE_PILOT in source_smoke.get("unlocks", [])
        ),
        "real_data": item.get("synthetic") is False,
        "real_execution_evidence": item.get("run_mode") == "REAL_EXECUTION",
        "fifty_to_sixty_symbols": 50 <= item.get("symbol_count", 0) <= 60,
        "at_least_five_years": item.get("history_years", 0) >= 5,
        "representative_exchanges": bool(item.get("representative_exchanges")),
        "representative_sectors_or_documented_limit": bool(
            item.get("representative_sectors_or_documented_limit")
        ),
        "source_routing_matches_smoke": bool(item.get("source_routing_matches_smoke")),
        "market_qc_passed": bool(item.get("market_qc_passed")),
        "price_basis_safe": bool(item.get("price_basis_safe")),
        "reconciliation_policy_safe": bool(item.get("reconciliation_policy_safe")),
        "provenance_complete": bool(item.get("provenance_complete")),
        "invalid_rows_fail_closed": bool(item.get("invalid_rows_fail_closed")),
        "source_qualified_conflicts": bool(item.get("source_qualified_conflicts")),
        "missing_values_preserved": bool(item.get("missing_values_preserved")),
        "no_price_forward_fill": bool(item.get("no_price_forward_fill")),
        "no_current_shares_backfill": bool(item.get("no_current_shares_backfill")),
        "real_provider_artifacts_hashed": provider_hashes_valid,
        "financial_pit_status_valid": financial_pit_status in ("PIT_UNRESOLVED", "PIT_READY"),
        "financial_safety_lock_active": (
            financial_pit_status == "PIT_READY" or not financial_features_allowed
        ),
        "evidence_hashed": bool(hashes),
    }
    report = _report(
        REPRESENTATIVE_PILOT,
        checks,
        "Pilot market M1 với source-qualified reconciliation và QC; financial PIT là track riêng.",
        hashes,
        unlocks=(M1_SCALE,),
    )
    report.update(financial_pit_status=financial_pit_status,
                  financial_features_allowed=financial_features_allowed)
    return report


def _range_years(start: str, end: str) -> float:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last:
        return -1
    return (last - first).days / 365.2425


def _scale_report(config: dict, pilot: dict, gate: str, *, extended: bool) -> dict:
    symbols = config.get("symbols", [])
    years = _range_years(config["start"], config["end"])
    hashes = dict(pilot.get("input_evidence_hashes", {}))
    hashes.update(config.get("evidence_hashes", {}))
    checks = {
        "representative_pilot_passed": (
            pilot.get("gate") == REPRESENTATIVE_PILOT
            and pilot.get("status") == "PASS"
            and gate in pilot.get("unlocks", [])
        ),
        "real_gate_evidence": pilot.get("checks", {}).get("real_data") is True,
        "historical_universe_evidence": bool(config.get("universe_evidence")),
        "at_least_300_unique_symbols": (
            len(symbols) >= 300 and len(symbols) == len(set(symbols))
        ),
        "at_least_five_years": years >= 5,
    }
    if extended:
        checks["at_most_fifteen_years"] = years <= 15
    scope = (
        "Future historical eligible universe; có thể vượt 1.200 mã, 5–15 năm."
        if extended else ">=300 securities và >=5 năm sau PASS representative pilot."
    )
    report = _report(gate, checks, scope, hashes, pass_status="PLANNED")
    if report["status"] == "PLANNED":
        jobs = [
            {"symbol": symbol, "start": first, "end": last}
            for symbol in sorted([*symbols, "VNINDEX"])
            for first, last in date_batches(config["start"], config["end"])
        ]
        report.update(
            config=config,
            representative_pilot=pilot,
            jobs=jobs,
            requests_lower_bound=len(jobs) + 1,
            interval_seconds=5,
            attempts=3,
            timeout_seconds=90,
            resume_policy=(
                "same vendor run ID only with unchanged code/config; preserve "
                "successful checksummed snapshots"
            ),
        )
    return report


def plan_m1_scale(config: dict, representative_pilot: dict) -> dict:
    """Plan, but never execute, the >=300-security M1 collection."""
    return _scale_report(config, representative_pilot, M1_SCALE, extended=False)


def plan_extended_scale(config: dict, representative_pilot: dict) -> dict:
    """Plan a future 5–15 year universe without an arbitrary symbol maximum."""
    return _scale_report(config, representative_pilot, EXTENDED_SCALE, extended=True)
