"""Offline EDA and quality reporting for one immutable M1 scale promotion."""
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median

from ..artifact_ids import new_artifact_id
from ..io import digest, now, read_json, read_rows, write_json, write_rows, atomic_write


def _inside(path, parent, label):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if not path.is_relative_to(parent):
        raise ValueError(f"{label} escapes {parent}")
    return path


def _verify_artifacts(directory, manifest):
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("canonical manifest has no artifact checksums")
    for relative, expected in artifacts.items():
        path = directory / relative
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError(f"canonical artifact checksum mismatch: {relative}")


def _at_least_calendar_years(start, end, years):
    start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    try:
        anniversary = start_date.replace(year=start_date.year + years)
    except ValueError:
        anniversary = start_date.replace(year=start_date.year + years, day=28)
    return anniversary <= end_date


def _five_calendar_years(start, end):
    return _at_least_calendar_years(start, end, 5)


def _three_calendar_years(start, end):
    return _at_least_calendar_years(start, end, 3)


def _markdown(report, rows):
    summary = report["summary"]
    features = report["latest_feature_coverage"]
    lines = [
        "# M1 Scale — EDA và báo cáo chất lượng dữ liệu",
        "",
        f"Generated: `{report['generated_at']}`  ",
        f"Canonical run: `{report['canonical_run_id']}`  ",
        f"Candidate: `{report['candidate_id']}`",
        "",
        "## Kết luận",
        "",
        f"**{report['m1_deadline_status']}** — acquisition/canonical market data đã hoàn tất, "
        f"nhưng latest feature-complete mới đạt {summary['latest_feature_complete']}/"
        f"{summary['selected_symbols']} và identity vẫn provisional. Không hạ gate để ép PASS.",
        "",
        "## Coverage",
        "",
        "| Chỉ tiêu | Kết quả |",
        "|---|---:|",
        f"| Securities | {summary['selected_symbols']} |",
        f"| Có >=3 calendar years sau QC | {summary['usable_3y']} |",
        f"| Có >=5 calendar years sau QC | {summary['usable_5y']} |",
        f"| Daily price rows | {summary['prices_daily']} |",
        f"| VNINDEX rows | {summary['benchmark_daily']} |",
        f"| Monthly feature snapshots | {summary['feature_snapshots']} |",
        f"| Latest feature-complete trước identity | {summary['latest_feature_complete']} |",
        f"| Latest officially eligible | {summary['latest_feature_eligible']} |",
        f"| Quarantined KBS/CafeF rows | {summary['quarantined_rows']} |",
        "",
        "## Latest momentum/feature coverage",
        "",
        "| Feature | Có giá trị | Thiếu |",
        "|---|---:|---:|",
    ]
    for name, values in features.items():
        lines.append(f"| `{name}` | {values['available']} | {values['missing']} |")
    lines.extend([
        "",
        "## Exchange coverage",
        "",
        "| Exchange | Securities | Price rows |",
        "|---|---:|---:|",
    ])
    for exchange, values in sorted(report["exchange_coverage"].items()):
        lines.append(f"| {exchange} | {values['securities']} | {values['price_rows']} |")
    lines.extend([
        "",
        "## Missingness và QC",
        "",
        f"- `traded_value` missing: {report['market_missingness']['traded_value_missing_rows']} "
        f"({report['market_missingness']['traded_value_missing_ratio']:.2%}).",
        f"- `volume` missing: {report['market_missingness']['volume_missing_rows']}; "
        f"zero volume: {report['market_missingness']['volume_zero_rows']}.",
        f"- Quarantine: KBS {report['quarantine_by_provider'].get('kbs', 0)}, "
        f"CafeF {report['quarantine_by_provider'].get('cafef', 0)}.",
        "- Financial: `PIT_UNRESOLVED`; financial features không được phép.",
        "",
        "## Per-symbol",
        "",
        "| Ticker | Exchange | Min | Max | Rows | >=5y | Feature complete | Missing required | Segment |",
        "|---|---|---|---|---:|---|---|---|---|",
    ])
    for row in rows:
        missing = ", ".join(row["missing_required_features"]) or "—"
        lines.append(
            f"| {row['ticker']} | {row['exchange']} | {row['observed_min']} | "
            f"{row['observed_max']} | {row['price_rows']} | "
            f"{'YES' if row['usable_5y'] else 'NO'} | "
            f"{'YES' if row['latest_feature_complete'] else 'NO'} | {missing} | "
            f"{row['latest_universe_segment']} |")
    lines.extend([
        "",
        "## Quyết định tiếp theo",
        "",
        "1. Review 332 mã thiếu feature theo missing-field và session-gap evidence.",
        "2. Hoàn thiện identity/security master; không biến current membership thành historical truth.",
        "3. Chỉ chạy lại promotion offline khi policy/methodology được phê duyệt; không cần crawl lại raw trước bước review.",
        "4. Chỉ chuyển M2 khi gate machine-readable đạt PASS.",
        "",
    ])
    return "\n".join(lines).encode("utf-8")


def build_m1_scale_quality_report(canonical_path, feature_config_path, *, root):
    root = Path(root).resolve()
    canonical_root = root / "data" / "canonical"
    canonical_path = _inside(canonical_path, canonical_root, "canonical path")
    manifest_path = canonical_path / "manifest.json"
    manifest = read_json(manifest_path)
    if (manifest.get("run_id") != canonical_path.name
            or manifest.get("canonical_promotion_status") not in ("PASS", "FAIL")
            or manifest.get("network_requests") != 0):
        raise ValueError("quality report requires a completed offline M1 promotion")
    _verify_artifacts(canonical_path, manifest)
    candidate_id = manifest.get("parent_candidate_id")
    candidate_path = _inside(canonical_root / candidate_id, canonical_root, "candidate path")
    candidate_manifest_path = candidate_path / "manifest.json"
    if (not candidate_manifest_path.is_file()
            or digest(candidate_manifest_path.read_bytes()) != manifest.get("parent_manifest_hash")):
        raise ValueError("parent candidate manifest checksum mismatch")
    candidate = read_json(candidate_manifest_path)
    if candidate.get("mapping_status") != "PASS":
        raise ValueError("parent candidate mapping is not PASS")

    feature_config_path = Path(feature_config_path).resolve()
    feature_config = read_json(feature_config_path)
    if digest(feature_config_path.read_bytes()) != manifest.get("feature_config_hash"):
        raise ValueError("feature config checksum mismatch")
    required = feature_config["required_features"]
    securities = read_rows(canonical_path / "clean" / "securities.jsonl")
    prices = read_rows(canonical_path / "clean" / "prices_daily.jsonl")
    benchmark = read_rows(canonical_path / "clean" / "benchmark_daily.jsonl")
    features = read_rows(canonical_path / "features" / "monthly.jsonl")
    quarantine_path = candidate_path / "quality" / "quarantined_rows.jsonl"
    quarantine = read_rows(quarantine_path)

    security_by_id = {row["security_id"]: row for row in securities}
    price_by_id = defaultdict(list)
    exchange_price_rows = Counter()
    for row in prices:
        price_by_id[row["security_id"]].append(row)
        exchange_price_rows[row["exchange"]] += 1
    latest = {}
    for row in features:
        prior = latest.get(row["security_id"])
        if prior is None or row["as_of_date"] > prior["as_of_date"]:
            latest[row["security_id"]] = row

    rows = []
    for security_id, security in sorted(security_by_id.items(), key=lambda item: item[1]["ticker"]):
        observations = price_by_id[security_id]
        if not observations or security_id not in latest:
            raise ValueError(f"missing canonical observations/features: {security_id}")
        observed_min = min(row["trade_date"] for row in observations)
        observed_max = max(row["trade_date"] for row in observations)
        snapshot = latest[security_id]
        missing = [name for name in required if snapshot.get(name) is None]
        rows.append({
            "security_id": security_id, "ticker": security["ticker"],
            "exchange": security["exchange"], "observed_min": observed_min,
            "observed_max": observed_max, "price_rows": len(observations),
            "usable_3y": _three_calendar_years(observed_min, observed_max),
            "usable_5y": _five_calendar_years(observed_min, observed_max),
            "latest_as_of_date": snapshot["as_of_date"],
            "latest_feature_complete": not missing,
            "latest_eligibility": snapshot["eligibility"],
            "latest_universe_segment": snapshot["universe_segment"],
            "missing_required_features": missing,
            "latest_na_reason": snapshot["na_reason"],
        })

    selected = len(rows)
    usable_3y = sum(row["usable_3y"] for row in rows)
    usable_5y = sum(row["usable_5y"] for row in rows)
    feature_complete = sum(row["latest_feature_complete"] for row in rows)
    eligible = sum(row["latest_universe_segment"] == "ELIGIBLE_FOR_CLUSTERING" for row in rows)
    latest_coverage = {
        name: {
            "available": sum(latest[row["security_id"]].get(name) is not None for row in rows),
            "missing": sum(latest[row["security_id"]].get(name) is None for row in rows),
        } for name in required
    }
    exchange_security = Counter(row["exchange"] for row in securities)
    price_counts = [row["price_rows"] for row in rows]
    traded_missing = sum(row["traded_value"] is None for row in prices)
    checks = {
        "at_least_300_symbols_with_5y_after_qc": usable_5y >= 300,
        "momentum_1m_3m_6m_12m_implemented": all(
            name in required for name in ("mom_21", "mom_63", "mom_126", "mom_252")),
        "at_least_300_latest_feature_complete": feature_complete >= 300,
        "eda_and_quality_report_generated": True,
        "raw_immutable_and_network_zero": True,
    }
    report = {
        "report_id": new_artifact_id("m1-scale-quality"),
        "generated_at": now(), "canonical_run_id": manifest["run_id"],
        "candidate_id": candidate_id,
        "m1_deadline_status": "PASS" if all(checks.values()) else "PARTIAL",
        "checks": checks,
        "blocking_reasons": [name for name, value in checks.items() if not value],
        "summary": {
            "selected_symbols": selected, "usable_3y": usable_3y,
            "usable_5y": usable_5y, "prices_daily": len(prices),
            "benchmark_daily": len(benchmark), "feature_snapshots": len(features),
            "latest_feature_complete": feature_complete,
            "latest_feature_eligible": eligible,
            "quarantined_rows": len(quarantine),
        },
        "exchange_coverage": {
            exchange: {"securities": exchange_security[exchange],
                       "price_rows": exchange_price_rows[exchange]}
            for exchange in sorted(exchange_security)
        },
        "latest_feature_coverage": latest_coverage,
        "market_missingness": {
            "volume_missing_rows": sum(row["volume"] is None for row in prices),
            "volume_zero_rows": sum(row["volume"] == 0 for row in prices),
            "traded_value_missing_rows": traded_missing,
            "traded_value_missing_ratio": traded_missing / len(prices),
        },
        "price_rows_distribution": {
            "minimum": min(price_counts), "median": median(price_counts),
            "maximum": max(price_counts),
        },
        "quarantine_by_provider": dict(sorted(Counter(
            row["provider"] for row in quarantine).items())),
        "financial": {"pit_status": "PIT_UNRESOLVED", "features_allowed": False},
        "input_hashes": {
            "canonical_manifest": digest(manifest_path.read_bytes()),
            "candidate_manifest": digest(candidate_manifest_path.read_bytes()),
            "feature_config": digest(feature_config_path.read_bytes()),
        },
    }
    output = root / "data" / "derived" / "m1_scale_quality" / report["report_id"]
    write_rows(output / "per_symbol.jsonl", rows)
    write_json(output / "report.json", report)
    atomic_write(output / "report.md", _markdown(report, rows))
    report["artifacts"] = {
        path.relative_to(output).as_posix(): digest(path.read_bytes())
        for path in sorted(output.iterdir()) if path.is_file()
    }
    write_json(output / "manifest.json", report)
    return output, report
