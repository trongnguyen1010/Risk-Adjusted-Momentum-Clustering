"""Criteria percentiles, combined score and top-30% selection (M3_PLAN Q7–Q9, D04)."""
import math

TOP_SHARE = 0.30


def n_select(n_candidates, share=TOP_SHARE):
    """ceil(share × N) with a guard against float noise (0.3 × 10 = 3.0000000000000004)."""
    return math.ceil(round(share * n_candidates, 9)) if n_candidates > 0 else 0


def percentiles(values):
    """Average-rank percentile in [0, 1] (higher value → higher percentile); None stays None."""
    present = sorted(v for v in values.values() if v is not None)
    if not present:
        return {k: None for k in values}
    if len(present) == 1:
        return {k: (0.5 if v is not None else None) for k, v in values.items()}
    out = {}
    for key, v in values.items():
        if v is None:
            out[key] = None
            continue
        below = sum(1 for x in present if x < v)
        equal = sum(1 for x in present if x == v)
        out[key] = (below + (equal - 1) / 2) / (len(present) - 1)
    return out


def combined_scores(rows, market_criteria, financial_criteria, *, missing=0.5, weight_market=0.5):
    """rows: {ticker: {criterion: value}}. Criteria: {name: higher_is_better}. Returns {ticker: dict(score, ...)}.

    A missing criterion gets the neutral percentile `missing` and a flag; all financial criteria missing → excluded.
    """
    pct = {}
    for name, higher in {**market_criteria, **financial_criteria}.items():
        raw = {t: (v[name] if higher or v.get(name) is None else -v[name]) for t, v in rows.items()}
        pct[name] = percentiles(raw)
    out = {}
    for t in rows:
        fin = [pct[c][t] for c in financial_criteria]
        if all(p is None for p in fin):
            continue
        mkt = [pct[c][t] if pct[c][t] is not None else missing for c in market_criteria]
        fin_filled = [p if p is not None else missing for p in fin]
        s_market, s_fin = sum(mkt) / len(mkt), sum(fin_filled) / len(fin_filled)
        out[t] = dict(s_market=s_market, s_fin=s_fin, score=weight_market * s_market + (1 - weight_market) * s_fin,
                      missing=[c for c in (*market_criteria, *financial_criteria) if pct[c][t] is None])
    return out


def select_top(scores, tiebreak, share=TOP_SHARE):
    """Rank by score desc, then tiebreak desc, then ticker; take n_select(N). Returns [(ticker, rank, weight)]."""
    order = sorted(scores, key=lambda t: (-scores[t], -(tiebreak.get(t) or 0.0), t))
    n = n_select(len(order), share)
    return [(t, i + 1, 1.0 / n) for i, t in enumerate(order[:n])]
