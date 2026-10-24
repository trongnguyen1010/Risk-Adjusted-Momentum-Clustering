"""Annual product indicators (D-IND-01): pure functions over one ticker's inputs.

A row is a dict of standardized fields for one fiscal year (missing = None).
Every metric yields a cell with a value, a status and the inputs it used, so a
number can always be traced back. Missing inputs stay missing: no zero fill and
no forward fill; the prior year must be exactly fiscal_year - 1.
"""
import math

OK = 'OK'
MISSING_INPUT = 'MISSING_INPUT'
NOT_APPLICABLE = 'NOT_APPLICABLE'
NEGATIVE_EARNINGS = 'NEGATIVE_EARNINGS'
NEGATIVE_EQUITY = 'NEGATIVE_EQUITY'
NO_PRICE = 'NO_PRICE'

PAR_VALUE = 10_000  # VND per share
DISPLAY_METRICS = ('eps', 'bvps', 'market_cap', 'pe', 'pb', 'roe', 'roa', 'gross_margin', 'net_margin',
                   'revenue_growth', 'profit_growth', 'debt_to_equity', 'current_ratio', 'asset_turnover', 'cfo_to_ni')
SCORE_METRICS = ('f_score', 'm_score', 'z_score', 'z_score_dp')
AUX_METRICS = ('price', 'shares')
METRICS = AUX_METRICS + DISPLAY_METRICS + SCORE_METRICS
FINANCIAL_SECTORS = frozenset({'BANK', 'SECURITIES', 'INSURANCE'})
# Ratios that need an industrial statement layout; banks/brokers/insurers get NOT_APPLICABLE.
FINANCIAL_METRICS = frozenset({'price', 'shares', 'eps', 'bvps', 'market_cap', 'pe', 'pb', 'roe', 'roa',
                               'revenue_growth', 'profit_growth'})

M_COEFFICIENTS = dict(intercept=-4.84, DSRI=0.920, GMI=0.528, AQI=0.404, SGI=0.892, DEPI=0.115,
                      SGAI=-0.172, TATA=4.679, LVGI=-0.327)
Z_COEFFICIENTS = dict(X1=1.2, X2=1.4, X3=3.3, X4=0.6, X5=1.0)
ZDP_COEFFICIENTS = dict(X1=6.56, X2=3.26, X3=6.72, X4=1.05)


def num(value):
    if value is None or isinstance(value, bool):
        return None
    value = float(value)
    return None if math.isnan(value) or math.isinf(value) else value


def div(a, b):
    return None if a is None or b is None or b == 0 else a / b


def cell(value=None, status=OK, inputs=None, missing=(), flags=(), **extra):
    if status == OK and value is None:
        status = MISSING_INPUT
    body = dict(inputs or {})
    if missing:
        body['missing'] = sorted(set(missing))
    if flags:
        body['flags'] = sorted(set(flags))
    body.update(extra)
    return dict(value=value if status == OK else None, status=status, inputs=body)


class Year:
    """Field access plus derived base quantities for one fiscal year."""

    def __init__(self, row, price=None):
        self.row = row or {}
        self.exists = bool(row)
        self.price = num(price)
        self.flags = []
        self.used = {}

    def __call__(self, field):
        value = num(self.row.get(field))
        self.used[field] = value
        return value

    @property
    def shares(self):
        common = self('common_share_capital_amount')
        if common and common > 0:
            return common / PAR_VALUE
        paid = self('paid_in_capital_amount')
        if paid and paid > 0:
            self.flags.append('SHARES_FROM_PAID_IN_CAPITAL')
            return paid / PAR_VALUE
        return None

    @property
    def parent_ni(self):
        parent = self('parent_net_profit')
        if parent is not None:
            return parent
        ni, nci = self('net_profit'), self('noncontrolling_profit')
        if ni is not None and nci is not None:
            self.flags.append('PARENT_NI_FROM_NET_MINUS_NCI')
            return ni - nci
        if ni is not None:
            self.flags.append('PARENT_NI_FROM_NET_PROFIT')
        return ni

    @property
    def parent_equity(self):
        equity, nci = self('total_equity'), self('noncontrolling_interests')
        if equity is None:
            return None
        if nci is None:
            self.flags.append('NCI_ASSUMED_ZERO')
            return equity
        return equity - nci

    @property
    def ebit(self):
        pbt, interest = self('profit_before_tax'), self('interest_expense')
        return None if pbt is None or interest is None else pbt + interest

    @property
    def ppe(self):
        tangible = self('net_tangible_ppe')
        if tangible is None:
            return None
        lease = self('finance_lease_ppe')
        return tangible + (lease or 0)

    @property
    def sga(self):
        selling, admin = self('selling_expense'), self('administrative_expense')
        return None if selling is None or admin is None else selling + admin

    @property
    def gross_margin(self):
        return div(self('gross_profit'), self('net_revenue'))

    @property
    def current_ratio(self):
        return div(self('current_assets'), self('current_liabilities'))


def avg(current, prior, name, flags):
    """(X_t + X_p) / 2; a missing prior year falls back to X_t and is flagged."""
    if current is None:
        return None
    if prior is None:
        flags.append('AVG_CURRENT_ONLY:' + name)
        return current
    return (current + prior) / 2


def _inputs(*years):
    out = {}
    for tag, year in years:
        for field, value in year.used.items():
            out[f'{field}@{tag}'] = value
    return out


def _missing(*years):
    return [f'{field}@{tag}' for tag, year in years for field, value in year.used.items() if value is None]


def ratio_cell(numerator, denominator, years, flags=(), nonpositive_denominator=None, nonpositive_status=None):
    if nonpositive_status and denominator is not None and denominator <= 0:
        return cell(status=nonpositive_status, inputs=_inputs(*years), flags=flags)
    value = div(numerator, denominator)
    if value is None:
        return cell(status=MISSING_INPUT, inputs=_inputs(*years), missing=_missing(*years) or ['ZERO_DENOMINATOR'],
                    flags=flags)
    return cell(value, inputs=_inputs(*years), flags=flags)


def display_metrics(t, p):
    """The 15 display indicators plus price/shares for year t (p = prior year)."""
    out = {}
    T, P = ('t', t), ('p', p)

    def fresh(*years):
        for y in years:
            y.used, y.flags = {}, []
        return [f for y in years for f in y.flags]

    fresh(t)
    shares = t.shares
    out['shares'] = cell(shares, inputs=_inputs(T), missing=_missing(T), flags=t.flags)
    out['price'] = cell(t.price, inputs={'raw_close_fy': t.price}) if t.price is not None else cell(status=NO_PRICE)

    fresh(t)
    shares, ni = t.shares, t.parent_ni
    eps = div(ni, shares)
    out['eps'] = cell(eps, inputs=_inputs(T), missing=_missing(T), flags=t.flags)

    fresh(t)
    shares, equity = t.shares, t.parent_equity
    bvps = div(equity, shares)
    out['bvps'] = cell(bvps, inputs=_inputs(T), missing=_missing(T), flags=t.flags)

    fresh(t)
    shares = t.shares
    if shares is None:
        out['market_cap'] = cell(status=MISSING_INPUT, inputs=_inputs(T), missing=_missing(T))
    elif t.price is None:
        out['market_cap'] = cell(status=NO_PRICE, inputs=_inputs(T))
    else:
        out['market_cap'] = cell(t.price * shares, inputs={**_inputs(T), 'raw_close_fy': t.price}, flags=t.flags)

    for metric, base, negative in (('pe', eps, NEGATIVE_EARNINGS), ('pb', bvps, NEGATIVE_EQUITY)):
        source = out['eps' if metric == 'pe' else 'bvps']
        if base is None:
            out[metric] = cell(status=MISSING_INPUT, inputs=source['inputs'], missing=source['inputs'].get('missing', [metric]))
        elif base <= 0:
            out[metric] = cell(status=negative, inputs={**source['inputs'], 'base': base})
        elif t.price is None:
            out[metric] = cell(status=NO_PRICE, inputs={**source['inputs'], 'base': base})
        else:
            out[metric] = cell(t.price / base, inputs={**source['inputs'], 'base': base, 'raw_close_fy': t.price})

    flags = fresh(t, p)
    ni, eq_t, eq_p = t.parent_ni, t.parent_equity, p.parent_equity
    flags = t.flags + ['p:' + f for f in p.flags]
    out['roe'] = ratio_cell(ni, avg(eq_t, eq_p, 'parent_equity', flags), [T, P], flags, nonpositive_status=NEGATIVE_EQUITY)

    fresh(t, p)
    flags = []
    out['roa'] = ratio_cell(t('net_profit'), avg(t('total_assets'), p('total_assets'), 'total_assets', flags), [T, P], flags)

    fresh(t)
    out['gross_margin'] = ratio_cell(t('gross_profit'), t('net_revenue'), [T])
    fresh(t)
    out['net_margin'] = ratio_cell(t('net_profit'), t('net_revenue'), [T])

    fresh(t, p)
    rev_t, rev_p = t('net_revenue'), p('net_revenue')
    if rev_p is not None and rev_p <= 0:
        out['revenue_growth'] = cell(status=MISSING_INPUT, inputs=_inputs(T, P), missing=['net_revenue@p<=0'])
    else:
        growth = div(rev_t, rev_p)
        out['revenue_growth'] = (cell(status=MISSING_INPUT, inputs=_inputs(T, P), missing=_missing(T, P)) if growth is None
                                 else cell(growth - 1, inputs=_inputs(T, P)))

    fresh(t, p)
    ni_t, ni_p = t.parent_ni, p.parent_ni
    flags = t.flags + ['p:' + f for f in p.flags]
    if ni_t is None or ni_p is None:
        out['profit_growth'] = cell(status=MISSING_INPUT, inputs=_inputs(T, P), missing=_missing(T, P), flags=flags)
    elif ni_p <= 0:
        out['profit_growth'] = cell(status=NEGATIVE_EARNINGS, inputs=_inputs(T, P), flags=flags)
    else:
        out['profit_growth'] = cell(ni_t / ni_p - 1, inputs=_inputs(T, P), flags=flags)

    fresh(t)
    out['debt_to_equity'] = ratio_cell(t('total_liabilities'), t('total_equity'), [T], nonpositive_status=NEGATIVE_EQUITY)
    fresh(t)
    out['current_ratio'] = ratio_cell(t('current_assets'), t('current_liabilities'), [T])
    fresh(t, p)
    flags = []
    out['asset_turnover'] = ratio_cell(t('net_revenue'), avg(t('total_assets'), p('total_assets'), 'total_assets', flags),
                                       [T, P], flags)
    fresh(t)
    out['cfo_to_ni'] = ratio_cell(t('operating_cash_flow'), t('net_profit'), [T], nonpositive_status=NEGATIVE_EARNINGS)
    return out


F_SIGNALS = ('roa_positive', 'cfo_positive', 'roa_improving', 'accruals', 'leverage_falling',
             'liquidity_improving', 'no_dilution', 'gross_margin_improving', 'turnover_improving')


def _gt(a, b):
    return None if a is None or b is None else a > b


def f_score(t, p, pp):
    """Piotroski (0-9). ROA = net_profit / prior-year total assets. Partial signals are kept, score is not."""
    for y in (t, p, pp):
        y.used, y.flags = {}, []
    flags = []
    ta_p, ta_pp, ta_t = p('total_assets'), pp('total_assets'), t('total_assets')
    roa_t, roa_p = div(t('net_profit'), ta_p), div(p('net_profit'), ta_pp)
    cfo = t('operating_cash_flow')
    ltd_t, ltd_p = t('noncurrent_loans_and_finance_leases'), p('noncurrent_loans_and_finance_leases')
    avg_t = avg(ta_t, ta_p, 'total_assets@t', flags)
    avg_p = avg(ta_p, ta_pp, 'total_assets@p', flags)
    if ltd_t == 0 and ltd_p == 0:
        leverage = True
    else:
        lev_t, lev_p = div(ltd_t, avg_t), div(ltd_p, avg_p)
        leverage = None if lev_t is None or lev_p is None else lev_t < lev_p
    shares_t, shares_p = t.shares, p.shares
    signals = dict(
        roa_positive=None if roa_t is None else roa_t > 0,
        cfo_positive=None if cfo is None else cfo > 0,
        roa_improving=_gt(roa_t, roa_p),
        accruals=_gt(div(cfo, ta_p), roa_t),
        leverage_falling=leverage,
        liquidity_improving=_gt(t.current_ratio, p.current_ratio),
        no_dilution=None if shares_t is None or shares_p is None else shares_t <= shares_p,
        gross_margin_improving=_gt(t.gross_margin, p.gross_margin),
        turnover_improving=_gt(div(t('net_revenue'), avg_t), div(p('net_revenue'), avg_p)))
    known = [v for v in signals.values() if v is not None]
    years = [('t', t), ('p', p), ('pp', pp)]
    body = dict(signals=signals, known_signals=len(known), **_inputs(*years))
    if len(known) < len(F_SIGNALS):
        missing = [name for name, v in signals.items() if v is None]
        return cell(status=MISSING_INPUT, inputs=body, missing=missing, flags=flags + t.flags + p.flags)
    return cell(float(sum(known)), inputs=body, flags=flags + t.flags + p.flags)


def m_score(t, p):
    """Beneish 8-variable model; any zero denominator or missing input makes it null."""
    for y in (t, p):
        y.used, y.flags = {}, []
    sales_t, sales_p = t('net_revenue'), p('net_revenue')
    ta_t, ta_p = t('total_assets'), p('total_assets')
    ppe_t, ppe_p = t.ppe, p.ppe
    dep_t, dep_p = t('aggregate_fixed_property_depreciation_amortization'), p('aggregate_fixed_property_depreciation_amortization')

    def quality(y, ta, ppe):
        ca = y('current_assets')
        return None if ca is None or ppe is None or ta in (None, 0) else 1 - (ca + ppe) / ta

    def dep_rate(dep, ppe):
        return None if dep is None or ppe is None else div(dep, dep + ppe)

    def lev(y, ta):
        cl, ltd = y('current_liabilities'), y('noncurrent_loans_and_finance_leases')
        return None if cl is None or ltd is None else div(cl + ltd, ta)

    def sga_rate(y, sales):
        return div(y.sga, sales)

    ni, cfo = t('net_profit'), t('operating_cash_flow')
    v = dict(
        DSRI=div(div(t('receivables'), sales_t), div(p('receivables'), sales_p)),
        GMI=div(p.gross_margin, t.gross_margin),
        AQI=div(quality(t, ta_t, ppe_t), quality(p, ta_p, ppe_p)),
        SGI=div(sales_t, sales_p),
        DEPI=div(dep_rate(dep_p, ppe_p), dep_rate(dep_t, ppe_t)),
        SGAI=div(sga_rate(t, sales_t), sga_rate(p, sales_p)),
        LVGI=div(lev(t, ta_t), lev(p, ta_p)),
        TATA=None if ni is None or cfo is None else div(ni - cfo, ta_t))
    body = dict(variables=v, **_inputs(('t', t), ('p', p)))
    missing = [k for k, x in v.items() if x is None]
    if missing:
        return cell(status=MISSING_INPUT, inputs=body, missing=missing)
    score = M_COEFFICIENTS['intercept'] + sum(M_COEFFICIENTS[k] * x for k, x in v.items())
    return cell(score, inputs=body)


def z_components(t):
    t.used, t.flags = {}, []
    ta, tl = t('total_assets'), t('total_liabilities')
    ca, cl = t('current_assets'), t('current_liabilities')
    return dict(
        X1=None if ca is None or cl is None else div(ca - cl, ta),
        X2=div(t('retained_earnings'), ta),
        X3=div(t.ebit, ta),
        X5=div(t('net_revenue'), ta),
        equity_to_liabilities=div(t('total_equity'), tl)), tl


def z_scores(t, market_cap_cell):
    """Altman Z (needs price) and Z'' (book equity, no price) as separate metrics."""
    market_cap = market_cap_cell['value']
    x, tl = z_components(t)
    used = _inputs(('t', t))
    base = {k: x[k] for k in ('X1', 'X2', 'X3')}
    missing = [k for k, val in base.items() if val is None]
    if x['equity_to_liabilities'] is None:
        dp = cell(status=MISSING_INPUT, inputs=dict(variables=x, **used), missing=missing + ['equity_to_liabilities'])
    elif missing:
        dp = cell(status=MISSING_INPUT, inputs=dict(variables=x, **used), missing=missing)
    else:
        z = sum(ZDP_COEFFICIENTS[k] * base[k] for k in base) + ZDP_COEFFICIENTS['X4'] * x['equity_to_liabilities']
        dp = cell(z, inputs=dict(variables=x, **used), variant='Z_DOUBLE_PRIME')
    variables = dict(base, X5=x['X5'])
    missing = [k for k, val in variables.items() if val is None]
    if missing or not tl:
        z = cell(status=MISSING_INPUT, inputs=dict(variables=variables, **used), missing=missing or ['total_liabilities@t'])
    elif market_cap is None:
        status = NO_PRICE if market_cap_cell['status'] == NO_PRICE else MISSING_INPUT
        z = cell(status=status, inputs=dict(variables=variables, **used), missing=[] if status == NO_PRICE else ['market_cap'])
    else:
        variables['X4'] = market_cap / tl
        z = cell(sum(Z_COEFFICIENTS[k] * variables[k] for k in Z_COEFFICIENTS),
                 inputs=dict(variables=variables, market_cap=market_cap, **used), variant='ALTMAN_1968')
    return z, dp


def compute_year(rows, prices, year, sector):
    """All metric cells for one ticker-year. rows: {year: row}, prices: {year: raw_close_fy}."""
    if not rows.get(year):
        return {m: cell(status=NOT_APPLICABLE if sector in FINANCIAL_SECTORS and m not in FINANCIAL_METRICS
                        else MISSING_INPUT, missing=['NO_ANNUAL_REPORT']) for m in METRICS}
    t, p, pp = Year(rows[year], prices.get(year)), Year(rows.get(year - 1)), Year(rows.get(year - 2))
    out = display_metrics(t, p)
    if sector in FINANCIAL_SECTORS:
        for m in METRICS:
            if m not in FINANCIAL_METRICS:
                out[m] = cell(status=NOT_APPLICABLE, sector=sector)
        return out
    out['f_score'] = f_score(t, p, pp)
    out['m_score'] = m_score(t, p)
    out['z_score'], out['z_score_dp'] = z_scores(t, out['market_cap'])
    return out


def compute_ticker(rows, prices, sector, years=range(2016, 2026)):
    return {y: compute_year(rows, prices, y, sector) for y in years}


def f_rating(score):
    return None if score is None else 'STRONG' if score >= 7 else 'AVERAGE' if score >= 4 else 'WEAK'


def z_zone(score):
    return None if score is None else 'DISTRESS' if score < 1.81 else 'GREY' if score <= 2.99 else 'SAFE'


def m_flag(score):
    return None if score is None else 'LIKELY_MANIPULATOR' if score > -1.78 else 'NORMAL'
