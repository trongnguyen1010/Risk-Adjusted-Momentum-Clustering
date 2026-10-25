"""Target portfolios per decision date for the M3 strategies (M3_PLAN §5 steps 1–7, Q5–Q10, Q14).

All rules come from the strategy config; nothing here reads prices after the decision date.
"""
from .ranking import combined_scores, n_select, select_top
from .universe import allowed_clusters, candidate_universe, cluster_order

FINANCIAL_SECTORS = ('BANK', 'SECURITIES', 'INSURANCE')


def financial_allowed(fin_labels, rule):
    """{fiscal_year: allowed B clusters} by median ROE (ties: lower median D/E)."""
    return {y: allowed_clusters(cluster_order(list(v.values()), 'roe', 'debt_to_equity', higher_tiebreak=False), rule)
            for y, v in fin_labels.items()}


class Strategies:
    def __init__(self, cfg, market, fin_labels, availability, sector, indicators):
        self.cfg, self.market, self.fin = cfg, market, fin_labels
        self.avail, self.sector, self.ind = availability, sector, indicators
        self.allowed_fin = financial_allowed(fin_labels, cfg['financial_rule'])
        self.mc = cfg['market_criteria']        # {feature: higher_is_better}
        self.fc = cfg['financial_criteria']     # {indicator: higher_is_better}
        self.n_min = cfg['n_min']
        self.share = cfg['top_share']

    def _rows(self, date, cands, use_market=True, use_fin=True):
        rows = {}
        for c in cands:
            row = {}
            if use_market:
                row.update({k: c['features'].get(k) for k in self.mc})
            if use_fin:
                vals = self.ind.get((c['ticker'], c['financial_year']), {}) if c.get('financial_year') else {}
                row.update({k: vals.get(k) for k in self.fc})
            rows[c['ticker']] = row
        return rows

    def _select(self, rows, cands, market_crit, fin_crit, weight_market):
        scores = combined_scores(rows, market_crit, fin_crit, weight_market=weight_market)
        liquidity = {c['ticker']: c['features'].get('liquidity_21') for c in cands}
        picks = select_top({t: v['score'] for t, v in scores.items()}, liquidity, self.share)
        return picks, scores

    def combined(self, date):
        cands, audit, _ = candidate_universe(self.market[date], date, self.fin, self.avail, self.sector,
                                             self.allowed_fin, market_rule=self.cfg['market_rule'])
        return self._finish(date, cands, audit, self.mc, self.fc, self.cfg['combined_weight_market'])

    def market_only(self, date):
        rows = [r for r in self.market[date] if r['liquidity'] != 'ILLIQUID']
        order = cluster_order([(r['cluster'], r['features']) for r in rows], 'mom_126', 'mdd_126')
        allowed = allowed_clusters(order, self.cfg['market_rule']) or set()
        cands = [dict(ticker=r['ticker'], features=r['features'], financial_year=None)
                 for r in rows if r['cluster'] in allowed]
        audit = [dict(decision_date=date, ticker=r['ticker'], combined=r['cluster'] in allowed) for r in rows]
        return self._finish(date, cands, audit, self.mc, {}, 1.0)

    def financial_only(self, date):
        # Financial Eligible Pool among stocks that trade (same liquidity rule as the market side).
        cands, audit, _ = candidate_universe(self.market[date], date, self.fin, self.avail, self.sector, self.allowed_fin,
                                             leading_market={r['cluster'] for r in self.market[date]})
        return self._finish(date, cands, audit, {}, self.fc, 0.0)

    def equal_weight(self, date):
        names = sorted(r['ticker'] for r in self.market[date] if r['liquidity'] != 'ILLIQUID')
        return dict(target={t: 1 / len(names) for t in names}, candidates=len(names), picks=names, audit=[])

    def momentum_only(self, date):
        rows = [r for r in self.market[date] if r['liquidity'] != 'ILLIQUID' and r['features'].get('mom_126') is not None]
        rows.sort(key=lambda r: (-r['features']['mom_126'], r['ticker']))
        n = n_select(len(rows), self.share)
        picks = [r['ticker'] for r in rows[:n]]
        return dict(target={t: 1 / n for t in picks}, candidates=len(rows), picks=picks, audit=[])

    def _finish(self, date, cands, audit, market_crit, fin_crit, weight_market):
        rows = self._rows(date, cands, bool(market_crit), bool(fin_crit))
        if len(cands) < self.n_min:
            names = {c['ticker'] for c in cands}
            return dict(target=None, keep_names=names, candidates=len(cands), picks=[], audit=audit,
                        status='UNIVERSE_TOO_SMALL')
        picks, scores = self._select(rows, cands, market_crit, fin_crit, weight_market)
        return dict(target={t: w for t, _, w in picks}, candidates=len(cands), picks=[t for t, _, _ in picks],
                    scores=scores, audit=audit, status='OK')

    def target_for(self, name, date):
        """Engine-ready target: a weight dict, or (Q6, universe too small) a function that keeps the current book and
        only sells the names that left the candidate set."""
        result = getattr(self, name)(date)
        if result.get('target') is None:
            keep = result['keep_names']
            result['engine_target'] = lambda pre: {t: w for t, w in pre.items() if t != 'CASH' and t in keep}
        else:
            result['engine_target'] = result['target']
        return result
