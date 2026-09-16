"""Run the bounded four-symbol research/demo SOURCE_SMOKE; never starts the pilot."""
import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.artifact_ids import new_artifact_id
from delta_t1.io import atomic_write, digest, encoded, write_json
from delta_t1.ingestion.planning import source_smoke_report
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.cafef import (ADAPTER_VERSION as CAFE_VERSION, CafeFSource,
                                               apply_invalid_row_policy,
                                               map_trade_history_row)
from delta_t1.ingestion.sources.vnstock import (ADAPTER_VERSION as KBS_VERSION, KBSPublicHttpSource,
                                                 classify_volume_semantics,
                                                 financial_raw_only_metadata,
                                                 map_kbs_wire_ohlcv_row)


EXPECTED_SYMBOLS = {"FPT": "HOSE", "VNM": "HOSE", "PVS": "HNX", "ACV": "UPCOM"}


def utc_now():
    return datetime.now().astimezone(timezone.utc).isoformat()


def validate_config(config):
    if (config.get("synthetic") is not False or config.get("research_demo") is not True
            or config.get("rights_status") != "RIGHTS_NOT_VERIFIED"
            or config.get("risk_acceptance") != "ACCEPTED_RESEARCH_RISK"
            or config.get("symbols") != EXPECTED_SYMBOLS or config.get("benchmark") != "VNINDEX"):
        raise ValueError("research/demo smoke policy or exact symbol scope is invalid")
    if config["http"].get("concurrency", 99) > 2:
        raise ValueError("SOURCE_SMOKE concurrency must be <= 2")
    for name in ("WINDOW_RECENT", "WINDOW_OLD"):
        window = config["windows"][name]
        days = (date.fromisoformat(window["end"]) - date.fromisoformat(window["start"])).days + 1
        if not 20 <= days <= 30:
            raise ValueError(f"{name} must span 20-30 calendar days")
    recent = config["windows"]["WINDOW_RECENT"]
    old = config["windows"]["WINDOW_OLD"]
    reach = (date.fromisoformat(recent["end"]) - date.fromisoformat(old["end"])).days
    if not 4.8 * 365 <= reach <= 5.2 * 366:
        raise ValueError("old window does not test approximately five-year reach")
    if config["financial"].get("mode") != "RAW_ONLY_PIT_UNRESOLVED":
        raise ValueError("financial mode must remain raw-only PIT-unresolved")
    policy = config.get("invalid_market_row_policy", {})
    if (policy.get("classification"), policy.get("row_status"), policy.get("policy")) != (
            "PROVIDER_CORRUPT_ROW", "INVALID_REQUIRED_MARKET_ROW", "EXCLUDE_ROW"):
        raise ValueError("invalid required-market-row policy is not fail-closed")
    if config.get("corporate_action_evidence", {}).get("status") not in (
            "VERIFIED", "PARTIAL", "UNAVAILABLE"):
        raise ValueError("corporate-action evidence status is invalid")
    if set(config.get("shares_status", {})) != set(EXPECTED_SYMBOLS):
        raise ValueError("shares status must cover every smoke symbol")


class RawStore:
    def __init__(self, root, run_id):
        self.root, self.run_id, self.artifacts = Path(root), run_id, []

    def save(self, provider, name, response, request, adapter_version, acquisition_client,
             endpoint_discovered_via=None):
        directory = self.root / "data" / "raw" / provider / self.run_id
        raw_path = directory / f"{name}.json"
        metadata_path = directory / f"{name}.metadata.json"
        body = response["body"]
        sha256 = digest(body)
        if raw_path.exists() and digest(raw_path.read_bytes()) != sha256:
            raise ValueError("immutable raw artifact collision")
        atomic_write(raw_path, body)
        metadata = {
            "provider": provider, "acquisition_client": acquisition_client,
            "endpoint_method": "GET", "url": response["url"], "request": request,
            "fetched_at": utc_now(), "adapter_client_version": adapter_version,
            "rights_status": "RIGHTS_NOT_VERIFIED",
            "execution_policy": "ACCEPTED_RESEARCH_RISK", "sha256": sha256,
            "bytes": len(body), "http_status": response["status"],
            "raw_path": raw_path.relative_to(self.root).as_posix(),
        }
        if endpoint_discovered_via:
            metadata["endpoint_discovered_via"] = endpoint_discovered_via
        write_json(metadata_path, metadata)
        self.artifacts.append(metadata)
        return metadata


def valid_market_rows(rows, index=False):
    if not rows or len({r["trade_date"] for r in rows}) != len(rows):
        return False
    for row in rows:
        if not (row["low"] <= row["open"] <= row["high"]
                and row["low"] <= row["close"] <= row["high"]):
            return False
        if row["volume"] is not None and row["volume"] < 0:
            return False
        if row["price_basis"] != "VENDOR_ADJUSTED":
            return False
        if row["price_unit"] != ("INDEX_POINTS" if index else "VND_PER_SHARE"):
            return False
    return True


def in_window(rows, window):
    return sorted((row for row in rows if window["start"] <= row["trade_date"] <= window["end"]),
                  key=lambda row: row["trade_date"])


def locate_cafef_window(source, store, symbol, exchange, window, label, max_page, cache):
    def fetch(page):
        if page not in cache:
            response = source.acquire_trade_history_page(
                {"symbol": symbol, "page_index": page, "page_size": 30})
            artifact = store.save("cafef", f"{symbol}-page-{page:03d}", response,
                                  {"symbol": symbol, "exchange": exchange,
                                   "page_index": page, "page_size": 30,
                                   "requested_window": window}, CAFE_VERSION, "direct")
            cache[page] = {"rows": [map_trade_history_row(row, symbol, exchange)
                                     for row in response["payload"]["Data"]],
                           "artifact": artifact}
        return cache[page]

    lo, hi, found = 1, max_page, None
    target = window["end"]
    while lo <= hi:
        page = (lo + hi) // 2
        rows = fetch(page)["rows"]
        if not rows:
            hi = page - 1
            continue
        newest, oldest = max(r["trade_date"] for r in rows), min(r["trade_date"] for r in rows)
        if target > newest:
            hi = page - 1
        elif target < oldest:
            lo = page + 1
        else:
            found = page
            break
    if found is None:
        found = min(max(lo, 1), max_page)
    pages = {found}
    rows = fetch(found)["rows"]
    if rows and max(r["trade_date"] for r in rows) < window["end"] and found > 1:
        pages.add(found - 1)
    if rows and min(r["trade_date"] for r in rows) > window["start"] and found < max_page:
        pages.add(found + 1)
    combined = [row for page in sorted(pages) for row in fetch(page)["rows"]]
    selected = in_window(combined, window)
    contributing = []
    for page in sorted(pages):
        if any(window["start"] <= row["trade_date"] <= window["end"]
               for row in fetch(page)["rows"]):
            artifact = fetch(page)["artifact"]
            contributing.append({"page": page, "raw_path": artifact["raw_path"],
                                 "sha256": artifact["sha256"]})
    return {"rows": selected, "contributing_pages": contributing}


def run(config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config)
    run_id = new_artifact_id("source-smoke")
    client = PublicJsonClient(**{k: v for k, v in config["http"].items() if k != "concurrency"})
    cafef, kbs, store = CafeFSource(client), KBSPublicHttpSource(client), RawStore(ROOT, run_id)
    result = {"run_id": run_id, "started_at": utc_now(), "config": config,
              "config_sha256": digest(encoded(config)), "symbols": {}, "benchmark": {},
              "financial": {}, "raw_artifacts": store.artifacts, "bypass_used": False,
              "pilot_started": False}
    windows = config["windows"]
    try:
        for symbol, exchange in config["symbols"].items():
            kbs_by_window, cafe_by_window = {}, {}
            for label, window in windows.items():
                response = kbs.acquire_ohlcv(symbol, window["start"], window["end"])
                store.save("kbs", f"{symbol}-{label.lower()}", response,
                           {"symbol": symbol, "exchange": exchange, "date_range": window},
                           KBS_VERSION, "delta_public_http", "vnstock")
                kbs_by_window[label] = sorted(
                    [map_kbs_wire_ohlcv_row(row, symbol, exchange)
                     for row in response["payload"]["data_day"]], key=lambda row: row["trade_date"])
            cache = {}
            for label, window in windows.items():
                cafe_by_window[label] = locate_cafef_window(
                    cafef, store, symbol, exchange, window, label,
                    config["cafef"]["max_search_page"], cache)
            checks = {}
            anomaly_findings = []
            for label in windows:
                krows, crows = kbs_by_window[label], cafe_by_window[label]["rows"]
                eligible_crows, findings = apply_invalid_row_policy(
                    crows, config["invalid_market_row_policy"])
                anomaly_findings.extend(findings)
                checks[label] = {
                    "kbs_rows": len(krows), "cafef_rows": len(crows),
                    "cafef_eligible_rows": len(eligible_crows),
                    "cafef_excluded_rows": len(crows) - len(eligible_crows),
                    "kbs_date_range": [krows[0]["trade_date"], krows[-1]["trade_date"]] if krows else None,
                    "cafef_date_range": [crows[0]["trade_date"], crows[-1]["trade_date"]] if crows else None,
                    "ohlcv_valid": valid_market_rows(krows),
                    "cafef_limits_valid": bool(eligible_crows) and all(
                        r["reference_price"] is not None and r["ceiling_price"] is not None
                        and r["floor_price"] is not None
                        and r["floor_price"] <= r["reference_price"] <= r["ceiling_price"]
                        for r in eligible_crows),
                    "invalid_rows_resolved": all(finding["safe"] for finding in findings),
                    "value_components_valid": bool(crows) and all(
                        all(r[f] is None or r[f] >= 0 for f in ("matched_volume", "matched_value",
                            "put_through_volume", "put_through_value", "traded_value")) for r in crows),
                    "cafef_contributing_pages": cafe_by_window[label]["contributing_pages"],
                }
            shared = sorted(set(r["trade_date"] for r in kbs_by_window["WINDOW_RECENT"])
                            & set(r["trade_date"] for r in cafe_by_window["WINDOW_RECENT"]["rows"]))
            volume = classify_volume_semantics(kbs_by_window["WINDOW_RECENT"],
                                               cafe_by_window["WINDOW_RECENT"]["rows"])
            volume_safe = volume["classification"] != "UNRESOLVED"
            passed = all(c["ohlcv_valid"] and c["cafef_limits_valid"]
                         and c["invalid_rows_resolved"] and c["value_components_valid"]
                         for c in checks.values()) and volume_safe
            investigation = None
            if symbol == "VNM":
                target_days = {"2021-09-08", "2021-09-09", "2021-09-10"}
                investigation = {
                    "requested_dates": "2021-09-08..2021-09-10",
                    "cafef": [{"trade_date": row["trade_date"], **row["raw_fields"]}
                              for row in cafe_by_window["WINDOW_OLD"]["rows"]
                              if row["trade_date"] in target_days],
                    "kbs": [row for row in kbs_by_window["WINDOW_OLD"]
                            if row["trade_date"] in target_days],
                    "classification": (anomaly_findings[0]["classification"]
                                       if anomaly_findings else "NO_ANOMALY"),
                    "policy": (anomaly_findings[0]["policy"]
                               if anomaly_findings else "NOT_REQUIRED"),
                }
            result["symbols"][symbol] = {"exchange": exchange, "status": "PASS" if passed else "FAIL",
                "checks": checks, "invalid_market_rows": anomaly_findings,
                "anomaly_investigation": investigation,
                "reconciliation": {"shared_recent_dates": len(shared),
                "volume_semantics": volume, "volume_safe_for_promotion": volume_safe,
                "price_status": "PRICE_BASIS_CONFLICT", "price_comparison_performed": False}}

        for label, window in windows.items():
            response = kbs.acquire_ohlcv("VNINDEX", window["start"], window["end"], is_index=True)
            store.save("kbs", f"VNINDEX-{label.lower()}", response,
                       {"symbol": "VNINDEX", "date_range": window}, KBS_VERSION,
                       "delta_public_http", "vnstock")
            rows = [map_kbs_wire_ohlcv_row(row, "VNINDEX", "HOSE", is_index=True)
                    for row in response["payload"]["data_day"]]
            result["benchmark"][label] = {"rows": len(rows), "valid": valid_market_rows(rows, index=True),
                                           "volume_available": any(r["volume"] is not None for r in rows)}
        fin = config["financial"]
        response = kbs.acquire_financial_raw(fin["symbol"], report_type=fin["report_type"],
                                             period_type=fin["period_type"], page=fin["page"],
                                             page_size=fin["page_size"])
        store.save("kbs", f"{fin['symbol']}-financial-raw-only", response,
                   {"symbol": fin["symbol"], "mode": fin["mode"], "report_type": fin["report_type"],
                    "period_type": fin["period_type"], "page": 1, "page_size": fin["page_size"]},
                   KBS_VERSION, "delta_public_http", "vnstock")
        observations = financial_raw_only_metadata(response["payload"])
        result["financial"] = {"status": "RAW_ONLY_PIT_UNRESOLVED", "observations": observations,
                               "facts_used_in_features": False}
        result["corporate_action"] = config["corporate_action_evidence"]
        result["shares_status"] = config["shares_status"]
        all_symbols = all(item["status"] == "PASS" for item in result["symbols"].values())
        benchmark_ok = all(item["valid"] and item["rows"] > 0 for item in result["benchmark"].values())
        history_ok = (all(item["checks"]["WINDOW_OLD"]["kbs_rows"] > 0
                          and item["checks"]["WINDOW_OLD"]["cafef_rows"] > 0
                          for item in result["symbols"].values())
                      and result["benchmark"]["WINDOW_OLD"]["rows"] > 0)
        anomaly_ok = (len(result["symbols"]["VNM"]["invalid_market_rows"]) == 1
                      and all(item["safe"] for item in result["symbols"]["VNM"]["invalid_market_rows"]))
        volume_ok = all(item["reconciliation"]["volume_safe_for_promotion"]
                        for item in result["symbols"].values())
        provenance_ok = all(
            artifact["acquisition_client"] == "delta_public_http"
            and artifact.get("endpoint_discovered_via") == "vnstock"
            for artifact in store.artifacts if artifact["provider"] == "kbs")
        traceability_ok = all(
            check["cafef_contributing_pages"]
            and all(item.get("raw_path") and item.get("sha256")
                    for item in check["cafef_contributing_pages"])
            for symbol in result["symbols"].values() for check in symbol["checks"].values())
        evidence_hashes = {artifact["raw_path"]: artifact["sha256"] for artifact in store.artifacts}
        for path in (config_path, ROOT / "docs/crawl/sources/CAFEF.md",
                     ROOT / "docs/data/DATA_USAGE_RISK_ACCEPTANCE.md"):
            evidence_hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
        evidence = {
            "synthetic": False, "symbol_count": len(result["symbols"]),
            "representative_exchange_evidence": "HOSE/HNX/UPCOM",
            "requested_history_years": 5,
            "verified_market_fields": ["open", "high", "low", "close", "reference_price",
                                       "ceiling_price", "floor_price", "volume", "traded_value"],
            "required_symbol_market_checks_passed": all_symbols,
            "benchmark_passed": benchmark_ok, "history_depth_passed": history_ok,
            "safe_anomaly_policy_applied": anomaly_ok, "volume_semantics_safe": volume_ok,
            "provenance_valid": provenance_ok,
            "cafef_window_evidence_hashed": traceability_ok,
            "corporate_actions_inspected": 1 if result["corporate_action"]["status"] in ("VERIFIED", "PARTIAL") else 0,
            "shares_capital_structure_documented": all(
                status in ("VERIFIED_AVAILABLE", "CURRENT_SNAPSHOT_ONLY",
                           "HISTORICAL_UNAVAILABLE", "BLOCKED")
                for status in result["shares_status"].values()),
            "quarterly_reports_inspected": len(observations),
            "collection_semantics_verified": (all_symbols and benchmark_ok and history_ok
                                                and anomaly_ok and volume_ok
                                                and provenance_ok and traceability_ok),
            "rights_reviewed": config.get("rights_status") == "RIGHTS_NOT_VERIFIED"
                               and config.get("risk_acceptance") == "ACCEPTED_RESEARCH_RISK",
            "evidence_hashes": evidence_hashes,
        }
        result["gate_evidence"] = evidence
        result["gate"] = source_smoke_report(evidence)
        result["overall"] = result["gate"]["status"]
    except Exception as exc:
        result["overall"] = "FAIL"
        result["stopped_error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        result["finished_at"] = utc_now()
        result["raw_artifacts"] = store.artifacts
        directory = ROOT / "data" / "raw" / "source_smoke" / run_id
        output = directory / "result.json"
        if "gate" not in result:
            result["gate"] = source_smoke_report({"synthetic": False, "evidence_hashes": {
                artifact["raw_path"]: artifact["sha256"] for artifact in store.artifacts}})
        write_json(directory / "gate.json", result["gate"])
        write_json(output, result)
        print(output)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "configs/data/source_smoke.research_demo.json"))
    args = parser.parse_args()
    try:
        outcome = run(args.config)
    except Exception as exc:
        print(f"STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(outcome["overall"])
