"""Offline reliability audit for local REPRESENTATIVE_PILOT raw artifacts.

This is not a research gate. It never calls a provider and never modifies raw data.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from delta_t1.ingestion.representative_pilot import _map_cafef_page_rows  # noqa: E402
from delta_t1.ingestion.sources.cafef import (  # noqa: E402
    apply_invalid_row_policy, classify_cafef_page_row, map_trade_history_row,
)
from delta_t1.ingestion.sources.vnstock import map_kbs_wire_ohlcv_row  # noqa: E402
from delta_t1.io import digest, read_json  # noqa: E402


CAFEF_FILE = re.compile(r"^cafef-(?P<symbol>[A-Z0-9]+)-page-(?P<page>\d{3})\.json$")
KBS_FILE = re.compile(
    r"^kbs-(?P<symbol>[A-Z0-9]+)-(?P<start>\d{4}-\d{2}-\d{2})-(?P<end>\d{4}-\d{2}-\d{2})\.json$")
METRICS = (
    "FILES", "ROWS", "SNAPSHOTS", "PARSE_ERRORS", "SCHEMA_ERRORS",
    "QC_ERRORS", "DUPLICATE_DATES", "REPEATED_PAGES", "PAGINATION_ERRORS",
    "COVERAGE_ERRORS", "REPLAY_ERRORS",
)


def _issue(issues, kind, run_id, symbol, location, detail):
    issues.append({"kind": kind, "run_id": run_id, "symbol": symbol,
                   "location": location, "detail": detail})


def _metadata(root, raw_path, metrics, issues, run_id, symbol):
    metadata_path = raw_path.with_name(f"{raw_path.stem}.metadata.json")
    if not metadata_path.is_file():
        metrics["SCHEMA_ERRORS"] += 1
        _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name, "missing metadata")
        return None
    try:
        metadata = read_json(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        metrics["SCHEMA_ERRORS"] += 1
        _issue(issues, "SCHEMA_ERROR", run_id, symbol, metadata_path.name, str(exc))
        return None
    if (metadata.get("sha256") != digest(raw_path.read_bytes())
            or metadata.get("symbol") != symbol
            or metadata.get("raw_path") != raw_path.relative_to(root).as_posix()):
        metrics["SCHEMA_ERRORS"] += 1
        _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name,
               "raw/metadata identity or checksum mismatch")
    return metadata


def _load_universe(root):
    path = root / "configs/data/representative_pilot.universe.v1.json"
    if not path.is_file():
        return {}
    return {row["ticker"]: row for row in read_json(path)}


def _load_config(root):
    path = root / "configs/data/representative_pilot.v1.json"
    return read_json(path) if path.is_file() else {
        "start": "2020-01-01", "end": "2026-09-15", "cafef": {"page_size": 30},
        "invalid_market_row_policy": {},
    }


def _audit_cafef(root, run_id, directory, config, universe, metrics, issues):
    series = defaultdict(list)
    for raw_path in sorted(directory.iterdir()):
        match = CAFEF_FILE.fullmatch(raw_path.name)
        if not match:
            if raw_path.name.endswith(".json") and not raw_path.name.endswith(".metadata.json"):
                metrics["SCHEMA_ERRORS"] += 1
                _issue(issues, "SCHEMA_ERROR", run_id, "?", raw_path.name,
                       "unexpected CafeF artifact name")
            continue
        symbol, page = match["symbol"], int(match["page"])
        metrics["FILES"] += 1
        metadata = _metadata(root, raw_path, metrics, issues, run_id, symbol)
        try:
            payload = read_json(raw_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            metrics["SCHEMA_ERRORS"] += 1
            _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name, f"invalid JSON: {exc}")
            continue
        rows = payload.get("Data") if isinstance(payload, dict) and payload.get("Success") is True else None
        if not isinstance(rows, list):
            metrics["SCHEMA_ERRORS"] += 1
            _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name, "invalid CafeF envelope")
            continue
        metrics["ROWS"] += len(rows)
        exchange = universe.get(symbol, {}).get("exchange")
        if exchange is None and metadata:
            exchange = metadata.get("request", {}).get("exchange")
        job = {"symbol": symbol, "exchange": exchange or "UNKNOWN"}
        dates, replay_ok = [], True
        mapped_rows = []
        for index, row in enumerate(rows):
            raw_date = row.get("TradeDate") if isinstance(row, dict) else None
            if classify_cafef_page_row(raw_date, page=page, row_index=index) == "CURRENT_SNAPSHOT":
                metrics["SNAPSHOTS"] += 1
                continue
            try:
                mapped = map_trade_history_row(row, symbol, job["exchange"])
                dates.append(mapped["trade_date"])
                mapped_rows.append(mapped)
            except Exception as exc:  # fail-closed report; never repairs raw
                name = "PARSE_ERRORS" if "TradeDate" in str(exc) or "date" in str(exc).lower() else "SCHEMA_ERRORS"
                metrics[name] += 1
                replay_ok = False
                _issue(issues, name[:-1], run_id, symbol, f"page={page},row={index}",
                       f"raw_trade_date={raw_date!r}: {exc}")
        try:
            replayed = _map_cafef_page_rows(rows, job, page)
            if len(replayed) != len(dates):
                raise ValueError("execution/replay mapped row count differs")
        except Exception as exc:
            if replay_ok:
                metrics["REPLAY_ERRORS"] += 1
            _issue(issues, "REPLAY_ERROR", run_id, symbol, f"page={page}", str(exc))
        series[symbol].append({
            "page": page, "rows": len(rows), "dates": dates,
            "mapped": mapped_rows,
            "fingerprint": digest(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()),
        })

    for symbol, pages in series.items():
        pages.sort(key=lambda item: item["page"])
        page_numbers = [item["page"] for item in pages]
        expected = list(range(page_numbers[0], page_numbers[-1] + 1))
        if page_numbers != expected:
            metrics["PAGINATION_ERRORS"] += 1
            _issue(issues, "PAGINATION_ERROR", run_id, symbol, "pages", "page gap")
        repeated = sum(count - 1 for count in Counter(item["fingerprint"] for item in pages).values()
                       if count > 1)
        metrics["REPEATED_PAGES"] += repeated
        if repeated:
            _issue(issues, "REPEATED_PAGE", run_id, symbol, "pages", str(repeated))
        all_dates = [value for item in pages for value in item["dates"]]
        all_mapped = [value for item in pages for value in item["mapped"]
                      if config["start"] <= value["trade_date"] <= config["end"]]
        _, findings = apply_invalid_row_policy(
            all_mapped, config.get("invalid_market_row_policy", {}))
        unsafe = [finding for finding in findings if not finding["safe"]]
        if unsafe:
            metrics["QC_ERRORS"] += len(unsafe)
            for finding in unsafe:
                _issue(issues, "QC_ERROR", run_id, symbol,
                       f"trade_date={finding['trade_date']}",
                       "invalid CafeF price band without exact evidence-pinned exclusion")
        duplicates = len(all_dates) - len(set(all_dates))
        metrics["DUPLICATE_DATES"] += duplicates
        if duplicates:
            _issue(issues, "DUPLICATE_DATE", run_id, symbol, "pages", str(duplicates))
        for previous, current in zip(pages, pages[1:]):
            overlap = set(previous["dates"]) & set(current["dates"])
            no_progress = (previous["dates"] and current["dates"]
                           and min(current["dates"]) >= min(previous["dates"]))
            if overlap or no_progress:
                metrics["PAGINATION_ERRORS"] += 1
                _issue(issues, "PAGINATION_ERROR", run_id, symbol,
                       f"pages={previous['page']},{current['page']}",
                       f"overlap={len(overlap)} no_progress={bool(no_progress)}")
        empty_pages = [item["page"] for item in pages if item["rows"] == 0]
        empty_before_data = any(
            item["rows"] == 0 and any(later["rows"] for later in pages[index + 1:])
            for index, item in enumerate(pages))
        if empty_before_data:
            metrics["PAGINATION_ERRORS"] += 1
            _issue(issues, "PAGINATION_ERROR", run_id, symbol, "pages", "data after empty page")
        if all_dates:
            last = pages[-1]
            terminal = bool(empty_pages) or last["rows"] < config["cafef"]["page_size"]
            if terminal and min(all_dates) > config["start"]:
                metrics["COVERAGE_ERRORS"] += 1
                _issue(issues, "COVERAGE_ERROR", run_id, symbol, f"page={last['page']}",
                       f"oldest={min(all_dates)} requested_start={config['start']} source exhausted")


def _audit_kbs(root, run_id, directory, universe, metrics, issues):
    dates_by_symbol = defaultdict(list)
    for raw_path in sorted(directory.iterdir()):
        match = KBS_FILE.fullmatch(raw_path.name)
        if not match:
            if raw_path.name.endswith(".json") and not raw_path.name.endswith(".metadata.json"):
                metrics["SCHEMA_ERRORS"] += 1
                _issue(issues, "SCHEMA_ERROR", run_id, "?", raw_path.name,
                       "unexpected KBS artifact name")
            continue
        symbol = match["symbol"]
        metrics["FILES"] += 1
        metadata = _metadata(root, raw_path, metrics, issues, run_id, symbol)
        try:
            payload = read_json(raw_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            metrics["SCHEMA_ERRORS"] += 1
            _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name, f"invalid JSON: {exc}")
            continue
        rows = payload.get("data_day") if isinstance(payload, dict) else None
        if payload.get("symbol") != symbol or not isinstance(rows, list):
            metrics["SCHEMA_ERRORS"] += 1
            _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name, "invalid KBS envelope/identity")
            continue
        if not rows:
            metrics["SCHEMA_ERRORS"] += 1
            _issue(issues, "SCHEMA_ERROR", run_id, symbol, raw_path.name, "empty KBS data_day")
        metrics["ROWS"] += len(rows)
        exchange = universe.get(symbol, {}).get("exchange") or (
            metadata or {}).get("request", {}).get("exchange") or "INDEX"
        mapped_dates = []
        for index, row in enumerate(rows):
            try:
                mapped = map_kbs_wire_ohlcv_row(row, symbol, exchange, is_index=symbol == "VNINDEX")
                mapped_dates.append(mapped["trade_date"])
                if not (mapped["low"] <= mapped["open"] <= mapped["high"]
                        and mapped["low"] <= mapped["close"] <= mapped["high"]):
                    raise ValueError("OHLC bounds invalid")
            except Exception as exc:
                name = "QC_ERRORS" if "OHLC bounds" in str(exc) else "SCHEMA_ERRORS"
                metrics[name] += 1
                _issue(issues, name[:-1], run_id, symbol,
                       f"{raw_path.name}:row={index}", str(exc))
        dates_by_symbol[symbol].extend(mapped_dates)
    for symbol, values in dates_by_symbol.items():
        duplicates = len(values) - len(set(values))
        metrics["DUPLICATE_DATES"] += duplicates
        if duplicates:
            _issue(issues, "DUPLICATE_DATE", run_id, symbol, "KBS batches", str(duplicates))


def audit(root=ROOT):
    root = Path(root).resolve()
    config, universe = _load_config(root), _load_universe(root)
    metrics, issues = Counter(), []
    financial = config.get("financial", {})
    if (financial.get("mode") != "RAW_ONLY_PIT_UNRESOLVED"
            or financial.get("enabled_for_market_gate") is not False
            or financial.get("collect_raw_side_track") is not False):
        metrics["SCHEMA_ERRORS"] += 1
        _issue(issues, "SCHEMA_ERROR", "CONFIG", "FINANCIAL", "financial", "PIT isolation lock changed")
    runs_root = root / "data/raw/representative_pilot"
    run_ids = sorted(path.name for path in runs_root.glob("representative-pilot-*") if path.is_dir())
    for run_id in run_ids:
        cafef = root / "data/raw/cafef" / run_id
        kbs = root / "data/raw/kbs" / run_id
        if cafef.is_dir():
            _audit_cafef(root, run_id, cafef, config, universe, metrics, issues)
        if kbs.is_dir():
            _audit_kbs(root, run_id, kbs, universe, metrics, issues)
    return {key: metrics[key] for key in METRICS}, issues, run_ids


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--max-issues", type=int, default=50)
    args = parser.parse_args(argv)
    metrics, issues, run_ids = audit(args.root)
    for key in METRICS:
        print(f"{key}={metrics[key]}")
    failed = any(metrics[key] for key in METRICS[3:])
    print(f"FINAL_PREFLIGHT={'FAIL' if failed else 'PASS'}")
    print(f"RUNS={len(run_ids)}")
    print("AFFECTED_RUNS=" + ",".join(sorted({issue["run_id"] for issue in issues})))
    print("AFFECTED_SYMBOLS=" + ",".join(sorted({issue["symbol"] for issue in issues})))
    for issue in issues[:args.max_issues]:
        print("ISSUE " + " ".join(f"{key}={value}" for key, value in issue.items()))
    if len(issues) > args.max_issues:
        print(f"ISSUES_SUPPRESSED={len(issues) - args.max_issues}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
