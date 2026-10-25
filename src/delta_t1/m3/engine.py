"""Monthly rebalance engine in value space (M3_PLAN §5 steps 8–13, D05–D08, Q12–Q13).

Prices and tradability come from callables so the engine is testable with synthetic data:
  price(ticker, date) -> float | None         (adjusted close; None = no valid price that day)
  tradable(ticker, date, side) -> bool        (side 'BUY' or 'SELL')
Cash earns 0, costs are 0 (cost scenarios are applied in reporting, from the ledger).
"""
from dataclasses import dataclass, field

EPS = 1e-12


@dataclass
class Portfolio:
    cash: float = 1.0
    values: dict = field(default_factory=dict)
    marks: dict = field(default_factory=dict)  # ticker -> last price used for valuation

    @property
    def nav(self):
        return self.cash + sum(self.values.values())

    def weights(self):
        nav = self.nav
        return {t: v / nav for t, v in self.values.items()} | {'CASH': self.cash / nav}


def revalue(pf, date, price):
    """Mark holdings to `date`; a missing price keeps the last mark and is reported as PRICE_STALE."""
    stale = []
    for t in list(pf.values):
        p = price(t, date)
        if p is None:
            stale.append(t)
            continue
        pf.values[t] *= p / pf.marks[t]
        pf.marks[t] = p
    return stale


def rebalance(pf, target, date, price, tradable):
    """Move pf toward `target` ({ticker: weight}, Σ ≤ 1) at `date`. Sells first, then buys.

    BUY_FAILED: money stays in cash. SELL_FAILED: position stays, no cash. If cash cannot cover the remaining buys,
    every remaining buy is scaled by execution_scale = cash / required (D07). Returns (ledger rows, turnover).
    """
    nav = pf.nav
    pre = {t: v / nav for t, v in pf.values.items()}
    ledger, traded = [], 0.0
    names = sorted(set(pre) | set(target))
    deltas = {t: target.get(t, 0.0) - pre.get(t, 0.0) for t in names}
    for t in names:
        d = deltas[t]
        if d >= -EPS:
            continue
        amount = -d * nav
        if tradable(t, date, 'SELL') and price(t, date) is not None:
            pf.values[t] -= amount
            pf.cash += amount
            traded += amount
            status = 'EXECUTED'
            if pf.values[t] <= EPS * nav:
                del pf.values[t]
                pf.marks.pop(t, None)
        else:
            status = 'SELL_FAILED'
        ledger.append(dict(date=date, ticker=t, side='SELL', pre_weight=pre.get(t, 0.0), target_weight=target.get(t, 0.0),
                           intended=amount, executed=amount if status == 'EXECUTED' else 0.0, scale=1.0, status=status))
    buys = []
    for t in names:
        d = deltas[t]
        if d <= EPS:
            if abs(d) <= EPS and t in target:
                ledger.append(dict(date=date, ticker=t, side='HOLD', pre_weight=pre.get(t, 0.0),
                                   target_weight=target[t], intended=0.0, executed=0.0, scale=1.0, status='HOLD'))
            continue
        ok = tradable(t, date, 'BUY') and price(t, date) is not None
        buys.append((t, d * nav, ok))
    required = sum(a for _, a, ok in buys if ok)
    scale = min(1.0, pf.cash / required) if required > EPS else 1.0
    for t, amount, ok in buys:
        executed = amount * scale if ok else 0.0
        if executed > 0:
            pf.values[t] = pf.values.get(t, 0.0) + executed
            pf.marks.setdefault(t, price(t, date))
            pf.cash -= executed
            traded += executed
        ledger.append(dict(date=date, ticker=t, side='BUY', pre_weight=pre.get(t, 0.0), target_weight=target.get(t, 0.0),
                           intended=amount, executed=executed, scale=scale if ok else 1.0,
                           status=('EXECUTED' if scale >= 1 - EPS else 'SCALED') if ok else 'BUY_FAILED'))
    if pf.cash < 0 and pf.cash > -EPS * nav:
        pf.cash = 0.0
    return ledger, traded / (2 * nav)


def run(schedule, price, tradable, end_date=None):
    """schedule: [(decision_date, execution_date, target)], target = dict or callable(pre_weights) -> dict.

    Starts 100% cash; positions carry over between periods (no reset). The last period is valued at end_date.
    Returns dict(nav=[(date, nav)], ledger=[...], holdings=[...], turnover=[(date, value)], stale=[(date, ticker)]).
    """
    pf = Portfolio()
    out = dict(nav=[], ledger=[], holdings=[], turnover=[], stale=[])
    for decision_date, execution_date, target in schedule:
        assert execution_date > decision_date, 'execution must follow the decision'
        out['stale'] += [(execution_date, t) for t in revalue(pf, execution_date, price)]
        out['nav'].append((execution_date, pf.nav))
        goal = target(pf.weights()) if callable(target) else target
        assert sum(goal.values()) <= 1 + 1e-9 and min(goal.values(), default=0) >= 0, 'invalid target weights'
        ledger, turnover = rebalance(pf, goal, execution_date, price, tradable)
        out['ledger'] += ledger
        out['turnover'].append((execution_date, turnover))
        out['holdings'] += [dict(date=execution_date, ticker=t, weight=w) for t, w in pf.weights().items()]
    if end_date and schedule:
        out['stale'] += [(end_date, t) for t in revalue(pf, end_date, price)]
        out['nav'].append((end_date, pf.nav))
    return out
