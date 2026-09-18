"""Offline EDA and quality reporting for one immutable M1 scale promotion."""
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from ..artifact_ids import new_artifact_id
from ..features.market import at_least_calendar_years, latest_completed_snapshot_rows
from ..io import atomic_write, digest, now, read_json, read_rows, write_json, write_rows
from .m1_scale import evaluate_m1_readiness_checks


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
    return at_least_calendar_years(start, end, years)


def _five_calendar_years(start, end):
    return _at_least_calendar_years(start, end, 5)


def _three_calendar_years(start, end):
    return _at_least_calendar_years(start, end, 3)


def _percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires observations")
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _history_evidence(observed_dates, open_session_dates):
    """Describe span and density independently, without a new pass threshold."""
    observed = sorted(set(observed_dates))
    if not observed:
        raise ValueError("history evidence requires observed prices")
    first, last = observed[0], observed[-1]
    expected = sorted(day for day in set(open_session_dates) if first <= day <= last)
    observed_sessions = len(set(observed) & set(expected))
    expected_count = len(expected)
    return {
        "observed_first_date": first,
        "observed_last_date": last,
        "price_rows": len(observed),
        "observed_span_3y": _three_calendar_years(first, last),
        "observed_span_5y": _five_calendar_years(first, last),
        "expected_open_sessions_in_observed_range": expected_count,
        "observed_open_sessions": observed_sessions,
        "missing_sessions_in_observed_range": max(expected_count - observed_sessions, 0),
        "observed_session_coverage": (
            observed_sessions / expected_count if expected_count else None
        ),
    }


def _markdown(report, rows):
    summary = report["summary"]
    features = report["latest_feature_coverage"]
    incomplete = summary["selected_symbols"] - summary["latest_feature_complete"]
    lines = [
        "# M1 Scale — EDA và báo cáo chất lượng dữ liệu",
        "",
        f"Generated: `{report['generated_at']}`  ",
        f"Canonical run: `{report['canonical_run_id']}`  ",
        f"Candidate: `{report['candidate_id']}`",
        "",
        "## Kết luận",
        "",
        f"**{report['m1_status']}** — collection/canonical market artifact đã hoàn tất. "
        f"Tại snapshot tháng hoàn tất `{summary['latest_completed_snapshot']}`, "
        f"feature-complete = {summary['latest_feature_complete']}/"
        f"{summary['selected_symbols']}, market-feature-ready = "
        f"{summary['market_feature_ready']}/{summary['selected_symbols']}, "
        f"historical-identity-ready = {summary['historical_identity_ready']}/"
        f"{summary['selected_symbols']} và research-ready = "
        f"{summary['research_ready']}/{summary['selected_symbols']}. "
        "Identity provisional và financial PIT vẫn được giữ fail-closed.",
        "",
        "## Coverage và readiness độc lập",
        "",
        "| Chỉ tiêu | Kết quả |",
        "|---|---:|",
        f"| Securities selected | {summary['selected_symbols']} |",
        f"| Observed calendar span >=3y | {summary['observed_span_3y']} |",
        f"| Observed calendar span >=5y | {summary['observed_span_5y']} |",
        f"| Daily price rows | {summary['prices_daily']} |",
        f"| VNINDEX rows | {summary['benchmark_daily']} |",
        f"| Monthly feature snapshots | {summary['feature_snapshots']} |",
        f"| Latest completed research snapshot | {summary['latest_completed_snapshot']} |",
        f"| Latest feature-complete | {summary['latest_feature_complete']} |",
        f"| Market-feature-ready | {summary['market_feature_ready']} |",
        f"| Historical-identity-ready | {summary['historical_identity_ready']} |",
        f"| Research-ready | {summary['research_ready']} |",
        f"| Legacy/scoped eligibility | {summary['legacy_scoped_eligible']} |",
        f"| Quarantined KBS/CafeF rows | {summary['quarantined_rows']} |",
        "",
        "Calendar span là evidence về khoảng thời gian quan sát, không đồng nghĩa "
        "với usable density. Session coverage và feature readiness được báo riêng.",
        "",
        "## Required-feature availability",
        "",
        "| Feature | Có giá trị | Thiếu |",
        "|---|---:|---:|",
    ]
    for name, values in features.items():
        lines.append(f"| `{name}` | {values['available']} | {values['missing']} |")
    distribution = report["price_rows_distribution"]
    coverage = report["session_coverage_distribution"]
    lines.extend([
        "",
        "## History density",
        "",
        "| Metric | Min | P25 | Median | P75 | Max |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Price rows | {distribution['minimum']} | {distribution['p25']:.1f} | "
        f"{distribution['median']:.1f} | {distribution['p75']:.1f} | "
        f"{distribution['maximum']} |",
        f"| Observed-session coverage | {coverage['minimum']:.2%} | "
        f"{coverage['p25']:.2%} | {coverage['median']:.2%} | "
        f"{coverage['p75']:.2%} | {coverage['maximum']:.2%} |",
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
        "## Top exclusion/missing-feature reasons",
        "",
        "| Reason | Count |",
        "|---|---:|",
    ])
    for reason, count in list(report["exclusion_reason_counts"].items())[:20]:
        lines.append(f"| `{reason}` | {count} |")
    lines.extend([
        "",
        "## Per-symbol",
        "",
        "| Ticker | Exchange | First | Last | Rows | Span >=5y | Session coverage | "
        "Lookback obs | Feature complete | Market ready | Identity ready | Research ready |",
        "|---|---|---|---|---:|---|---:|---:|---|---|---|---|",
    ])
    for row in rows:
        coverage_value = row["observed_session_coverage"]
        coverage_text = f"{coverage_value:.2%}" if coverage_value is not None else "—"
        lines.append(
            f"| {row['ticker']} | {row['exchange']} | {row['observed_first_date']} | "
            f"{row['observed_last_date']} | {row['price_rows']} | "
            f"{'YES' if row['observed_span_5y'] else 'NO'} | {coverage_text} | "
            f"{row['recent_lookback_observations']} | "
            f"{'YES' if row['latest_feature_complete'] else 'NO'} | "
            f"{'YES' if row['market_feature_ready'] else 'NO'} | "
            f"{'YES' if row['historical_identity_ready'] else 'NO'} | "
            f"{'YES' if row['research_ready'] else 'NO'} |"
        )
    lines.extend([
        "",
        "## Quyết định tiếp theo",
        "",
        f"1. Review {incomplete} mã thiếu required feature theo missing-field và session-gap evidence.",
        "2. Phê duyệt density/research sample-size policy; report không tự đặt threshold.",
        "3. Hoàn thiện historical identity/security master; không biến current membership thành historical truth.",
        "4. Giải quyết financial PIT theo publication/revision evidence; không giả định.",
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
            or manifest.get("canonical_promotion_status") != "PASS"
            or manifest.get("network_requests") != 0
            or manifest.get("schema_version") != "1.5.0"):
        raise ValueError("quality report requires a completed offline M1 promotion v1.5")
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
    calendar = read_rows(canonical_path / "clean" / "trading_calendar.jsonl")
    features = read_rows(canonical_path / "features" / "monthly.jsonl")
    quarantine = read_rows(candidate_path / "quality" / "quarantined_rows.jsonl")

    latest_completed_snapshot, latest = latest_completed_snapshot_rows(
        features, manifest["collection_end"]
    )
    security_by_id = {row["security_id"]: row for row in securities}
    if set(latest) != set(security_by_id):
        raise ValueError("latest completed snapshot does not cover the exact M1 universe")
    price_by_id = defaultdict(list)
    exchange_price_rows = Counter()
    for row in prices:
        price_by_id[row["security_id"]].append(row)
        exchange_price_rows[row["exchange"]] += 1
    open_sessions = defaultdict(list)
    for row in calendar:
        if row["is_open"]:
            open_sessions[row["exchange"]].append(row["trade_date"])

    rows = []
    missing_feature_counts = Counter()
    reason_counts = Counter()
    for security_id, security in sorted(
            security_by_id.items(), key=lambda item: item[1]["ticker"]):
        observations = price_by_id[security_id]
        if not observations:
            raise ValueError(f"missing canonical observations: {security_id}")
        snapshot = latest[security_id]
        missing = [name for name in required if snapshot.get(name) is None]
        missing_feature_counts.update(missing)
        gating_reason_keys = {
            "history", "trading_status", "metadata", "historical_identity",
        }
        reason_counts.update(
            f"{key}:{value}" for key, value in snapshot["na_reason"].items()
            if key in required or key in gating_reason_keys
        )
        evidence = _history_evidence(
            [row["trade_date"] for row in observations],
            open_sessions[security["exchange"]],
        )
        rows.append({
            "security_id": security_id, "ticker": security["ticker"],
            "exchange": security["exchange"], **evidence,
            "latest_completed_snapshot": snapshot["as_of_date"],
            "recent_lookback_observations": snapshot["lookback_observations"],
            "recent_missing_sessions": snapshot["missing_count"],
            "latest_feature_complete": snapshot["feature_complete"],
            "market_feature_ready": snapshot["market_feature_ready"],
            "historical_identity_ready": snapshot["historical_identity_ready"],
            "research_ready": snapshot["research_ready"],
            "legacy_scoped_eligibility": snapshot["eligibility"],
            "latest_universe_segment": snapshot["universe_segment"],
            "missing_required_features": missing,
            "latest_na_reason": snapshot["na_reason"],
        })

    selected = len(rows)
    observed_span_3y = sum(row["observed_span_3y"] for row in rows)
    observed_span_5y = sum(row["observed_span_5y"] for row in rows)
    feature_complete = sum(row["latest_feature_complete"] for row in rows)
    market_ready = sum(row["market_feature_ready"] for row in rows)
    identity_ready = sum(row["historical_identity_ready"] for row in rows)
    research_ready = sum(row["research_ready"] for row in rows)
    legacy_eligible = sum(row["legacy_scoped_eligibility"] for row in rows)
    latest_coverage = {
        name: {
            "available": sum(latest[row["security_id"]].get(name) is not None for row in rows),
            "missing": sum(latest[row["security_id"]].get(name) is None for row in rows),
        } for name in required
    }
    exchange_security = Counter(row["exchange"] for row in securities)
    price_counts = [row["price_rows"] for row in rows]
    session_coverages = [
        row["observed_session_coverage"] for row in rows
        if row["observed_session_coverage"] is not None
    ]
    traded_missing = sum(row["traded_value"] is None for row in prices)
    checks = {
        **evaluate_m1_readiness_checks(
            selected=selected, observed_span_3y=observed_span_3y,
            observed_span_5y=observed_span_5y,
            historical_identity_ready=identity_ready,
            market_feature_artifact_generated=bool(features),
        ),
        "momentum_1m_3m_6m_12m_implemented": all(
            name in required for name in ("mom_21", "mom_63", "mom_126", "mom_252")),
        "latest_completed_snapshot_selected": bool(latest_completed_snapshot),
        "market_feature_readiness_reported": True,
        "eda_and_quality_report_generated": True,
        "raw_immutable_and_network_zero": True,
    }
    report = {
        "report_id": new_artifact_id("m1-scale-quality"),
        "generated_at": now(), "canonical_run_id": manifest["run_id"],
        "candidate_id": candidate_id, "network_requests": 0,
        "m1_status": "PASS" if all(checks.values()) else "PARTIAL",
        "m1_gate_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "blocking_reasons": [name for name, value in checks.items() if not value],
        "summary": {
            "selected_symbols": selected, "observed_span_3y": observed_span_3y,
            "observed_span_5y": observed_span_5y, "prices_daily": len(prices),
            "benchmark_daily": len(benchmark), "feature_snapshots": len(features),
            "latest_completed_snapshot": latest_completed_snapshot,
            "latest_feature_complete": feature_complete,
            "market_feature_ready": market_ready,
            "historical_identity_ready": identity_ready,
            "research_ready": research_ready,
            "legacy_scoped_eligible": legacy_eligible,
            "quarantined_rows": len(quarantine),
        },
        "research_sample_size": {
            "policy_status": "UNRESOLVED", "approved_threshold": None,
            "latest_completed_market_feature_ready": market_ready,
            "latest_completed_research_ready": research_ready,
        },
        "exchange_coverage": {
            exchange: {"securities": exchange_security[exchange],
                       "price_rows": exchange_price_rows[exchange]}
            for exchange in sorted(exchange_security)
        },
        "latest_feature_coverage": latest_coverage,
        "missing_required_feature_counts": dict(sorted(missing_feature_counts.items())),
        "exclusion_reason_counts": dict(sorted(
            reason_counts.items(), key=lambda item: (-item[1], item[0])
        )),
        "market_missingness": {
            "volume_missing_rows": sum(row["volume"] is None for row in prices),
            "volume_zero_rows": sum(row["volume"] == 0 for row in prices),
            "traded_value_missing_rows": traded_missing,
            "traded_value_missing_ratio": traded_missing / len(prices),
        },
        "price_rows_distribution": {
            "minimum": min(price_counts), "p25": _percentile(price_counts, .25),
            "median": median(price_counts), "p75": _percentile(price_counts, .75),
            "maximum": max(price_counts),
        },
        "session_coverage_distribution": {
            "minimum": min(session_coverages), "p25": _percentile(session_coverages, .25),
            "median": median(session_coverages),
            "p75": _percentile(session_coverages, .75),
            "maximum": max(session_coverages),
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
