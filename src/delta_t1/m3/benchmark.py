"""VNINDEX benchmark on the same valuation dates as the strategy (price index, M3_PLAN §9)."""


def benchmark_nav(closes, dates):
    """closes: {date: VNINDEX close}; dates: the strategy's valuation dates. NAV starts at 1 on dates[0]."""
    base = closes[dates[0]]
    return [(d, closes[d] / base) for d in dates if d in closes]


def period_returns(nav):
    return [(nav[i][0], nav[i][1] / nav[i - 1][1] - 1) for i in range(1, len(nav))]
