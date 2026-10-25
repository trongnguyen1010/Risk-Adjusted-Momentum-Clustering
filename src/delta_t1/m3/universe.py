"""PIT financial state, leading clusters and the Candidate Universe (M3_PLAN §5 steps 1–4, Q2/Q4/Q5/Q10)."""
from datetime import date
from statistics import median

STALE_MONTHS = 18


def _median(values):
    values = [v for v in values if v is not None]
    return median(values) if values else None


def leading_cluster(members, key, tiebreak, higher_tiebreak=True):
    """Cluster with the highest median `key`; ties broken by median `tiebreak`. members: [(cluster, features)].

    Returns (cluster, {cluster: (median key, median tiebreak)}) or (None, …) when it cannot be decided.
    """
    groups = {}
    for cluster, features in members:
        if cluster is None or cluster < 0:
            continue
        groups.setdefault(cluster, []).append(features)
    stats = {c: (_median(f.get(key) for f in fs), _median(f.get(tiebreak) for f in fs)) for c, fs in groups.items()}
    ranked = [(c, s) for c, s in stats.items() if s[0] is not None]
    if not ranked:
        return None, stats
    sign = 1 if higher_tiebreak else -1
    ranked.sort(key=lambda cs: (cs[1][0], sign * cs[1][1] if cs[1][1] is not None else float('-inf')), reverse=True)
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None, stats
    return ranked[0][0], stats


def cluster_order(members, key, tiebreak, higher_tiebreak=True):
    """Clusters ranked best → worst by median `key` (ties by median `tiebreak`). Same profile-only rule as
    leading_cluster; used for the 'top two' and 'all but the weakest' variants (M3_PLAN Q5)."""
    lead, stats = leading_cluster(members, key, tiebreak, higher_tiebreak)
    sign = 1 if higher_tiebreak else -1
    ranked = [c for c, st in stats.items() if st[0] is not None]
    ranked.sort(key=lambda c: (stats[c][0], sign * stats[c][1] if stats[c][1] is not None else float('-inf')),
                reverse=True)
    return ranked if lead is not None else []


def allowed_clusters(order, rule):
    """'leading' → best only; 'top2' → best two; 'not_weakest' → all but the worst (needs ≥ 2 clusters)."""
    if not order:
        return None
    if rule == 'leading':
        return {order[0]}
    if rule == 'top2':
        return set(order[:2])
    if rule == 'not_weakest':
        return set(order[:-1]) if len(order) > 1 else set(order)
    raise ValueError(f'unknown cluster rule {rule!r}')


def stale_after(fiscal_year, months=STALE_MONTHS):
    """Last date a fiscal_year report may be used (period end 31/12 + `months`)."""
    total = 12 + months
    year, month = fiscal_year + (total - 1) // 12, (total - 1) % 12 + 1
    return date(year, month, 30 if month != 2 else 28).isoformat()


def financial_state(ticker, decision_date, availability, years):
    """Latest fiscal year usable at decision_date, or (None, reason). Never reads a row with usable_from > t."""
    usable = [y for y in years if (row := availability.get((ticker, y))) and row['usable_from_date']
              and row['usable_from_date'] <= decision_date]
    if not usable:
        return None, 'FINANCIAL_NOT_AVAILABLE'
    year = max(usable)
    if decision_date > stale_after(year):
        return None, 'FINANCIAL_STALE'
    return year, None


def candidate_universe(market_rows, decision_date, fin_labels, availability, sector, leading_fin, *,
                       include_illiquid=False, leading_market=None, market_rule='leading'):
    """Market Eligible Pool ∩ Financial Eligible Pool with one primary exclusion reason per ticker.

    leading_fin: {fiscal_year: allowed B cluster(s)} (an int or a set). leading_market: allowed A cluster(s), or None
    to derive them from this snapshot's profile with `market_rule`. Returns (candidates, audit, allowed market set).
    """
    as_set = lambda v: None if v is None else (set(v) if isinstance(v, (set, frozenset, list, tuple)) else {v})  # noqa: E731
    pool_rows = [r for r in market_rows if include_illiquid or r['liquidity'] != 'ILLIQUID']
    if leading_market is None:
        order = cluster_order([(r['cluster'], r['features']) for r in pool_rows], 'mom_126', 'mdd_126')
        leading_market = allowed_clusters(order, market_rule)
    leading_market = as_set(leading_market)
    leading_fin = {y: as_set(v) for y, v in leading_fin.items()}
    years = sorted(fin_labels)
    candidates, audit = [], []
    for r in market_rows:
        t = r['ticker']
        reason, year = None, None
        if r['liquidity'] == 'ILLIQUID' and not include_illiquid:
            reason = 'MARKET_ILLIQUID'
        elif leading_market is None:
            reason = 'CLUSTER_PROFILE_AMBIGUOUS'
        elif r['cluster'] not in leading_market:
            reason = 'MARKET_NOT_IN_LEADING_CLUSTER'
        market_ok = reason is None
        if sector.get(t) in ('BANK', 'SECURITIES', 'INSURANCE'):
            fin_reason = 'FINANCIAL_SECTOR_NO_B'
        else:
            year, fin_reason = financial_state(t, decision_date, availability, years)
            if fin_reason is None:
                label = fin_labels.get(year, {}).get(t)
                if label is None:
                    fin_reason = 'FINANCIAL_STATE_MISSING'
                elif leading_fin.get(year) is None:
                    fin_reason = 'CLUSTER_PROFILE_AMBIGUOUS'
                elif label[0] not in leading_fin[year]:
                    fin_reason = 'FINANCIAL_NOT_IN_LEADING_CLUSTER'
        fin_ok = fin_reason is None
        audit.append(dict(decision_date=decision_date, ticker=t, market_cluster=r['cluster'], market_eligible=market_ok,
                          financial_year=year, financial_eligible=fin_ok, combined=market_ok and fin_ok,
                          reason=reason or fin_reason or ''))
        if market_ok and fin_ok:
            candidates.append(dict(ticker=t, market_cluster=r['cluster'], financial_year=year,
                                   financial_cluster=fin_labels[year][t][0], features=r['features']))
    return candidates, audit, leading_market
