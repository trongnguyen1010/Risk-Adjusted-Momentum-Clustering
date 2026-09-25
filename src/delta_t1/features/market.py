"""Calendar-aligned market features; missing sessions remain None."""
import math
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from statistics import covariance, mean, stdev, variance

from .registry import validate_required_features


STRICT_HISTORICAL_IDENTITY_STATUSES = {"verified", "synthetic"}
LEGACY_SCOPED_IDENTITY_STATUSES = {
    "verified", "synthetic", "provisional_verified_for_pilot",
}


def subtract_years(value: date, years: int) -> date:
    """Calendar-year cutoff; map Feb 29 to Feb 28 in a non-leap target year."""
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def at_least_calendar_years(start: str, end: str, years: int) -> bool:
    """Return calendar-span evidence only; this does not claim usable density."""
    start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    try:
        anniversary = start_date.replace(year=start_date.year + years)
    except ValueError:
        anniversary = start_date.replace(year=start_date.year + years, day=28)
    return anniversary <= end_date


def latest_completed_month_cutoff(collection_end: str) -> str:
    """Return the last calendar date allowed for a completed monthly snapshot.

    A collection ending before the final calendar day of its month is partial,
    so the current month is excluded without consulting a future exchange
    calendar.  If collection closes on calendar month-end, that month may be
    selected and its final observed session remains the snapshot date.
    """
    end = date.fromisoformat(collection_end)
    if end.day == monthrange(end.year, end.month)[1]:
        return end.isoformat()
    first = end.replace(day=1)
    return date.fromordinal(first.toordinal() - 1).isoformat()


def latest_completed_snapshot_rows(rows, collection_end: str):
    """Select one common latest snapshot from the last completed month."""
    cutoff = latest_completed_month_cutoff(collection_end)
    dates = sorted({row["as_of_date"] for row in rows if row["as_of_date"] <= cutoff})
    if not dates:
        raise ValueError("no feature snapshot exists in a completed collection month")
    snapshot_date = dates[-1]
    selected = [row for row in rows if row["as_of_date"] == snapshot_date]
    if len(selected) != len({row["security_id"] for row in selected}):
        raise ValueError("completed feature snapshot has duplicate security rows")
    return snapshot_date, {row["security_id"]: row for row in selected}


def momentum(prices, window):
    values = prices[-window - 1:]
    return values[-1] / values[0] - 1 if len(values) == window + 1 and all(
        value is not None and value > 0 for value in values
    ) else None


def returns(prices):
    return [b / a - 1 if a is not None and b is not None and a > 0 else None
            for a, b in zip(prices, prices[1:])]


def drawdown(prices, window):
    values = prices[-window:]
    if len(values) < window or any(value is None for value in values):
        return None
    peak, worst = values[0], 0.0
    for value in values:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    return worst


def full_window(values, size):
    tail = values[-size:]
    return tail if len(tail) == size and all(value is not None for value in tail) else None


def build_features(tables, config, data_version):
    """Build monthly market snapshots using explicitly closed month-end sessions."""
    required_features = validate_required_features(config["required_features"])
    metadata = tables["securities"]
    prices = {(row["security_id"], row["trade_date"]): row for row in tables["prices_daily"]}
    benchmark = {row["trade_date"]: row for row in tables.get("benchmark_daily", [])
                 if row["index_id"] == config.get("benchmark_id", "VNINDEX")}
    calendars = defaultdict(list)
    for row in tables["trading_calendar"]:
        if row["is_open"]:
            calendars[row["exchange"]].append(row)
    for rows in calendars.values():
        rows.sort(key=lambda item: item["trade_date"])
    output = []
    readiness_policy = config.get("readiness_policy", "LEGACY_READINESS_POLICY")
    readiness_v2 = readiness_policy == "MARKET_FEATURE_READINESS_V2"
    for sid in sorted({item["security_id"] for item in metadata}):
        history = [item for item in metadata if item["security_id"] == sid]
        day_map = {}
        for meta in history:
            for session in calendars[meta["exchange"]]:
                day = session["trade_date"]
                if (meta["valid_from"] <= day < (meta["valid_to"] or "9999-12-31")
                        and (not meta["listing_date"] or meta["listing_date"] <= day)
                        and (not meta["delisting_date"] or day < meta["delisting_date"])):
                    day_map[day] = (session, meta)
        series, benchmark_series, liquidity, session_days = [], [], [], []
        previous_basis = None
        for day, (session, meta) in sorted(day_map.items()):
            row = prices.get((sid, day))
            cutoff = datetime.fromisoformat(session["decision_at"])
            usable = bool(row and datetime.fromisoformat(row["available_at"]) <= cutoff
                          and datetime.fromisoformat(meta["available_at"]) <= cutoff)
            usable = usable and row["adjustment_basis"] in config["accepted_adjustments"]
            usable = usable and (not session.get("available_at")
                                 or datetime.fromisoformat(session["available_at"]) <= cutoff)
            if usable and previous_basis is not None and previous_basis != row["adjustment_basis"]:
                series, benchmark_series, liquidity, session_days = [], [], [], []
            if usable:
                previous_basis = row["adjustment_basis"]
            price_field = "raw_close" if usable and row["adjustment_basis"] == "unadjusted" else "adj_close"
            series.append(row[price_field] if usable else None)
            session_days.append(day)
            bench = benchmark.get(day)
            benchmark_series.append(bench["close"] if bench and datetime.fromisoformat(bench["available_at"]) <= cutoff else None)
            liquidity.append(row["traded_value"] if usable else None)
            if not session["is_month_end"]:
                continue
            observed_days = [observed_day for observed_day, value in zip(session_days, series) if value is not None]
            history_start = observed_days[0] if observed_days else None
            history_days = ((date.fromisoformat(day) - date.fromisoformat(history_start)).days
                            if history_start else None)
            minimum_history_years = config.get("minimum_history_years", 0)
            has_minimum_history = bool(
                history_start
                and date.fromisoformat(history_start) <= subtract_years(date.fromisoformat(day), minimum_history_years)
            ) if minimum_history_years else bool(history_start)
            features = {
                "security_id": sid,
                "ticker": meta["ticker"],
                "as_of_date": day,
                "available_at": session["decision_at"],
                "feature_version": "1.6.0" if readiness_v2 else "1.5.0",
                "data_version": data_version,
                "data_mode": config.get("data_mode", "synthetic" if config["accepted_adjustments"] == ["synthetic"] else "real"),
                "vendor_run_id": config.get("vendor_run_id"),
                "canonical_run_id": config.get("canonical_run_id"),
                "lookback_observations": sum(value is not None for value in series[-253:]),
                "missing_count": sum(value is None for value in series[-253:]),
                "history_start_date": history_start,
                "history_calendar_days": history_days,
                "history_observations": len(observed_days),
                "listing_age_days": ((date.fromisoformat(day) - date.fromisoformat(meta["listing_date"])).days
                                     if meta["listing_date"] else None),
                "adjustment_basis": previous_basis,
            }
            for window in (21, 63, 126, 252):
                features[f"mom_{window}"] = momentum(series, window)
            daily_returns = returns(series[-253:])
            for window in (63, 126):
                tail = full_window(daily_returns, window)
                deviation = stdev(tail) if tail else None
                features[f"vol_{window}"] = deviation * math.sqrt(252) if deviation is not None else None
            features["mdd_126"] = drawdown(series, 126)
            stock = full_window(daily_returns, 126)
            market = full_window(returns(benchmark_series[-127:]), 126)
            features["beta_126"] = (covariance(stock, market) / variance(market)
                                    if stock and market and variance(market) > 1e-16 else None)
            liquidity_tail = full_window(liquidity, 21)
            features["liquidity_21"] = mean(liquidity_tail) if liquidity_tail else None
            downside = full_window(daily_returns, 63)
            features["downside_vol_63"] = (math.sqrt(mean(min(value, 0) ** 2 for value in downside) * 252)
                                           if downside else None)
            features["ram_63"] = (features["mom_63"] / features["vol_63"]
                                  if features["mom_63"] is not None and features["vol_63"]
                                  and features["vol_63"] > 1e-12 else None)
            reasons = {name: "insufficient_window_gap_unavailable_or_undefined"
                       for name, value in features.items()
                       if value is None and name not in ("vendor_run_id", "canonical_run_id")}
            if not row or row["trading_status"] != "normal":
                reasons["trading_status"] = "missing_or_not_normal"
            if datetime.fromisoformat(meta["available_at"]) > cutoff:
                reasons["metadata"] = "not_available_as_of_snapshot"
            historical_identity_ready = (
                meta["identity_status"] in STRICT_HISTORICAL_IDENTITY_STATUSES
            )
            if not historical_identity_ready:
                reasons["historical_identity"] = (
                    "provisional_observed_interval_only"
                    if meta["identity_status"] == "provisional"
                    else "pilot_observed_interval_only"
                )
            if (config.get("minimum_listing_age_days", 0) > 0
                    and (features["listing_age_days"] is None
                         or features["listing_age_days"] < config["minimum_listing_age_days"])):
                reasons["metadata"] = "minimum_listing_age"
            if not has_minimum_history:
                reasons["history"] = f"minimum_{minimum_history_years}_calendar_years_of_observed_data"
            if features["missing_count"] > config.get("maximum_missing_sessions", 253):
                reasons["metadata"] = "missing_session_threshold"
            features["na_reason"] = reasons
            feature_complete = not any(features[name] is None for name in required_features)
            # V2 separates existence/quality of a real provider observation from
            # execution tradability. A valid zero-volume row remains in every
            # price window and does not fail market-data readiness.
            market_feature_ready = (
                feature_complete and has_minimum_history
                and (readiness_v2 or "trading_status" not in reasons)
                and "metadata" not in reasons
            )
            # Keep legacy/scoped eligibility semantics explicit.  In particular,
            # pilot observed-interval identity remains usable for its frozen pilot
            # contract, while strict historical research readiness is separate.
            features["feature_complete"] = feature_complete
            features["market_feature_ready"] = market_feature_ready
            features["historical_identity_ready"] = historical_identity_ready
            features["research_ready"] = market_feature_ready and historical_identity_ready
            features["eligibility"] = (
                market_feature_ready
                and meta["identity_status"] in LEGACY_SCOPED_IDENTITY_STATUSES
            )
            if not has_minimum_history and "trading_status" not in reasons and "metadata" not in reasons:
                features["universe_segment"] = "REFERENCE_ONLY"
            elif features["eligibility"]:
                features["universe_segment"] = "ELIGIBLE_FOR_CLUSTERING"
            else:
                features["universe_segment"] = "EXCLUDED"
            output.append(features)
    return output
