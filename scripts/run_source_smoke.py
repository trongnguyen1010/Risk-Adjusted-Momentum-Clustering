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
from delta_t1.ingestion.sources.base import PublicJsonClient
from delta_t1.ingestion.sources.cafef import (ADAPTER_VERSION as CAFE_VERSION, CafeFSource,
                                               map_trade_history_row)
from delta_t1.ingestion.sources.vnstock import (ADAPTER_VERSION as KBS_VERSION, KBSVnstockSource,
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


class RawStore:
    def __init__(self, root, run_id):
        self.root, self.run_id, self.artifacts = Path(root), run_id, []

    def save(self, provider, name, response, request, adapter_version, acquisition_client):
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
            store.save("cafef", f"{symbol}-page-{page:03d}", response,
                       {"symbol": symbol, "exchange": exchange, "page_index": page,
                        "page_size": 30, "requested_window": window}, CAFE_VERSION, "direct")
            cache[page] = [map_trade_history_row(row, symbol, exchange)
                           for row in response["payload"]["Data"]]
        return cache[page]

    lo, hi, found = 1, max_page, None
    target = window["end"]
    while lo <= hi:
        page = (lo + hi) // 2
        rows = fetch(page)
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
    rows = fetch(found)
    if rows and max(r["trade_date"] for r in rows) < window["end"] and found > 1:
        pages.add(found - 1)
    if rows and min(r["trade_date"] for r in rows) > window["start"] and found < max_page:
        pages.add(found + 1)
    combined = [row for page in sorted(pages) for row in fetch(page)]
    return in_window(combined, window)


def run(config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config)
    run_id = new_artifact_id("source-smoke")
    client = PublicJsonClient(**{k: v for k, v in config["http"].items() if k != "concurrency"})
    cafef, kbs, store = CafeFSource(client), KBSVnstockSource(client), RawStore(ROOT, run_id)
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
                           KBS_VERSION, "vnstock")
                kbs_by_window[label] = sorted(
                    [map_kbs_wire_ohlcv_row(row, symbol, exchange)
                     for row in response["payload"]["data_day"]], key=lambda row: row["trade_date"])
            cache = {}
            for label, window in windows.items():
                cafe_by_window[label] = locate_cafef_window(
                    cafef, store, symbol, exchange, window, label,
                    config["cafef"]["max_search_page"], cache)
            checks = {}
            for label in windows:
                krows, crows = kbs_by_window[label], cafe_by_window[label]
                checks[label] = {
                    "kbs_rows": len(krows), "cafef_rows": len(crows),
                    "kbs_date_range": [krows[0]["trade_date"], krows[-1]["trade_date"]] if krows else None,
                    "cafef_date_range": [crows[0]["trade_date"], crows[-1]["trade_date"]] if crows else None,
                    "ohlcv_valid": valid_market_rows(krows),
                    "cafef_limits_valid": bool(crows) and all(r["reference_price"] is not None
                        and r["ceiling_price"] is not None and r["floor_price"] is not None
                        and r["floor_price"] <= r["reference_price"] <= r["ceiling_price"] for r in crows),
                    "value_components_valid": bool(crows) and all(
                        all(r[f] is None or r[f] >= 0 for f in ("matched_volume", "matched_value",
                            "put_through_volume", "put_through_value", "traded_value")) for r in crows),
                }
            shared = sorted(set(r["trade_date"] for r in kbs_by_window["WINDOW_RECENT"])
                            & set(r["trade_date"] for r in cafe_by_window["WINDOW_RECENT"]))
            volume_matches = []
            for day in shared:
                kr = next(r for r in kbs_by_window["WINDOW_RECENT"] if r["trade_date"] == day)
                cr = next(r for r in cafe_by_window["WINDOW_RECENT"] if r["trade_date"] == day)
                volume_matches.append(kr["volume"] == cr["matched_volume"])
            passed = all(c["ohlcv_valid"] and c["cafef_limits_valid"] and c["value_components_valid"]
                         for c in checks.values())
            result["symbols"][symbol] = {"exchange": exchange, "status": "PASS" if passed else "FAIL",
                "checks": checks, "reconciliation": {"shared_recent_dates": len(shared),
                "volume_status": "MATCH" if volume_matches and all(volume_matches) else "VALUE_CONFLICT",
                "price_status": "PRICE_BASIS_CONFLICT", "price_comparison_performed": False}}

        for label, window in windows.items():
            response = kbs.acquire_ohlcv("VNINDEX", window["start"], window["end"], is_index=True)
            store.save("kbs", f"VNINDEX-{label.lower()}", response,
                       {"symbol": "VNINDEX", "date_range": window}, KBS_VERSION, "vnstock")
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
                   KBS_VERSION, "vnstock")
        observations = financial_raw_only_metadata(response["payload"])
        result["financial"] = {"status": "RAW_ONLY_PIT_UNRESOLVED", "observations": observations,
                               "facts_used_in_features": False}
        all_symbols = all(item["status"] == "PASS" for item in result["symbols"].values())
        benchmark_ok = all(item["valid"] and item["rows"] > 0 for item in result["benchmark"].values())
        result["overall"] = "PASS" if all_symbols and benchmark_ok else "FAIL"
    except Exception as exc:
        result["overall"] = "FAIL"
        result["stopped_error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        result["finished_at"] = utc_now()
        result["raw_artifacts"] = store.artifacts
        output = ROOT / "data" / "raw" / "source_smoke" / run_id / "result.json"
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
