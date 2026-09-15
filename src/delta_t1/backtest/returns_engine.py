"""Self-financing fractional RETURN-SPACE simulation, not exchange share accounting.

Adjusted levels represent normalized investment units. They never stand in for
raw execution prices or integer quantities. Unresolved marks block evaluation.
"""
from datetime import datetime
import math


def rebalance(values: dict[str, float], cash: float, target: dict[str, float], rate: float) -> tuple[dict, float, float, float]:
    """Solve post-cost allocation; costs charged on full traded notional (L1)."""
    nav = cash + sum(values.values())
    ids = values.keys() | target.keys()
    if any(not math.isfinite(w) or w < 0 for w in target.values()) or sum(target.values()) > 1 + 1e-12 or not 0 <= rate < .1:
        raise ValueError("invalid long-only target or cost rate")
    low, high = 0.0, nav
    for _ in range(80):
        cost = (low + high) / 2
        traded = sum(abs(target.get(s, 0) * (nav - cost) - values.get(s, 0)) for s in ids)
        if cost < rate * traded:
            low = cost
        else:
            high = cost
    cost = (low + high) / 2 if rate else 0.0
    result = {s: w * (nav - cost) for s, w in target.items() if w > 0}
    traded = sum(abs(result.get(s, 0) - values.get(s, 0)) for s in ids)
    return result, (nav - cost) * max(0.0, 1 - sum(target.values())), cost, traded / nav


def simulate(targets: list[dict], tables: dict, config: dict) -> dict:
    """Next-session close, explicit daily calendar, drifted weights and cash.

    Missing prices for an existing holding are errors, including delisted names;
    no silent liquidation, stale-price fill, or compression across missing days.
    """
    if config["execution"] != "next_close" or config["rebalance_frequency"] != "monthly":
        raise ValueError("return engine supports monthly next_close only")
    if config["return_basis"] not in ("synthetic", "split_adjusted", "vendor_adjusted", "unadjusted", "total_return"):
        raise ValueError("verified adjusted return convention required")
    if config["return_basis"] in ("vendor_adjusted", "unadjusted") and not config.get("pilot_price_proxy_acknowledged"):
        raise ValueError("pilot price-proxy limitation must be acknowledged")
    mark_field = "raw_close" if config["return_basis"] == "unadjusted" else "adj_close"
    if not targets:
        raise ValueError("no target snapshots")
    rate = (config["transaction_cost_bps"] + config["slippage_bps"]) / 10000
    if not math.isfinite(rate) or not 0 <= rate < .1 or any(config[k] < 0 for k in ("transaction_cost_bps", "slippage_bps", "minimum_holding_sessions")):
        raise ValueError("invalid execution costs/holding constraint")
    sessions = sorted((r for r in tables["trading_calendar"] if r["exchange"] == config["exchange"] and r["is_open"]), key=lambda r: r["trade_date"])
    scheduled, pending = {}, []
    for target in sorted(targets, key=lambda t: datetime.fromisoformat(t["decision_time"])):
        candidates = [s for s in sessions if s["trade_date"] > target["snapshot_date"] and datetime.fromisoformat(s["close_at"]) > datetime.fromisoformat(target["decision_time"])]
        if not candidates:
            pending.append(target)
            continue
        day = candidates[0]["trade_date"]
        if day in scheduled:
            raise ValueError("multiple signals map to the same execution session")
        scheduled[day] = target
    if not scheduled:
        raise ValueError("no execution session after signals")
    prices = {(r["security_id"], r["trade_date"]): r for r in tables["prices_daily"]}
    calendar = {(r["exchange"], r["trade_date"]): r for r in tables["trading_calendar"]}
    benchmarks = {r["trade_date"]: r for r in tables["benchmark_daily"] if r["index_id"] == config["benchmark_id"]}
    values, gross_values, cash, gross_cash = {}, {}, 1.0, 1.0
    previous_prices, entered = {}, {}
    rows, executions = [], []
    previous_nav = previous_gross = 1.0
    previous_benchmark = None
    peak = 1.0
    for step, session in enumerate(s for s in sessions if s["trade_date"] >= min(scheduled)):
        day = session["trade_date"]
        target = scheduled.get(day)
        ids = values.keys() | gross_values.keys() | (target["weights"].keys() if target else set())
        current = {}
        for sid in ids:
            record = prices.get((sid, day))
            if not record or record[mark_field] is None or record["adjustment_basis"] != config["return_basis"]:
                raise ValueError(f"missing or incompatible holding/execution mark: {sid} {day}")
            actual_session = calendar.get((record["exchange"], day))
            if not actual_session or not actual_session["is_open"] or datetime.fromisoformat(actual_session["close_at"]) != datetime.fromisoformat(session["close_at"]):
                raise ValueError("return engine requires synchronized exchange close sessions")
            if datetime.fromisoformat(record["available_at"]) > datetime.fromisoformat(actual_session["decision_at"]):
                raise ValueError("holding/execution mark unavailable by daily valuation cutoff")
            if target and record["trading_status"] != "normal":
                raise ValueError("cannot rebalance suspended/unknown security")
            current[sid] = record[mark_field]
        for book in (values, gross_values):
            for sid in book:
                book[sid] *= current[sid] / previous_prices[sid]
        cost, turnover = 0.0, 0.0
        if target:
            for sid in values:
                current_nav = cash + sum(values.values())
                if target["weights"].get(sid, 0) * current_nav < values[sid] - 1e-12 and step - entered[sid] < config["minimum_holding_sessions"]:
                    raise ValueError("target violates minimum holding constraint")
            old = set(values)
            values, cash, cost, turnover = rebalance(values, cash, target["weights"], rate)
            gross_values, gross_cash, _, _ = rebalance(gross_values, gross_cash, target["weights"], 0)
            for sid in values.keys() - old:
                entered[sid] = step
            executions.append(dict(date=day, signal_time=target["decision_time"], execution_time=session["close_at"],
                                   target_weights=target["weights"], cost=cost, traded_notional_over_nav=turnover))
        nav, gross_nav = cash + sum(values.values()), gross_cash + sum(gross_values.values())
        benchmark = benchmarks.get(day)
        if not benchmark or datetime.fromisoformat(benchmark["available_at"]) > datetime.fromisoformat(session["decision_at"]):
            raise ValueError("missing/unavailable benchmark session: " + day)
        level = benchmark["close"]
        peak = max(peak, nav)
        rows.append(dict(date=day, net_nav=nav, gross_nav=gross_nav, cash_fraction=cash / nav,
                         net_return=nav / previous_nav - 1, gross_return=gross_nav / previous_gross - 1,
                         benchmark_return=level / previous_benchmark - 1 if previous_benchmark else 0.0,
                         cost=cost, turnover=turnover, drawdown=nav / peak - 1,
                         weights={s: value / nav for s, value in values.items()}))
        previous_nav, previous_gross, previous_benchmark = nav, gross_nav, level
        previous_prices = current
    return dict(nav=rows, executions=executions, pending_signals=pending, mode="fractional_return_space",
                limitations=["No raw share quantities, lots, settlement or exchange liquidity fills", "No cash-dividend reinvestment for split_adjusted basis", "Missing/delisted marks block instead of assuming recovery", "Cash earns zero by explicit simulation assumption"])
