"""Offline EDA and quality reporting for one immutable M1 scale promotion."""
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from ..artifact_ids import new_artifact_id
from ..features.market import at_least_calendar_years, latest_completed_snapshot_rows
from ..io import atomic_write, digest, now, read_json, read_rows, write_json, write_rows
from .m1_scale import evaluate_m1_readiness_checks

try:
    import matplotlib
    matplotlib.use("Agg")  # offline / non-interactive backend
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MATPLOTLIB_AVAILABLE = False


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


# ---------------------------------------------------------------------------
# EDA plot generation
# ---------------------------------------------------------------------------

_REQUIRED_FEATURES = (
    "mom_21", "mom_63", "mom_126", "mom_252",
    "vol_63", "mdd_126", "beta_126", "liquidity_21",
)


def _generate_plots(report, rows, plots_dir):
    """Generate exactly four deterministic EDA charts into plots_dir.

    Returns a dict mapping plot key -> relative path string (or None if
    matplotlib is unavailable).  Does NOT raise on partial failure;
    individual plot errors are surfaced via returned None values.

    Note on session coverage: the coverage shown is relative to the
    *observed canonical exchange-session union*, NOT a verified official
    HOSE/HNX/UPCOM exchange calendar.  The label explicitly reflects this.
    """
    if not _MATPLOTLIB_AVAILABLE:
        return {name: None for name in (
            "exchange_distribution", "observed_session_coverage",
            "feature_availability", "exclusion_reasons",
        )}

    plots_dir = Path(plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    # 1. Securities by exchange (bar chart) -----------------------------------
    try:
        exchange_data = report.get("exchange_coverage", {})
        exchanges = sorted(exchange_data)
        counts = [exchange_data[ex]["securities"] for ex in exchanges]
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(exchanges, counts, color=["#2196F3", "#4CAF50", "#FF9800"][:len(exchanges)])
        ax.bar_label(bars, padding=3)
        ax.set_title("Securities by Exchange")
        ax.set_ylabel("Number of Securities")
        ax.set_xlabel("Exchange")
        ax.set_ylim(0, max(counts) * 1.15 if counts else 1)
        fig.tight_layout()
        path = plots_dir / "exchange_distribution.png"
        fig.savefig(path, dpi=100)
        plt.close(fig)
        results["exchange_distribution"] = path.name
    except Exception:  # pragma: no cover
        results["exchange_distribution"] = None

    # 2. Session coverage distribution (histogram) ----------------------------
    try:
        coverages = [
            row["observed_session_coverage"]
            for row in rows
            if row.get("observed_session_coverage") is not None
        ]
        med = median(coverages) if coverages else None
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(coverages, bins=40, color="#5C6BC0", edgecolor="white", linewidth=0.4)
        if med is not None:
            ax.axvline(med, color="#E53935", linestyle="--", linewidth=1.5,
                       label=f"Median {med:.2%}")
            ax.legend(fontsize=9)
        ax.set_title(
            "Coverage vs. Observed Exchange Sessions\n"
            "(relative to observed canonical session union, NOT official exchange calendar)"
        )
        ax.set_xlabel("Coverage vs. Observed Exchange Sessions")
        ax.set_ylabel("Symbols")
        fig.tight_layout()
        path = plots_dir / "observed_session_coverage.png"
        fig.savefig(path, dpi=100)
        plt.close(fig)
        results["observed_session_coverage"] = path.name
    except Exception:  # pragma: no cover
        results["observed_session_coverage"] = None

    # 3. Required feature availability (bar chart) ----------------------------
    try:
        feature_cov = report.get("latest_feature_coverage", {})
        total = report.get("summary", {}).get("selected_symbols", 500)
        feat_names = list(_REQUIRED_FEATURES)
        available = [feature_cov.get(f, {}).get("available", 0) for f in feat_names]
        missing = [feature_cov.get(f, {}).get("missing", total - available[i])
                   for i, f in enumerate(feat_names)]
        x = range(len(feat_names))
        fig, ax = plt.subplots(figsize=(9, 4))
        bar_avail = ax.bar(x, available, label="Available", color="#43A047")
        bar_miss = ax.bar(x, missing, bottom=available, label="Missing", color="#EF5350")
        ax.bar_label(bar_avail, labels=[str(v) for v in available],
                     padding=2, fontsize=8)
        ax.set_xticks(list(x))
        ax.set_xticklabels(feat_names, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Symbols")
        ax.set_title("Required Feature Availability at Latest Completed Snapshot")
        ax.set_ylim(0, total * 1.12)
        ax.axhline(total, color="#0D47A1", linestyle=":", linewidth=1, label=f"Total ({total})")
        ax.legend(fontsize=9)
        fig.tight_layout()
        path = plots_dir / "feature_availability.png"
        fig.savefig(path, dpi=100)
        plt.close(fig)
        results["feature_availability"] = path.name
    except Exception:  # pragma: no cover
        results["feature_availability"] = None

    # 4. Top exclusion/missing-feature reasons (horizontal bar) ---------------
    try:
        reason_counts = report.get("exclusion_reason_counts", {})
        # Show top 12; distinguish historical_identity from market-feature reasons
        top = sorted(reason_counts.items(), key=lambda kv: -kv[1])[:12]
        labels = [item[0] for item in top]
        counts = [item[1] for item in top]
        colors = [
            "#7B1FA2" if "historical_identity" in lbl else "#1565C0"
            for lbl in labels
        ]
        fig, ax = plt.subplots(figsize=(10, max(3, len(labels) * 0.55)))
        bars = ax.barh(range(len(labels)), counts, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels([lbl.replace(":", ":\n  ") for lbl in labels], fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("Symbol-count")
        ax.set_title("Top Exclusion / Missing-Feature Reasons")
        legend_handles = [
            plt.Rectangle((0, 0), 1, 1, color="#7B1FA2", label="historical_identity"),
            plt.Rectangle((0, 0), 1, 1, color="#1565C0", label="market-feature"),
        ]
        ax.legend(handles=legend_handles, fontsize=8, loc="lower right")
        fig.tight_layout()
        path = plots_dir / "exclusion_reasons.png"
        fig.savefig(path, dpi=100)
        plt.close(fig)
        results["exclusion_reasons"] = path.name
    except Exception:  # pragma: no cover
        results["exclusion_reasons"] = None

    return results


def _markdown(report, rows, plot_names=None):
    summary = report["summary"]
    features = report["latest_feature_coverage"]
    incomplete = summary["selected_symbols"] - summary["latest_feature_complete"]
    mfsr = report.get("market_feature_stage_ready", False)
    plot_names = plot_names or {}
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
        "## Readiness summary",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| `market_feature_stage_ready` | {'✓ true' if mfsr else '✗ false'} |",
        f"| `research_stage_ready` | {'✓ true' if report.get('research_stage_ready') else '✗ false'} |",
        f"| `feature_stage_ready` *(deprecated alias = strict gate)* "
        f"| {'✓ true' if report.get('feature_stage_ready') else '✗ false'} |",
        "",
        "> **Lưu ý:** `market_feature_stage_ready = true` KHÔNG có nghĩa historical identity",
        "> đã verify, financial PIT đã giải quyết, clustering sample đã approved, hay research",
        "> gate PASS. Đây chỉ là bằng chứng rằng canonical promotion đã thành công và",
        "> market feature artifact đã được tạo.",
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
        # NOTE: label is 'coverage_vs_observed_exchange_sessions', NOT 'observed_session_coverage'.
        # This is coverage relative to the *observed canonical exchange-session union*,
        # NOT proof of complete official HOSE/HNX/UPCOM exchange calendar coverage.
        f"| Coverage vs. observed exchange sessions | {coverage['minimum']:.2%} | "
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
    # Embed EDA charts (relative paths; report remains readable if images are absent)
    lines.extend(["", "## EDA Charts", ""])
    chart_specs = [
        ("exchange_distribution", "1. Securities by Exchange"),
        ("observed_session_coverage",
         "2. Coverage vs. Observed Exchange Sessions"
         " *(relative to observed canonical session union, NOT official exchange calendar)*"),
        ("feature_availability", "3. Required Feature Availability"),
        ("exclusion_reasons", "4. Top Exclusion / Missing-Feature Reasons"),
    ]
    has_any_plot = False
    for key, caption in chart_specs:
        fname = plot_names.get(key)
        if fname:
            lines.append(f"### {caption}")
            lines.append(f"")
            lines.append(f"![{caption}](plots/{fname})")
            lines.append(f"")
            has_any_plot = True
        else:
            lines.append(f"### {caption}")
            lines.append("")
            lines.append("*Chart unavailable (matplotlib not installed or generation failed).*")
            lines.append("")
    if not has_any_plot:
        lines.append(
            "> Install the `research` optional dependency (`pip install -e .[research]`) "
            "to generate plots."
        )
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
        "> `historical_identity:provisional_observed_interval_only` phản ánh rằng identity",
        "> chỉ là *observed interval* (không phải complete historical membership). Đây KHÔNG",
        "> phải là lỗi trong tính toán market feature.",
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
        # market_feature_stage_ready is independent from strict research gate.
        # true iff canonical promotion succeeded AND market feature artifact was generated.
        # Does NOT imply historical identity verified, financial PIT resolved,
        # clustering sample approved, or research gate passing.
        "market_feature_stage_ready": (
            manifest.get("canonical_promotion_status") == "PASS"
            and bool(features)
        ),
        "feature_stage_ready": False,  # deprecated alias: strict research gate (always FAIL here)
        "research_stage_ready": False,  # strict gate (historical identity + PIT + policy)
    }
    output = root / "data" / "derived" / "m1_scale_quality" / report["report_id"]
    write_rows(output / "per_symbol.jsonl", rows)
    write_json(output / "report.json", report)
    # Generate EDA plots (requires matplotlib; gracefully absent if unavailable)
    plot_names = _generate_plots(report, rows, output / "plots")
    atomic_write(output / "report.md", _markdown(report, rows, plot_names=plot_names))
    report["artifacts"] = {
        path.relative_to(output).as_posix(): digest(path.read_bytes())
        for path in sorted(output.rglob("*")) if path.is_file()
    }
    write_json(output / "manifest.json", report)
    return output, report
