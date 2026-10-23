"""M3-B Market-only: read verified artifacts without importing research/model code.

Run: python -m streamlit run m3_dashboard.py
Loaders and queries are also importable without Streamlit for offline verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import date
from html import escape
from pathlib import Path


# 1. CONFIG / CONSTANTS
ROOT = Path(__file__).resolve().parent
MARKET_FEATURES = (
    "mom_21", "mom_63", "mom_126", "mom_252",
    "vol_63", "mdd_126", "beta_126", "liquidity_21",
)
SCATTER_X = "liquidity_21"
SCATTER_Y = "beta_126"
# Fixed display-scale constant in VND. No source values or model inputs change.
LIQUIDITY_SYMLOG_CONSTANT = 1_000_000_000
HANDOFF_DIR = "M2/artifacts/m2-final-handoff-v1"
FEATURE_DIR = "artifacts/cafef_primary/cafef-c8-complete-only-v2"
SOURCES = {
    "manifest": f"{HANDOFF_DIR}/m2_to_m3_handoff_manifest.json",
    "labels": f"{HANDOFF_DIR}/m2_cluster_labels_for_m3.csv",
    "profiles": f"{HANDOFF_DIR}/m2_cluster_profiles_for_m3.csv",
    "features": f"{FEATURE_DIR}/canonical/feature_snapshots.jsonl",
    "feature_manifest": f"{FEATURE_DIR}/manifest.json",
    "development_manifest": "M2/artifacts/m2-task4-kmeans-baseline-v1/manifest.json",
    "holdout_manifest": "M2/artifacts/m2-final-holdout/manifest.json",
    "securities": f"{FEATURE_DIR}/canonical/securities.jsonl",
}
SUMMARY_DATES = {
    "MEDIAN_DEVELOPMENT_60M": "development",
    "MEDIAN_HOLDOUT_24M": "holdout",
    "MEDIAN_OVERALL_84M": "overall",
}


class DataContractError(ValueError):
    """Invalid or ambiguous evidence must stop data display."""


def _require(condition, message):
    if not condition:
        raise DataContractError(message)


# 2. DATA LOADING (uncached; UI caching is confined to main)
def _read_json(path):
    with Path(path).open(encoding="utf-8-sig") as handle:
        value = json.load(handle)
    _require(isinstance(value, dict), f"{path}: JSON phải là object")
    return value


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_fingerprints(root=ROOT):
    """Changed files invalidate UI cache; no cache is used in offline tests."""
    paths = [Path(root) / relative for relative in SOURCES.values()]
    paths.append(Path(__file__))
    return tuple(
        (str(path.resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        for path in paths for stat in [path.stat()]
    )


def _read_csv(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        _require(len(fields) == len(set(fields)), f"{path}: duplicate columns")
        _require(set(required) <= set(fields), f"{path}: thiếu required columns")
        rows = []
        for line, row in enumerate(reader, 2):
            _require(None not in row and None not in row.values(),
                     f"{path}:{line}: sai số cột")
            rows.append(row)
    _require(bool(rows), f"{path}: file rỗng")
    return rows


def _iso_date(value):
    _require(isinstance(value, str), "Ngày phải là chuỗi ISO YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise DataContractError(f"Ngày không hợp lệ: {value}") from exc
    _require(parsed.isoformat() == value, f"Ngày không đúng ISO: {value}")
    return value


def _identity(value):
    _require(isinstance(value, str) and bool(value) and value == value.strip(),
             f"Identity rỗng hoặc sai định dạng: {value!r}")
    return value


def _number(value, field, missing=True):
    if value is None or value == "":
        _require(missing, f"{field}: missing value")
        return None
    _require(not isinstance(value, bool), f"{field}: boolean không phải numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DataContractError(f"{field}: không phải numeric") from exc
    if math.isnan(number) and missing:
        return None
    _require(math.isfinite(number), f"{field}: giá trị không finite")
    return number


def _integer(value, field):
    number = _number(value, field, missing=False)
    _require(number.is_integer(), f"{field}: phải là integer")
    return int(number)


def load_m2_manifest(path=ROOT / SOURCES["manifest"]):
    return _read_json(path)


def load_market_labels(path=ROOT / SOURCES["labels"]):
    rows = _read_csv(path, ("snapshot_date", "security_id", "ticker",
                            "cluster_label", "membership_period"))
    for row in rows:
        _iso_date(row["snapshot_date"])
        _identity(row["security_id"])
        _identity(row["ticker"])
        row["cluster_label"] = _integer(row["cluster_label"], "cluster_label")
    _unique_index(rows, ("snapshot_date", "security_id"))
    _unique_index(rows, ("snapshot_date", "ticker"))
    return rows


def load_market_profiles(path=ROOT / SOURCES["profiles"]):
    rows = _read_csv(path, ("snapshot_date", "cluster_label", "size", "size_ratio",
                            "membership_period", *MARKET_FEATURES))
    for row in rows:
        if row["snapshot_date"] not in SUMMARY_DATES:
            _iso_date(row["snapshot_date"])
        row["cluster_label"] = _integer(row["cluster_label"], "cluster_label")
        row["size"] = _integer(row["size"], "size")
        row["size_ratio"] = _number(row["size_ratio"], "size_ratio", missing=False)
        for feature in MARKET_FEATURES:
            row[feature] = _number(row[feature], feature)
    _unique_index(rows, ("snapshot_date", "cluster_label"))
    return rows


def load_market_features(path, labels):
    """Audit every source key; retain only exact assignment matches in memory.

    Other feature rows are counted, never used to extend the M2 universe.
    No availability/financial logic or feature computation occurs here.
    """
    wanted = {(r["snapshot_date"], r["security_id"]) for r in labels}
    m2_dates = {r["snapshot_date"] for r in labels}
    seen, ticker_keys, rows, dates, schema = set(), {}, {}, Counter(), set()
    extra_in_m2 = 0
    required = {"as_of_date", "security_id", "ticker", *MARKET_FEATURES}
    with Path(path).open(encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            row = json.loads(line)
            _require(isinstance(row, dict) and required <= row.keys(),
                     f"{path}:{line_number}: thiếu feature schema")
            schema.update(row)
            day = _iso_date(row["as_of_date"])
            _require("2016-01-01" <= day <= "2025-12-31", "Feature source ngoài 2016–2025")
            sid, ticker = _identity(row["security_id"]), _identity(row["ticker"])
            key, ticker_key = (day, sid), (day, ticker)
            _require(key not in seen, f"Duplicate feature key: {key}")
            _require(ticker_key not in ticker_keys or ticker_keys[ticker_key] == sid,
                     f"Ticker ambiguity: {ticker_key}")
            seen.add(key)
            ticker_keys[ticker_key] = sid
            dates[day] += 1
            if key in wanted:
                rows[key] = {
                    "as_of_date": day, "security_id": sid, "ticker": ticker,
                    "source_line": line_number,
                    **{f: _number(row[f], f) for f in MARKET_FEATURES},
                }
            elif day in m2_dates:
                extra_in_m2 += 1
    _require(bool(dates), "Feature source rỗng")
    return {
        "rows": rows, "schema": sorted(schema), "row_count": sum(dates.values()),
        "snapshot_count": len(dates), "first_date": min(dates), "last_date": max(dates),
        "feature_only_rows": len(seen - wanted), "feature_only_m2_dates": extra_in_m2,
    }


def load_company_names(path):
    """Reference names only, joined by security_id; no historical identity claim."""
    names = {}
    with Path(path).open(encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            row = json.loads(line)
            _require(isinstance(row, dict) and {"security_id", "ticker", "company_name"} <= row.keys(),
                     f"{path}:{line_number}: thiếu company metadata")
            sid = _identity(row["security_id"])
            _require(sid not in names, f"Duplicate company security_id: {sid}")
            _identity(row["ticker"])
            name = row["company_name"]
            _require(name is None or isinstance(name, str), "company_name phải là text hoặc null")
            names[sid] = {"ticker": row["ticker"], "company_name": name or None}
    return names


# 3. VALIDATION
def _unique_index(rows, fields):
    index = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        _require(key not in index, f"Duplicate key {fields}: {key}")
        index[key] = row
    return index


def validate_market_contract(manifest, labels, profiles, features):
    methodology, coverage = manifest["methodology"], manifest["coverage"]
    _require(manifest["status"] == "OFFICIALLY_HANDED_OFF", "Handoff chưa official")
    _require(methodology["selected_algorithm"] == "KMeans_Baseline"
             and methodology["global_k"] == 2, "Sai frozen algorithm/global_k")
    _require(tuple(methodology["features"]) == MARKET_FEATURES, "Sai 8-feature contract")
    dates = coverage["rebalance_dates"]
    _require(isinstance(dates, list) and all(isinstance(d, str) for d in dates),
             "Snapshot universe phải là list ngày ISO")
    _require(len(dates) == len(set(dates)) == coverage["total_snapshots"] == 84
             and dates == sorted(dates), "Snapshot universe phải đúng 84 ngày unique")
    for day in dates:
        _iso_date(day)
        _require("2019-01-01" <= day <= "2025-12-31", "M2 snapshot ngoài 2019–2025")
    _require({r["snapshot_date"] for r in labels} == set(dates), "Labels khác manifest dates")
    _require(len(labels) == coverage["total_member_observations"], "Sai assignment count")
    _unique_index(labels, ("snapshot_date", "security_id"))
    _unique_index(labels, ("snapshot_date", "ticker"))
    _unique_index(profiles, ("snapshot_date", "cluster_label"))
    monthly = [r for r in profiles if r["snapshot_date"] not in SUMMARY_DATES]
    summaries = [r for r in profiles if r["snapshot_date"] in SUMMARY_DATES]
    counts = Counter((r["snapshot_date"], r["cluster_label"]) for r in labels)
    totals = Counter(r["snapshot_date"] for r in labels)
    expected = {(d, c) for d in dates for c in (0, 1)}
    _require(set(counts) == expected, "Labels thiếu/thừa cluster 0/1")
    _require({(r["snapshot_date"], r["cluster_label"]) for r in monthly} == expected,
             "Profiles thiếu/thừa snapshot hoặc cluster")
    for period, n in (("development", 60), ("holdout", 24)):
        period_dates = [d for d in dates if (d < "2024-01-01") == (period == "development")]
        _require(len(period_dates) == coverage[f"n_{period}_snapshots"] == n,
                 f"Sai {period} snapshot count")
        _require([min(period_dates), max(period_dates)] == coverage[f"{period}_window"],
                 f"Sai {period} window")
    gap = coverage.get("systemic_gap")
    if gap:
        _require(len(gap) == 2 and not any(gap[0] <= d <= gap[1] for d in dates),
                 "Snapshot nằm trong systemic gap")
    for row in labels + monthly:
        expected_period = "development" if row["snapshot_date"] < "2024-01-01" else "holdout"
        _require(row["membership_period"] == expected_period, "Sai membership_period")
    for row in summaries:
        _require(row["membership_period"] == SUMMARY_DATES[row["snapshot_date"]],
                 "Sai summary membership_period")
    for row in monthly:
        count = counts[(row["snapshot_date"], row["cluster_label"])]
        _require(row["size"] == count and math.isclose(
            row["size_ratio"], count / totals[row["snapshot_date"]], abs_tol=1e-12,
            rel_tol=1e-12), "Profile size/size_ratio khác member list")
    matched = features["rows"]
    missing = [(r["snapshot_date"], r["security_id"]) for r in labels
               if (r["snapshot_date"], r["security_id"]) not in matched]
    missing_values = 0
    for row in labels:
        feature = matched.get((row["snapshot_date"], row["security_id"]))
        if feature is not None:
            _require(feature["ticker"] == row["ticker"], "Ticker mismatch tại join key")
            missing_values += any(feature[f] is None for f in MARKET_FEATURES)
    missing_profiles = sum(any(row[f] is None for f in MARKET_FEATURES) for row in monthly)
    return {
        "status": "PARTIAL" if missing or missing_values or missing_profiles else "PASS",
        "join_key": "labels(snapshot_date, security_id) ↔ features(as_of_date, security_id), one-to-one",
        "label_rows": len(labels), "monthly_profiles": len(monthly),
        "summary_profiles": len(summaries), "m2_snapshots": len(dates),
        "feature_rows": features["row_count"], "feature_snapshots": features["snapshot_count"],
        "feature_only_rows": features["feature_only_rows"],
        "feature_only_m2_dates": features["feature_only_m2_dates"],
        "missing_feature_rows": len(missing), "rows_with_missing_feature_values": missing_values,
        "profiles_with_missing_values": missing_profiles,
    }


def load_market_data(root=ROOT):
    root = Path(root)
    before = source_fingerprints(root)
    manifest = load_m2_manifest(root / SOURCES["manifest"])
    for name in ("labels", "profiles"):
        path = root / SOURCES[name]
        _require(_sha256(path) == manifest["artifacts_sha256"][path.name],
                 f"Checksum mismatch: {path.name}")
    fm = _read_json(root / SOURCES["feature_manifest"])
    dm = _read_json(root / SOURCES["development_manifest"])
    hm = _read_json(root / SOURCES["holdout_manifest"])
    feature_hash = _sha256(root / SOURCES["features"])
    _require(feature_hash == fm["outputs"]["canonical/feature_snapshots.jsonl"]
             == dm["lineage"]["c8_feature_sha256"] == hm["c8_feature_sha256"],
             "Feature hash khác C8/development/holdout lineage")
    _require(_sha256(root / SOURCES["feature_manifest"]) == dm["source_manifest_hash"]
             == hm["c8_manifest_sha256"], "C8 manifest khác development/holdout lineage")
    _require(dm["status"] == "PASS" and hm["status"] == "complete", "M2 source chưa complete")
    _require(_sha256(root / SOURCES["securities"]) == fm["outputs"]["canonical/securities.jsonl"],
             "Checksum mismatch: securities.jsonl")
    company_names = load_company_names(root / SOURCES["securities"])
    labels = load_market_labels(root / SOURCES["labels"])
    for label in labels:
        company = company_names.get(label["security_id"])
        _require(company is None or company["ticker"] == label["ticker"], "Company ticker mismatch")
    profiles = load_market_profiles(root / SOURCES["profiles"])
    features = load_market_features(root / SOURCES["features"], labels)
    audit = validate_market_contract(manifest, labels, profiles, features)
    _require(before == source_fingerprints(root), "Source thay đổi trong lúc đọc; hãy tải lại")
    return {
        "manifest": manifest, "labels": labels, "profiles": profiles,
        "feature_rows": features["rows"], "audit": audit,
        "labels_by_ticker_date": _unique_index(labels, ("snapshot_date", "ticker")),
        "feature_hash": feature_hash, "feature_schema": features["schema"],
        "company_names": company_names,
        "feature_window": (features["first_date"], features["last_date"]),
        "root": str(root.resolve()),
    }


# 4. QUERY LOGIC (exact dates only; returns explicit, non-throwing query states)
def list_decision_dates(data):
    return list(data["manifest"]["coverage"]["rebalance_dates"])


def list_tickers(data):
    return sorted({row["ticker"] for row in data["labels"]})


def get_market_overview(data, decision_date):
    if not isinstance(decision_date, str) or decision_date not in list_decision_dates(data):
        return {"status": "SNAPSHOT_NOT_FOUND"}
    profiles = sorted((dict(r) for r in data["profiles"] if r["snapshot_date"] == decision_date),
                      key=lambda r: r["cluster_label"])
    members = {c: sorted((dict(r) for r in data["labels"] if r["snapshot_date"] == decision_date
                           and r["cluster_label"] == c), key=lambda r: r["ticker"])
               for c in (0, 1)}
    if not profiles or not any(members.values()):
        return {"status": "MARKET_CLUSTER_NOT_FOUND"}
    return {"status": "OK", "snapshot_date": decision_date, "profiles": profiles,
            "members": members, "membership_period": profiles[0]["membership_period"]}


def get_market_company(data, ticker, decision_date):
    if not isinstance(decision_date, str) or decision_date not in list_decision_dates(data):
        return {"status": "SNAPSHOT_NOT_FOUND"}
    if not isinstance(ticker, str) or ticker not in list_tickers(data):
        return {"status": "TICKER_NOT_FOUND"}
    label = data["labels_by_ticker_date"].get((decision_date, ticker))
    if label is None:
        return {"status": "MARKET_CLUSTER_NOT_FOUND"}
    feature = data["feature_rows"].get((decision_date, label["security_id"]))
    if feature is None:
        return {"status": "MARKET_FEATURES_NOT_FOUND", "cluster": dict(label), "features": None}
    values = {f: feature[f] for f in MARKET_FEATURES}
    return {
        "status": "MARKET_FEATURE_VALUES_MISSING" if any(v is None for v in values.values()) else "OK",
        "cluster": dict(label), "features": values, "feature_source_line": feature["source_line"],
    }


def cluster_display_names(profiles):
    """Snapshot-local descriptive aliases; never relabel the scientific artifact."""
    ordered = sorted(profiles, key=lambda r: r["cluster_label"])
    neutral = {r["cluster_label"]: f"Nhóm {chr(65 + i)}" for i, r in enumerate(ordered)}
    values = [r["liquidity_21"] for r in ordered]
    if len(ordered) != 2 or any(v is None for v in values) or values[0] == values[1]:
        return neutral
    leader = max(ordered, key=lambda r: r["liquidity_21"])
    other = next(r for r in ordered if r is not leader)
    # "Đại trà" is used only when that lower-liquidity group is also larger.
    return {leader["cluster_label"]: "Dẫn đầu thanh khoản",
            other["cluster_label"]: "Đại trà" if other["size"] > leader["size"]
            else "Thanh khoản thấp hơn"}


def get_market_scatter(data, decision_date):
    overview = get_market_overview(data, decision_date)
    if overview["status"] != "OK":
        return {"status": overview["status"], "rows": [], "missing_count": 0}
    names, rows, missing = cluster_display_names(overview["profiles"]), [], 0
    for label, members in overview["members"].items():
        for member in members:
            features = data["feature_rows"].get((decision_date, member["security_id"]))
            if features is None or any(features[f] is None for f in (SCATTER_X, SCATTER_Y)):
                missing += 1
                continue
            rows.append({"ticker": member["ticker"], "security_id": member["security_id"],
                         "group": names[label], **{f: features[f] for f in MARKET_FEATURES}})
    return {"status": "PARTIAL" if missing else "OK", "rows": rows, "missing_count": missing}


def get_market_members(data, decision_date, cluster_label, search="", page=1, page_size=10):
    overview = get_market_overview(data, decision_date)
    if overview["status"] != "OK":
        return {"status": overview["status"], "rows": []}
    if not isinstance(cluster_label, int) or isinstance(cluster_label, bool) or cluster_label not in overview["members"]:
        return {"status": "MARKET_CLUSTER_NOT_FOUND", "rows": []}
    if (not isinstance(search, str) or not isinstance(page, int) or isinstance(page, bool)
            or page < 1 or not isinstance(page_size, int) or page_size not in (10, 25, 50, 100)):
        return {"status": "INVALID_QUERY_STATE", "rows": []}
    matched = []
    for member in overview["members"][cluster_label]:
        company = data["company_names"].get(member["security_id"], {})
        name = company.get("company_name")
        if search.strip().casefold() not in f"{member['ticker']} {name or ''}".casefold():
            continue
        features = data["feature_rows"].get((decision_date, member["security_id"]))
        matched.append({"ticker": member["ticker"], "security_id": member["security_id"],
                        "company_name": name,
                        "feature_status": "MARKET_FEATURES_NOT_FOUND" if features is None else (
                            "MARKET_FEATURE_VALUES_MISSING" if any(features[f] is None for f in MARKET_FEATURES) else "OK"),
                        **{f: features[f] if features is not None else None for f in MARKET_FEATURES}})
    total = len(matched)
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    start = (page - 1) * page_size
    return {"status": "OK", "rows": matched[start:start + page_size], "page": page,
            "page_size": page_size, "total": total, "total_pages": pages, "start": start}


# 5. STREAMLIT UI — native controls, local CSS, no separate frontend
PALETTE = ("#237cff", "#49bd82")
DASHBOARD_CSS = """
<style>
.stApp {background:linear-gradient(120deg,#f2f8fe 0%,#fbfdff 48%,#f5f9fe 100%);color:#12203b;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stMainBlockContainer"] {max-width:1660px;padding:1.8rem 1.7rem 2rem;}
.delta-header {display:flex;justify-content:space-between;gap:24px;align-items:center;margin:0 0 22px;}
.delta-header h1 {font-size:28px!important;letter-spacing:-.8px;margin:0;padding:0;color:#101e39;}
.delta-subtitle {color:#70809a;font-size:13px;margin-top:7px;}
.delta-badge {background:#eaf3ff;border:1px solid #dceaff;border-radius:9px;padding:11px 16px;
 color:#2a5f9f;font-size:12px;line-height:1.7;white-space:nowrap;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#e0e9f4!important;border-radius:12px!important;}
.st-key-filter_panel,.st-key-scatter_panel,.st-key-profile_panel,.st-key-members_panel {
 background:rgba(255,255,255,.78);border-radius:12px;}
.st-key-filter_panel {min-height:885px;background:linear-gradient(160deg,#f8fbff,#f0f6fc);}
.st-key-filter_panel [data-testid="stCaptionContainer"] {font-size:12px;line-height:1.6;}
.st-key-filter_panel [data-testid="stSelectbox"] {margin-bottom:12px;}
[data-testid="stSelectbox"] [data-baseweb="select"]>div,
[data-testid="stTextInput"] input {border-radius:7px;border-color:#dce6f2;background:#fff;}
.st-key-member_search .react-aria-TextField {
 border:1px solid #aebfd5!important;border-radius:8px;background:#fff;
 box-shadow:0 1px 2px rgba(25,52,89,.04);}
.st-key-member_search .react-aria-TextField:focus-within {
 border-color:#237cff!important;box-shadow:0 0 0 3px rgba(35,124,255,.12);}
.st-key-member_search input {border:0!important;outline:none;}
h3 {font-size:16px!important;letter-spacing:-.2px;padding:0!important;margin:0 0 6px!important;}
[data-testid="stDataFrame"] {border-radius:8px;overflow:hidden;}
[data-testid="stMetricLabel"] {font-size:12px;color:#6b7890;}
[data-testid="stMetricValue"] {font-size:25px;font-weight:700;color:#152344;}
.st-key-kpi_total,.st-key-kpi_count,.st-key-kpi_largest,.st-key-kpi_smallest {border-radius:10px;padding:12px 16px;min-height:110px;}
.st-key-kpi_total {background:#eaf4ff;} .st-key-kpi_count {background:#eafaef;}
.st-key-kpi_largest {background:#f1edff;} .st-key-kpi_smallest {background:#fff3e5;}
[data-testid="stButton"] button {border-radius:7px;box-shadow:none;font-size:13px;}
[data-testid="stButton"] button[kind="primary"] {background:#237cff;border-color:#237cff;}
[data-testid="stSegmentedControl"] {border-radius:7px;}
.delta-footnote {font-size:11px;color:#8b97aa;margin-top:14px;}
@media(max-width:850px){.delta-header{display:block}.delta-badge{margin-top:12px;white-space:normal}
.st-key-filter_panel{min-height:0}[data-testid="stMainBlockContainer"]{padding:1rem}}
</style>
"""


def _format_count(value):
    return f"{value:,}".replace(",", ".")


def _table(st, rows, group_colors=None, height=None):
    import pandas as pd

    frame = pd.DataFrame(rows)
    formats = {f: "{:,.4f}" for f in MARKET_FEATURES if f in frame.columns}
    if "liquidity_21" in formats:
        formats["liquidity_21"] = "{:,.0f}"
    if "Tỷ trọng" in frame.columns:
        formats["Tỷ trọng"] = "{:.2%}"
    styled = frame.style.format(formats, na_rep="MISSING").set_properties(
        **{"font-size": "12px", "color": "#253957"})
    if group_colors and "Nhóm" in frame.columns:
        styled = styled.map(lambda name: f"color:{group_colors[name]};font-weight:600;"
                            "background-color:#f1f7ff", subset=["Nhóm"])
    config = {f: st.column_config.NumberColumn(f, width="small")
              for f in MARKET_FEATURES if f in frame.columns}
    for field in ("Số mã", "Tỷ trọng", "STT"):
        if field in frame.columns:
            config[field] = st.column_config.NumberColumn(field, width="small")
    if "Nhóm" in frame.columns:
        config["Nhóm"] = st.column_config.TextColumn("Nhóm", width="medium")
    if "Mã" in frame.columns:
        config["Mã"] = st.column_config.TextColumn("Mã", width="small")
    if "Tên công ty" in frame.columns:
        config["Tên công ty"] = st.column_config.TextColumn(
            "Tên công ty", width="medium", help="Tên tham chiếu từ metadata C8; không phải tên lịch sử point-in-time.")
    if "liquidity_21" in frame.columns:
        config["liquidity_21"] = st.column_config.NumberColumn(
            "liquidity_21", width="medium", help="Giá trị gốc từ artifact, đơn vị VND; không chuẩn hóa theo ảnh mẫu.")
    st.dataframe(styled, hide_index=True, width="stretch", height=height or "auto", column_config=config)


def _set_member_page(st, page=1):
    st.session_state["member_page"] = page


def render_overview(st, data, decision_date):
    result = get_market_overview(data, decision_date)
    if result["status"] != "OK":
        st.warning(result["status"])
        return
    profiles = result["profiles"]
    names = cluster_display_names(profiles)
    colors = {names[r["cluster_label"]]: PALETTE[i % len(PALETTE)] for i, r in enumerate(profiles)}
    largest, smallest = max(profiles, key=lambda r: r["size"]), min(profiles, key=lambda r: r["size"])
    metrics = st.columns(4, gap="small")
    for col, key, title, value, caption in (
        (metrics[0], "total", "Tổng số mã", _format_count(sum(r["size"] for r in profiles)), decision_date),
        (metrics[1], "count", "Số nhóm", str(len(profiles)), "KMeans Baseline"),
        (metrics[2], "largest", "Nhóm lớn nhất", f"{_format_count(largest['size'])} mã", names[largest["cluster_label"]]),
        (metrics[3], "smallest", "Nhóm nhỏ nhất", f"{_format_count(smallest['size'])} mã", names[smallest["cluster_label"]]),
    ):
        with col:
            with st.container(key=f"kpi_{key}"):
                st.metric(title, value)
                st.caption(caption)
    with st.container(border=True, key="scatter_panel"):
        st.subheader("Biểu đồ phân cụm các mã", help="Mỗi điểm là một ticker với features gốc của snapshot đang chọn; màu theo assignment M2.")
        scatter = get_market_scatter(data, decision_date)
        if scatter["missing_count"]:
            st.warning(f"MARKET_FEATURES_NOT_FOUND — {_format_count(scatter['missing_count'])} mã thiếu tọa độ; không được vẽ thay bằng zero.")
        if scatter["rows"]:
            st.vega_lite_chart(scatter["rows"], {
                "mark": {"type": "circle", "size": 46, "opacity": .72, "stroke": "white", "strokeWidth": .4},
                "encoding": {
                    "x": {"field": SCATTER_X, "type": "quantitative",
                          "title": "Thanh khoản bình quân 21 phiên (tỷ VND/phiên · symlog)",
                          "scale": {"type": "symlog", "constant": LIQUIDITY_SYMLOG_CONSTANT, "zero": True},
                          "axis": {"values": [0, 1e9, 1e10, 1e11, 1e12, 1e13],
                                   "labelExpr": "format(datum.value / 1e9, ',.0f')"}},
                    "y": {"field": SCATTER_Y, "type": "quantitative",
                          "title": "Beta 126 phiên (độ nhạy với thị trường)",
                          "scale": {"type": "linear", "zero": False}},
                    "color": {"field": "group", "type": "nominal", "title": None,
                              "scale": {"domain": list(colors), "range": list(colors.values())},
                              "legend": {"orient": "right", "labelLimit": 220, "symbolSize": 100}},
                    "tooltip": [{"field": "ticker", "type": "nominal", "title": "Mã"},
                                {"field": "group", "type": "nominal", "title": "Nhóm"},
                                *[{"field": f, "type": "quantitative", "format": ",.4f"} for f in MARKET_FEATURES]],
                },
                "config": {"view": {"stroke": None}, "background": "transparent",
                           "axis": {"gridColor": "#e8eff8", "domainColor": "#bdcce0", "labelColor": "#526583",
                                    "titleColor": "#526583", "titleFontWeight": "normal", "titlePadding": 12}},
            }, width="stretch", height=280, theme=None, key="market_scatter")
        st.caption("X: liquidity_21 · Y: beta_126 — cố định cho mọi snapshot. "
                   "X dùng symlog, giữ giá trị 0; nhãn trục quy đổi tỷ VND, tooltip giữ VND gốc.")
    with st.container(border=True, key="profile_panel"):
        st.subheader("Đặc điểm trung bình theo nhóm (Cluster Profile)",
                     help="Profile cấp cluster từ M2, độc lập với features của từng ticker.")
        _table(st, [{"Nhóm": names[r["cluster_label"]], "Số mã": r["size"], "Tỷ trọng": r["size_ratio"],
                     **{f: r[f] for f in MARKET_FEATURES}} for r in profiles], colors, height=112)
    with st.container(border=True, key="members_panel"):
        st.subheader("Danh sách mã trong từng nhóm")
        label = st.segmented_control("Nhóm cổ phiếu", list(names), default=profiles[0]["cluster_label"],
                                     required=True, format_func=names.get, key="member_cluster",
                                     label_visibility="collapsed", on_change=_set_member_page, args=(st,))
        controls = st.columns([1.2, 1.5, 3], gap="small")
        with controls[0]:
            page_size = st.selectbox("Hiển thị", (10, 25, 50, 100), key="member_page_size",
                                     on_change=_set_member_page, args=(st,))
        with controls[2]:
            search = st.text_input("Tìm mã hoặc tên công ty", placeholder="Tìm mã (ticker)...",
                                   key="member_search", on_change=_set_member_page, args=(st,))
        members = get_market_members(data, decision_date, label, search,
                                     st.session_state.get("member_page", 1), page_size)
        if members["status"] != "OK":
            st.warning(members["status"])
            return
        st.session_state["member_page"] = members["page"]
        if members["rows"]:
            for status in ("MARKET_FEATURES_NOT_FOUND", "MARKET_FEATURE_VALUES_MISSING"):
                missing = sum(row["feature_status"] == status for row in members["rows"])
                if missing:
                    st.warning(f"{status} — {missing} mã trên trang thiếu dữ liệu; hiển thị MISSING.")
            _table(st, [{"STT": members["start"] + i + 1, "Mã": r["ticker"], "Tên công ty": r["company_name"],
                         **{f: r[f] for f in MARKET_FEATURES}} for i, r in enumerate(members["rows"])],
                   height=min(440, 37 + len(members["rows"]) * 35))
        else:
            st.info("Không tìm thấy mã phù hợp trong nhóm đã chọn.")
        pagination = st.columns([4, .55, .55, .55, .55, .55, .55, .55], gap="small")
        with pagination[0]:
            first = members["start"] + 1 if members["total"] else 0
            st.caption(f"{first}–{min(members['start'] + page_size, members['total'])} / "
                       f"{_format_count(members['total'])} mã · Trang {members['page']}/{members['total_pages']}")
        with pagination[1]:
            st.button("‹", key="page_prev", disabled=members["page"] == 1,
                      on_click=_set_member_page, args=(st, members["page"] - 1), width="stretch")
        start_page = min(max(1, members["page"] - 2), max(1, members["total_pages"] - 4))
        for col, number in zip(pagination[2:7], range(start_page, min(start_page + 5, members["total_pages"] + 1))):
            with col:
                st.button(str(number), key=f"page_{number}", type="primary" if number == members["page"] else "secondary",
                          on_click=_set_member_page, args=(st, number), width="stretch")
        with pagination[7]:
            st.button("›", key="page_next", disabled=members["page"] == members["total_pages"],
                      on_click=_set_member_page, args=(st, members["page"] + 1), width="stretch")


# 6. MAIN
def main(root=ROOT):
    import streamlit as st

    st.set_page_config(page_title="DELTA · M3-B Market", layout="wide")
    st.html(DASHBOARD_CSS)
    for obsolete_key in ("view", "ticker"):
        st.session_state.pop(obsolete_key, None)

    @st.cache_data(show_spinner=False, max_entries=1)
    def cached_load(root_string, fingerprints):
        return load_market_data(Path(root_string))

    if st.session_state.pop("reload_data", False):
        cached_load.clear()
        for key in ("decision_date", "ticker", "member_page", "member_search", "member_cluster"):
            st.session_state.pop(key, None)
    try:
        fingerprints = source_fingerprints(root)
        with st.spinner("Đang xác minh checksum và data contract…"):
            data = cached_load(str(Path(root).resolve()), fingerprints)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        st.error(f"DATA_CONTRACT_BLOCKED — {exc}")
        st.button("Đọc lại dữ liệu", on_click=lambda: st.session_state.update(reload_data=True))
        return
    if data["audit"]["status"] != "PASS":
        st.warning(f"PARTIAL — {data['audit']['missing_feature_rows']} assignments thiếu feature row; "
                   f"{data['audit']['rows_with_missing_feature_values']} rows thiếu feature values; "
                   f"{data['audit']['profiles_with_missing_values']} profiles thiếu giá trị.")
    dates = list_decision_dates(data)
    window = data["feature_window"]
    st.html(f'<div class="delta-header"><div><h1>Market Clustering Dashboard</h1>'
            f'<div class="delta-subtitle">Phân cụm động lượng thị trường · Market-only · Dữ liệu '
            f'{escape(window[0][:4])}–{escape(window[1][:4])}</div></div>'
            f'<div class="delta-badge">Nguồn: Official M2 handoff + C8 Market Features<br>'
            f'Snapshot mới nhất: <strong>{escape(dates[-1])}</strong></div></div>')
    if "decision_date" in st.session_state and st.session_state["decision_date"] not in dates:
        st.error("SNAPSHOT_NOT_FOUND — dùng nút Đọc lại dữ liệu để đặt lại lựa chọn.")
        st.button("Đọc lại dữ liệu", on_click=lambda: st.session_state.update(reload_data=True))
        return
    filters, content = st.columns([1, 4.8], gap="medium")
    with filters:
        with st.container(border=True, key="filter_panel"):
            decision_date = st.selectbox("Chọn ngày phân cụm", dates, index=len(dates) - 1, key="decision_date",
                                         on_change=_set_member_page, args=(st,))
            st.divider()
            st.caption(f"{len(dates)} snapshot đã xác minh\n\n{dates[0]} → {dates[-1]}")
            st.caption("Development" if decision_date < "2024-01-01" else "Holdout")
            st.button("Đọc lại dữ liệu", key="reload", width="stretch",
                      on_click=lambda: st.session_state.update(reload_data=True))
    with content:
        render_overview(st, data, decision_date)
    with st.expander("Data source / snapshot / version"):
        st.write({"handoff_version": data["manifest"]["manifest_version"],
                  "handoff_timestamp": data["manifest"]["timestamp"],
                  "snapshot_date": decision_date, "algorithm": "KMeans_Baseline", "global_k": 2})
        for name, path in SOURCES.items():
            st.caption(f"{name}: {path}")
        st.caption(f"{data['audit']['summary_profiles']} summary profiles MEDIAN_* được giữ trong "
                   "nguồn; không phải snapshot và không xuất hiện trong selector.")
        st.json(data["audit"])
        names = cluster_display_names(get_market_overview(data, decision_date)["profiles"])
        st.write({"display_names_by_source_label": names})
        st.caption("Tên mô tả theo snapshot: Dẫn đầu thanh khoản = liquidity_21 profile cao hơn; "
                   "Đại trà = nhóm còn lại có nhiều thành viên hơn. Nếu thiếu/tie profile, dùng tên trung tính. "
                   "Không sửa assignment, không xếp hạng cổ phiếu. Tên công ty là metadata tham chiếu C8.")
    st.html('<div class="delta-footnote">DELTA · Nghiên cứu clustering · Không phải khuyến nghị đầu tư</div>')


if __name__ == "__main__":
    main()
