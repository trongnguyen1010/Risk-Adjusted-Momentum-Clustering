"""Calendar-aligned windows. Missing sessions remain None, never forward filled."""
import math
from datetime import datetime, date
from statistics import mean, stdev, variance, covariance
from collections import defaultdict


def subtract_years(value: date, years: int) -> date:
    """Calendar-year cutoff; map Feb 29 to Feb 28 in a non-leap target year."""
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def momentum(prices, window):
    values = prices[-window - 1:]
    return values[-1] / values[0] - 1 if len(values) == window + 1 and all(v is not None and v > 0 for v in values) else None


def returns(prices):
    return [b / a - 1 if a is not None and b is not None and a > 0 else None for a, b in zip(prices, prices[1:])]


def drawdown(prices, window):
    values = prices[-window:]
    if len(values) < window or any(v is None for v in values):
        return None
    peak, worst = values[0], 0.0
    for value in values:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    return worst


def full_window(values, size):
    tail = values[-size:]
    return tail if len(tail) == size and all(v is not None for v in tail) else None


def build_features(tables, config, data_version):
    """Monthly rows only, using calendar's explicitly closed month-end sessions."""
    metadata = tables["securities"]
    prices = {(r["security_id"], r["trade_date"]): r for r in tables["prices_daily"]}
    benchmark = {r["trade_date"]: r for r in tables.get("benchmark_daily", []) if r["index_id"] == config.get("benchmark_id", "VNINDEX")}
    calendars = defaultdict(list)
    for row in tables["trading_calendar"]:
        if row["is_open"]:
            calendars[row["exchange"]].append(row)
    for rows in calendars.values():
        rows.sort(key=lambda x: x["trade_date"])
    output = []
    for sid in sorted({m["security_id"] for m in metadata}):
        history = [m for m in metadata if m["security_id"] == sid]
        # Union of exchange calendars, then choose the exchange valid for each day.
        day_map = {}
        for meta in history:
            for session in calendars[meta["exchange"]]:
                d = session["trade_date"]
                if meta["valid_from"] <= d < (meta["valid_to"] or "9999-12-31") and (not meta["listing_date"] or meta["listing_date"] <= d) and (not meta["delisting_date"] or d < meta["delisting_date"]):
                    day_map[d] = (session, meta)
        series, bseries, liquidity, price_records, session_days = [], [], [], [], []
        previous_basis = None
        for day, (session, meta) in sorted(day_map.items()):
            row = prices.get((sid, day))
            cutoff = datetime.fromisoformat(session["decision_at"])
            usable = row and datetime.fromisoformat(row["available_at"]) <= cutoff and datetime.fromisoformat(meta["available_at"]) <= cutoff
            usable = usable and row["adjustment_basis"] in config["accepted_adjustments"]
            usable = usable and (not session.get("available_at") or datetime.fromisoformat(session["available_at"]) <= cutoff)
            if usable and previous_basis is not None and previous_basis != row["adjustment_basis"]:
                # Never splice incompatible return conventions into a rolling window.
                series, bseries, liquidity, price_records, session_days = [], [], [], [], []
            if usable:
                previous_basis = row["adjustment_basis"]
            price_field = "raw_close" if usable and row["adjustment_basis"] == "unadjusted" else "adj_close"
            series.append(row[price_field] if usable else None)
            price_records.append(row if usable else None)
            session_days.append(day)
            bench = benchmark.get(day)
            bseries.append(bench["close"] if bench and datetime.fromisoformat(bench["available_at"]) <= cutoff else None)
            liquidity.append(row["traded_value"] if usable else None)
            if not session["is_month_end"]:
                continue
            observed_days = [d for d, value in zip(session_days, series) if value is not None]
            history_start = observed_days[0] if observed_days else None
            history_days = ((date.fromisoformat(day) - date.fromisoformat(history_start)).days
                            if history_start else None)
            minimum_history_years = config.get("minimum_history_years", 0)
            has_minimum_history = bool(
                history_start
                and date.fromisoformat(history_start)
                <= subtract_years(date.fromisoformat(day), minimum_history_years)
            ) if minimum_history_years else bool(history_start)
            features = {"security_id": sid, "ticker": meta["ticker"], "as_of_date": day, "available_at": session["decision_at"],
                        "feature_version": "1.3.0", "data_version": data_version,
                        "data_mode": config.get("data_mode", "synthetic" if config["accepted_adjustments"] == ["synthetic"] else "real"),
                        "vendor_run_id": config.get("vendor_run_id"), "canonical_run_id": config.get("canonical_run_id"),
                        "lookback_observations": sum(v is not None for v in series[-253:]),
                        "missing_count": sum(v is None for v in series[-253:]),
                        "history_start_date": history_start,
                        "history_calendar_days": history_days,
                        "history_observations": len(observed_days),
                        "listing_age_days": (date.fromisoformat(day) - date.fromisoformat(meta["listing_date"])).days if meta["listing_date"] else None,
                        "adjustment_basis": previous_basis}
            for window in (21, 63, 126, 252):
                features[f"mom_{window}"] = momentum(series, window)
            rs = returns(series[-253:])
            for window in (63, 126):
                tail = full_window(rs, window)
                sd = stdev(tail) if tail else None
                features[f"vol_{window}"] = sd * math.sqrt(252) if sd is not None else None
                # rf is either an explicit experimental constant or as-of daily rate records.
                rf_values = []
                for rate_day in session_days[-window:]:
                    if config.get("rf_annual") is not None:
                        annual = config["rf_annual"]
                    else:
                        candidates = [r for r in tables.get("risk_free_rate", []) if r["tenor"] == config.get("rf_tenor") and r["date"] <= rate_day and datetime.fromisoformat(r["available_at"]) <= datetime.fromisoformat(rate_day + "T00:00:00+07:00")]
                        annual = max(candidates, key=lambda r: (r["date"], r["available_at"]))["annual_rate"] if candidates else None
                    rf_values.append((1 + annual) ** (1 / 252) - 1 if annual is not None else None)
                excess = [r - rf for r, rf in zip(tail, rf_values)] if tail and full_window(rf_values, window) else None
                excess_sd = stdev(excess) if excess else None
                features[f"sharpe_{window}"] = math.sqrt(252) * mean(excess) / excess_sd if excess_sd and excess_sd > 1e-12 else None
            features["mdd_126"] = drawdown(series, 126)
            stock, market = full_window(rs, 126), full_window(returns(bseries[-127:]), 126)
            features["beta_126"] = covariance(stock, market) / variance(market) if stock and market and variance(market) > 1e-16 else None
            lt = full_window(liquidity, 21)
            features["liquidity_21"] = mean(lt) if lt else None
            downside = full_window(rs, 63)
            features["downside_vol_63"] = math.sqrt(mean(min(r, 0) ** 2 for r in downside) * 252) if downside else None
            features["ram_63"] = features["mom_63"] / features["vol_63"] if features["mom_63"] is not None and features["vol_63"] and features["vol_63"] > 1e-12 else None
            reasons = {k: "insufficient_window_gap_unavailable_or_undefined" for k, v in features.items() if v is None and k not in ("vendor_run_id", "canonical_run_id")}
            if not row or row["trading_status"] != "normal":
                reasons["trading_status"] = "missing_or_not_normal"
            if datetime.fromisoformat(meta["available_at"]) > cutoff:
                reasons["metadata"] = "not_available_as_of_snapshot"
            if meta["identity_status"] == "provisional":
                reasons["metadata"] = "unverified_historical_identity"
            if config.get("minimum_listing_age_days", 0) > 0 and (features["listing_age_days"] is None or features["listing_age_days"] < config["minimum_listing_age_days"]):
                reasons["metadata"] = "minimum_listing_age"
            if not has_minimum_history:
                reasons["history"] = f"minimum_{minimum_history_years}_calendar_years_of_observed_data"
            if features["missing_count"] > config.get("maximum_missing_sessions", 253):
                reasons["metadata"] = "missing_session_threshold"
            features["na_reason"] = reasons
            feature_complete = not any(features[k] is None for k in config["required_features"])
            features["eligibility"] = feature_complete and has_minimum_history and "trading_status" not in reasons and "metadata" not in reasons
            if not has_minimum_history and "trading_status" not in reasons and "metadata" not in reasons:
                features["universe_segment"] = "REFERENCE_ONLY"
            elif features["eligibility"]:
                features["universe_segment"] = "ELIGIBLE_FOR_CLUSTERING"
            else:
                features["universe_segment"] = "EXCLUDED"
            output.append(features)
    return output
