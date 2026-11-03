"""Target portfolios per decision date for the M3 strategies (KE_HOACH_M3_SCHEMA_GITHUB §3, §9).

All rules come from the strategy config; nothing here reads prices after the decision date.

Audit rows (one per ticker considered, written to universe_audit_<strategy>.csv, plan §16.10):
  decision_date, ticker, market_cluster, market_eligible, financial_year, financial_cluster, financial_eligible,
  in_candidate_universe, reason, flags
"""
from .ranking import combined_scores, n_select, select_top
from .universe import STALE_MONTHS, allowed_clusters, candidate_universe, cluster_order

FINANCIAL_SECTORS = ('BANK', 'SECURITIES', 'INSURANCE')
AUDIT_KEYS = ('decision_date', 'ticker', 'market_cluster', 'market_eligible', 'financial_year', 'financial_cluster',
              'financial_eligible', 'in_candidate_universe', 'reason', 'flags')


def financial_order_from_labels(fin_labels):
    """Legacy fallback (B v4 reference only): cluster order by median ROE (ties: lower median D/E) over the whole
    fiscal year. Official runs read the order frozen at the B-PIT cutoff instead (plan §3.1.5, §3.4.1)."""
    return {y: cluster_order(list(v.values()), 'roe', 'debt_to_equity', higher_tiebreak=False)
            for y, v in fin_labels.items()}


def financial_allowed(fin_order, rule):
    """{fiscal_year: allowed B clusters} from a {fiscal_year: [best → worst]} order."""
    return {y: allowed_clusters(order, rule) for y, order in fin_order.items()}


def _audit_row(decision_date, ticker, **values):
    row = dict.fromkeys(AUDIT_KEYS, '')
    row.update(decision_date=decision_date, ticker=ticker, **values)
    return row


class Strategies:
    def __init__(self, cfg, market, fin_labels, availability, sector, indicators, fin_order=None):
        self.cfg, self.market, self.fin = cfg, market, fin_labels
        self.avail, self.sector, self.ind = availability, sector, indicators
        self.fin_order = fin_order if fin_order is not None else financial_order_from_labels(fin_labels)
        self.allowed_fin = financial_allowed(self.fin_order, cfg['financial_rule'])
        self.mc = cfg['market_criteria']        # {feature: higher_is_better}
        self.fc = cfg['financial_criteria']     # {indicator: higher_is_better}
        self.n_min = cfg['n_min']
        self.share = cfg['top_share']
        self.stale_months = cfg.get('stale_months', STALE_MONTHS)

    def _universe(self, date, **kwargs):
        cands, raw_audit, _ = candidate_universe(self.market[date], date, self.fin, self.avail, self.sector,
                                                 self.allowed_fin, stale_months=self.stale_months, **kwargs)
        fin_cluster = {c['ticker']: c['financial_cluster'] for c in cands}
        audit = [_audit_row(date, a['ticker'], market_cluster=a['market_cluster'], market_eligible=a['market_eligible'],
                            financial_year=a['financial_year'] or '', financial_cluster=fin_cluster.get(a['ticker'], ''),
                            financial_eligible=a['financial_eligible'], in_candidate_universe=a['combined'],
                            reason=a['reason']) for a in raw_audit]
        return cands, audit

    def _rows(self, cands, use_market=True, use_fin=True):
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

    def combined(self, date):
        cands, audit = self._universe(date, market_rule=self.cfg['market_rule'])
        return self._finish(date, cands, audit, self.mc, self.fc, self.cfg['combined_weight_market'])

    def market_only(self, date):
        rows = [r for r in self.market[date] if r['liquidity'] != 'ILLIQUID']
        order = cluster_order([(r['cluster'], r['features']) for r in rows], 'mom_126', 'mdd_126')
        allowed = allowed_clusters(order, self.cfg['market_rule'])
        cands, audit = [], []
        for r in self.market[date]:
            if r['liquidity'] == 'ILLIQUID':
                reason = 'MARKET_ILLIQUID'
            elif allowed is None:
                reason = 'CLUSTER_PROFILE_AMBIGUOUS'
            elif r['cluster'] not in allowed:
                reason = 'MARKET_NOT_IN_LEADING_CLUSTER'
            else:
                reason = ''
                cands.append(dict(ticker=r['ticker'], features=r['features'], financial_year=None))
            audit.append(_audit_row(date, r['ticker'], market_cluster=r['cluster'], market_eligible=not reason,
                                    in_candidate_universe=not reason, reason=reason))
        return self._finish(date, cands, audit, self.mc, {}, 1.0)

    def financial_only(self, date):
        # Financial Eligible Pool ∩ traded universe: every market cluster is allowed, ILLIQUID still excluded.
        cands, audit = self._universe(date, leading_market={r['cluster'] for r in self.market[date]})
        return self._finish(date, cands, audit, {}, self.fc, 0.0)

    def equal_weight(self, date):
        audit = [_audit_row(date, r['ticker'], market_cluster=r['cluster'],
                            in_candidate_universe=r['liquidity'] != 'ILLIQUID',
                            reason='MARKET_ILLIQUID' if r['liquidity'] == 'ILLIQUID' else '')
                 for r in self.market[date]]
        names = sorted(a['ticker'] for a in audit if a['in_candidate_universe'])
        if not names:
            return dict(target={}, candidates=0, picks=[], audit=audit, status='NO_CANDIDATES')
        return dict(target={t: 1 / len(names) for t in names}, candidates=len(names), picks=names, audit=audit,
                    status='OK')

    def momentum_only(self, date):
        audit, rows = [], []
        for r in self.market[date]:
            if r['liquidity'] == 'ILLIQUID':
                reason = 'MARKET_ILLIQUID'
            elif r['features'].get('mom_126') is None:
                reason = 'MOM_126_MISSING'
            else:
                reason = ''
                rows.append(r)
            audit.append(_audit_row(date, r['ticker'], market_cluster=r['cluster'], in_candidate_universe=not reason,
                                    reason=reason))
        rows.sort(key=lambda r: (-r['features']['mom_126'], r['ticker']))
        n = n_select(len(rows), self.share)
        if n == 0:
            return dict(target={}, candidates=0, picks=[], audit=audit, status='NO_CANDIDATES')
        picks = [r['ticker'] for r in rows[:n]]
        return dict(target={t: 1 / n for t in picks}, candidates=len(rows), picks=picks, audit=audit, status='OK')

    def _finish(self, date, cands, audit, market_crit, fin_crit, weight_market):
        """Score, drop FINANCIAL_CRITERIA_MISSING, then apply N_min and top-share on the same N (plan §3.5.3, §3.7)."""
        rows = self._rows(cands, bool(market_crit), bool(fin_crit))
        scores = combined_scores(rows, market_crit, fin_crit, weight_market=weight_market)
        by_ticker = {a['ticker']: a for a in audit}
        for t, s in scores.items():
            if s['missing']:
                by_ticker[t]['flags'] = ';'.join(f'FC_MISSING:{c}' if c in fin_crit else f'MC_MISSING:{c}'
                                                 for c in s['missing'])
        for c in cands:
            if c['ticker'] not in scores:  # every financial criterion missing
                by_ticker[c['ticker']].update(in_candidate_universe=False, reason='FINANCIAL_CRITERIA_MISSING')
        cands = [c for c in cands if c['ticker'] in scores]
        if len(cands) < self.n_min:
            return dict(target=None, keep_names={c['ticker'] for c in cands}, candidates=len(cands), picks=[],
                        audit=audit, status='UNIVERSE_TOO_SMALL')
        liquidity = {c['ticker']: c['features'].get('liquidity_21') for c in cands}
        picks = select_top({t: v['score'] for t, v in scores.items()}, liquidity, self.share)
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
