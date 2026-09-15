"""Build dashboard-facing company snapshots without recomputing research logic."""

from collections import defaultdict
from pathlib import Path

from ..io import digest, encoded, now, read_json, read_rows, write_json


PUBLIC_FEATURES = (
    "mom_21",
    "mom_63",
    "mom_126",
    "mom_252",
    "vol_63",
    "vol_126",
    "downside_vol_63",
    "beta_126",
    "mdd_126",
)


def _require_file(directory, relative):
    path = Path(directory) / relative
    if not path.is_file():
        raise ValueError(f"missing product input: {path}")
    return path


def _latest(rows, field):
    return max(rows, key=lambda row: row[field]) if rows else None


def _state(available, reason=None):
    result = {"status": "available" if available else "unavailable"}
    if reason:
        result["reason"] = reason
    return result


def build_company_detail(security, prices, features, assignments, profiles, securities):
    """Project one security into the stable product API shape.

    Inputs are already-canonical rows. Missing product domains remain explicitly
    unavailable; the projection never fabricates fundamentals, news or OHLC.
    """
    security_id = security["security_id"]
    ticker = security["ticker"].upper()
    prices = sorted((row for row in prices if row["security_id"] == security_id), key=lambda row: row["trade_date"])
    features = sorted((row for row in features if row["security_id"] == security_id), key=lambda row: row["as_of_date"])
    all_assignments = list(assignments)
    security_assignments = sorted(
        (row for row in all_assignments if row["security_id"] == security_id),
        key=lambda row: row["snapshot_date"],
    )

    quote = None
    if prices:
        current = prices[-1]
        previous = prices[-2] if len(prices) > 1 else None
        price = current.get("raw_close") or current.get("adj_close")
        previous_price = (previous.get("raw_close") or previous.get("adj_close")) if previous else None
        change = price - previous_price if price is not None and previous_price is not None else None
        quote = {
            "as_of_date": current["trade_date"],
            "price": price,
            "previous_close": previous_price,
            "change": change,
            "change_pct": change / previous_price if change is not None and previous_price else None,
            "open": current.get("raw_open"),
            "high": current.get("raw_high"),
            "low": current.get("raw_low"),
            "reference": current.get("reference_price"),
            "ceiling": current.get("ceiling_price"),
            "floor": current.get("floor_price"),
            "currency": security.get("currency"),
            "price_unit": security.get("price_unit"),
            "price_basis": current.get("adjustment_basis"),
            "source": current.get("source"),
        }
    missing_quote_fields = [
        field for field in ("open", "high", "low", "reference", "ceiling", "floor")
        if quote is not None and quote.get(field) is None
    ]
    quote_state = _state(quote is not None, "Không có quan sát giá canonical." if quote is None else None)
    if quote is not None and missing_quote_fields:
        quote_state = {
            "status": "partial",
            "reason": "Một số trường quote chưa có semantics/source được duyệt.",
            "missing_fields": missing_quote_fields,
        }

    latest_feature = _latest(features, "as_of_date")
    public_features = {
        name: latest_feature.get(name)
        for name in PUBLIC_FEATURES
        if latest_feature and name in latest_feature
    }

    profile_by_key = {
        (row["snapshot_date"], row["aligned_cluster_id"]): row
        for row in profiles
    }
    ticker_by_security = {row["security_id"]: row["ticker"] for row in securities}
    latest_assignment = _latest(security_assignments, "snapshot_date")
    cluster = None
    if latest_assignment:
        cluster_id = latest_assignment["aligned_cluster_id"]
        snapshot_date = latest_assignment["snapshot_date"]
        profile = profile_by_key.get((snapshot_date, cluster_id), {})
        peers = sorted({
            ticker_by_security.get(row["security_id"], row["security_id"])
            for row in all_assignments
            if row["snapshot_date"] == snapshot_date
            and row["aligned_cluster_id"] == cluster_id
            and row["security_id"] != security_id
        })
        cluster = {
            "as_of_date": snapshot_date,
            "cluster_id": cluster_id,
            "label": profile.get("semantic_label"),
            "centroid": profile.get("centroid"),
            "size": profile.get("size"),
            "peers": peers,
            "history": [
                {"date": row["snapshot_date"], "cluster_id": row["aligned_cluster_id"]}
                for row in security_assignments
            ],
        }

    warnings = []
    if quote and quote["price_basis"] == "vendor_adjusted":
        warnings.append("Giá là chuỗi điều chỉnh kỹ thuật của vendor, không phải raw executable price hoặc total return đã xác minh.")
    if security.get("identity_status") == "provisional_verified_for_pilot":
        warnings.append("Định danh chỉ được xác minh trong phạm vi pilot; chưa phải historical security master hoàn chỉnh.")
    if len(securities) < 20:
        warnings.append("Peer/cluster hiện lấy từ pilot nhỏ, chỉ dùng kiểm thử sản phẩm và không phải kết luận đầu tư.")

    return {
        "schema_version": "1.0.0",
        "company": {
            "security_id": security_id,
            "ticker": ticker,
            "name": security.get("company_name"),
            "exchange": security.get("exchange"),
            "sector": security.get("sector"),
            "industry": security.get("industry"),
            "description": None,
        },
        "quote": quote,
        "quote_state": quote_state,
        "market_history": [
            {
                "date": row["trade_date"],
                "price": row.get("raw_close") or row.get("adj_close"),
                "volume": row.get("volume"),
                "price_basis": row.get("adjustment_basis"),
            }
            for row in prices
        ],
        "analytics": {
            "state": _state(latest_feature is not None, "Chưa có feature snapshot." if latest_feature is None else None),
            "as_of_date": latest_feature.get("as_of_date") if latest_feature else None,
            "values": public_features,
        },
        "cluster": cluster,
        "cluster_state": _state(cluster is not None, "Chưa có assignment bất biến." if cluster is None else None),
        "fundamentals": {"state": _state(False, "Financial PIT pipeline mới có schema, chưa có source mapping được duyệt."), "periods": []},
        "sentiment": {"state": _state(False, "Chưa có licensed news feed và Vietnamese sentiment model được đánh giá."), "series": []},
        "news": {"state": _state(False, "Chưa có news-source contract và quyền sử dụng nội dung."), "items": []},
        "quality": {"warnings": warnings},
        "provenance": {
            "data_version": latest_feature.get("data_version") if latest_feature else (prices[-1].get("data_version") if prices else None),
            "canonical_run_id": latest_feature.get("canonical_run_id") if latest_feature else None,
            "experiment_run_id": latest_assignment.get("run_id") if latest_assignment else None,
        },
    }


def export_product_bundle(canonical_dir, feature_run_dir, experiment_dir, output_dir, generated_at=None):
    """Export one immutable, API-ready bundle and return its manifest."""
    canonical_dir, feature_run_dir = Path(canonical_dir), Path(feature_run_dir)
    experiment_dir, output_dir = Path(experiment_dir), Path(output_dir)
    securities = read_rows(_require_file(canonical_dir, "clean/securities.jsonl"))
    prices = read_rows(_require_file(canonical_dir, "clean/prices_daily.jsonl"))
    features = read_rows(_require_file(feature_run_dir, "features/monthly.jsonl"))
    assignments = read_rows(_require_file(experiment_dir, "assignments.jsonl"))
    profiles = read_rows(_require_file(experiment_dir, "profiles.jsonl"))
    experiment_manifest = read_json(_require_file(experiment_dir, "manifest.json"))

    if experiment_manifest.get("status") != "complete":
        raise ValueError("product export requires a complete immutable experiment")
    if not securities:
        raise ValueError("product export requires at least one security")

    current_by_ticker = {}
    for row in securities:
        ticker = row["ticker"].upper()
        previous = current_by_ticker.get(ticker)
        if previous is None or (row.get("valid_from") or "") > (previous.get("valid_from") or ""):
            current_by_ticker[ticker] = row

    output_dir.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    companies = []
    for ticker, security in sorted(current_by_ticker.items()):
        detail = build_company_detail(security, prices, features, assignments, profiles, securities)
        relative = f"companies/{ticker}.json"
        write_json(output_dir / relative, detail)
        artifacts[relative] = digest(encoded(detail) + b"\n")
        companies.append({
            "ticker": ticker,
            "name": security.get("company_name"),
            "exchange": security.get("exchange"),
            "detail_url": f"/api/v1/companies/{ticker}",
        })

    catalog = {"schema_version": "1.0.0", "companies": companies}
    write_json(output_dir / "companies.json", catalog)
    artifacts["companies.json"] = digest(encoded(catalog) + b"\n")
    manifest = {
        "schema_version": "1.0.0",
        "status": "complete",
        "generated_at": generated_at or now(),
        "source": {
            "canonical_run_id": canonical_dir.name,
            "feature_run_id": feature_run_dir.name,
            "experiment_run_id": experiment_dir.name,
        },
        "company_count": len(companies),
        "artifacts": artifacts,
        "limitations": [
            "Legacy real pilot is exposed only as a product integration fixture.",
            "Missing fundamentals, sentiment and news are explicit unavailable states.",
        ],
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest
