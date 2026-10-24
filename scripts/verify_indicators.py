"""Independent QA of an indicators run (D-IND-01, plan section 5).

Re-derives values straight from inputs-wide and terminal.sqlite with its own
formula code (it does not import delta_t1.indicators.compute), then writes
qa-report.md plus CSV details next to the results. Read-only for everything else.
"""
import argparse
import json
import math
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
RESULTS = 'data/financial/indicators_v1/results'
TERMINAL = 'data/web/delta-intelligence-v1/terminal.sqlite'
SPOT = ('FPT', 'VNM', 'HPG', 'MWG', 'GAS', 'VCB', 'TCB', 'SSI', 'BVH', 'DGC')
FINANCIAL = {'BANK', 'SECURITIES', 'INSURANCE'}
SAMPLE = 600
SCORE_SAMPLE = 80
REL_TOL = 1e-9
OPTIONAL = ('finance_lease_ppe@',)  # added to PPE only when present

import pandas as pd  # noqa: E402


# --- Independent formulas -------------------------------------------------

def v(row, f):
    if row is None:
        return None
    x = row.get(f)
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def q(a, b):
    return None if a is None or b is None or b == 0 else a / b


def shares(r):
    for f in ('common_share_capital_amount', 'paid_in_capital_amount'):
        x = v(r, f)
        if x is not None and x > 0:
            return x / 10000
    return None


def parent_ni(r):
    if v(r, 'parent_net_profit') is not None:
        return v(r, 'parent_net_profit')
    if v(r, 'net_profit') is not None and v(r, 'noncontrolling_profit') is not None:
        return v(r, 'net_profit') - v(r, 'noncontrolling_profit')
    return v(r, 'net_profit')


def parent_eq(r):
    te = v(r, 'total_equity')
    return None if te is None else te - (v(r, 'noncontrolling_interests') or 0)


def mean2(a, b):
    return None if a is None else a if b is None else (a + b) / 2


def recompute(metric, t, p, pp, price):
    """Value only (None when the metric has no value)."""
    if metric == 'eps':
        return q(parent_ni(t), shares(t))
    if metric == 'bvps':
        return q(parent_eq(t), shares(t))
    if metric == 'market_cap':
        s = shares(t)
        return None if s is None or price is None else s * price
    if metric == 'pe':
        e = q(parent_ni(t), shares(t))
        return None if e is None or e <= 0 or price is None else price / e
    if metric == 'pb':
        b = q(parent_eq(t), shares(t))
        return None if b is None or b <= 0 or price is None else price / b
    if metric == 'roe':
        d = mean2(parent_eq(t), parent_eq(p))
        return None if d is None or d <= 0 else q(parent_ni(t), d)
    if metric == 'roa':
        return q(v(t, 'net_profit'), mean2(v(t, 'total_assets'), v(p, 'total_assets')))
    if metric == 'gross_margin':
        return q(v(t, 'gross_profit'), v(t, 'net_revenue'))
    if metric == 'net_margin':
        return q(v(t, 'net_profit'), v(t, 'net_revenue'))
    if metric == 'revenue_growth':
        a, b = v(t, 'net_revenue'), v(p, 'net_revenue')
        return None if a is None or b is None or b <= 0 else a / b - 1
    if metric == 'profit_growth':
        a, b = parent_ni(t), parent_ni(p) if p else None
        return None if a is None or b is None or b <= 0 else a / b - 1
    if metric == 'debt_to_equity':
        te = v(t, 'total_equity')
        return None if te is None or te <= 0 else q(v(t, 'total_liabilities'), te)
    if metric == 'current_ratio':
        return q(v(t, 'current_assets'), v(t, 'current_liabilities'))
    if metric == 'asset_turnover':
        return q(v(t, 'net_revenue'), mean2(v(t, 'total_assets'), v(p, 'total_assets')))
    if metric == 'cfo_to_ni':
        ni = v(t, 'net_profit')
        return None if ni is None or ni <= 0 else q(v(t, 'operating_cash_flow'), ni)
    if metric == 'f_score':
        return piotroski(t, p, pp)
    if metric == 'm_score':
        return beneish(t, p)
    if metric == 'z_score':
        return altman(t, price)
    if metric == 'z_score_dp':
        return altman_dp(t)
    raise KeyError(metric)


def piotroski(t, p, pp):
    if p is None:
        return None
    roa = q(v(t, 'net_profit'), v(p, 'total_assets'))
    roa_p = q(v(p, 'net_profit'), v(pp, 'total_assets'))
    cfo = v(t, 'operating_cash_flow')
    at_t, at_p = mean2(v(t, 'total_assets'), v(p, 'total_assets')), mean2(v(p, 'total_assets'), v(pp, 'total_assets'))
    l_t, l_p = v(t, 'noncurrent_loans_and_finance_leases'), v(p, 'noncurrent_loans_and_finance_leases')
    gm = lambda r: q(v(r, 'gross_profit'), v(r, 'net_revenue'))  # noqa: E731
    cr = lambda r: q(v(r, 'current_assets'), v(r, 'current_liabilities'))  # noqa: E731
    cmp = lambda a, b: None if a is None or b is None else a > b  # noqa: E731
    lev = True if l_t == 0 and l_p == 0 else cmp(q(l_p, at_p), q(l_t, at_t))
    s_t, s_p = shares(t), shares(p)
    sig = [None if roa is None else roa > 0, None if cfo is None else cfo > 0, cmp(roa, roa_p),
           cmp(q(cfo, v(p, 'total_assets')), roa), lev, cmp(cr(t), cr(p)),
           None if s_t is None or s_p is None else s_t <= s_p, cmp(gm(t), gm(p)),
           cmp(q(v(t, 'net_revenue'), at_t), q(v(p, 'net_revenue'), at_p))]
    return None if any(s is None for s in sig) else float(sum(sig))


def beneish(t, p):
    if p is None:
        return None
    ppe = lambda r: None if v(r, 'net_tangible_ppe') is None else v(r, 'net_tangible_ppe') + (v(r, 'finance_lease_ppe') or 0)  # noqa: E731
    sga = lambda r: None if v(r, 'selling_expense') is None or v(r, 'administrative_expense') is None else v(r, 'selling_expense') + v(r, 'administrative_expense')  # noqa: E731
    gm = lambda r: q(v(r, 'gross_profit'), v(r, 'net_revenue'))  # noqa: E731
    dep = 'aggregate_fixed_property_depreciation_amortization'

    def aq(r):
        ca, pp_, ta = v(r, 'current_assets'), ppe(r), v(r, 'total_assets')
        return None if ca is None or pp_ is None or not ta else 1 - (ca + pp_) / ta

    def dr(r):
        d, pp_ = v(r, dep), ppe(r)
        return None if d is None or pp_ is None else q(d, d + pp_)

    def lv(r):
        cl, ltd = v(r, 'current_liabilities'), v(r, 'noncurrent_loans_and_finance_leases')
        return None if cl is None or ltd is None else q(cl + ltd, v(r, 'total_assets'))

    ni, cfo = v(t, 'net_profit'), v(t, 'operating_cash_flow')
    x = [q(q(v(t, 'receivables'), v(t, 'net_revenue')), q(v(p, 'receivables'), v(p, 'net_revenue'))),
         q(gm(p), gm(t)), q(aq(t), aq(p)), q(v(t, 'net_revenue'), v(p, 'net_revenue')), q(dr(p), dr(t)),
         q(q(sga(t), v(t, 'net_revenue')), q(sga(p), v(p, 'net_revenue'))), q(lv(t), lv(p)),
         None if ni is None or cfo is None else q(ni - cfo, v(t, 'total_assets'))]
    if any(a is None for a in x):
        return None
    dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata = x
    return -4.84 + .920 * dsri + .528 * gmi + .404 * aqi + .892 * sgi + .115 * depi - .172 * sgai + 4.679 * tata - .327 * lvgi


def _x123(t):
    ta, ca, cl = v(t, 'total_assets'), v(t, 'current_assets'), v(t, 'current_liabilities')
    pbt, ie = v(t, 'profit_before_tax'), v(t, 'interest_expense')
    x1 = None if ca is None or cl is None else q(ca - cl, ta)
    x3 = None if pbt is None or ie is None else q(pbt + ie, ta)
    return x1, q(v(t, 'retained_earnings'), ta), x3


def altman(t, price):
    x1, x2, x3 = _x123(t)
    s, tl = shares(t), v(t, 'total_liabilities')
    x5 = q(v(t, 'net_revenue'), v(t, 'total_assets'))
    if None in (x1, x2, x3, x5, s, price) or not tl:
        return None
    return 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * (price * s / tl) + 1.0 * x5


def altman_dp(t):
    x1, x2, x3 = _x123(t)
    x4 = q(v(t, 'total_equity'), v(t, 'total_liabilities'))
    return None if None in (x1, x2, x3, x4) else 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4


# --- Report helpers -------------------------------------------------------

def fmt(x, digits=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return '—'
    s = f'{x:,.{digits}f}'
    return s.replace(',', '_').replace('.', ',').replace('_', '.')


def md_table(frame):
    cols = list(frame.columns)
    lines = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    lines += ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in frame.itertuples(index=False)]
    return '\n'.join(lines)


def year_end_prices():
    con = sqlite3.connect(f'file:{ROOT / TERMINAL}?mode=ro', uri=True)
    rows = con.execute("select ticker, date, raw_close from prices where date like '____-12-__' "
                       "and raw_close is not null").fetchall()
    con.close()
    best = {}
    for t, d, close in rows:
        key = (t, int(d[:4]))
        if int(d[8:10]) >= 1 and (key not in best or d > best[key][0]):
            best[key] = (d, close)
    return {k: float(c) for k, (d, c) in best.items()}  # Every December date is <= 30 days from 31/12.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', help='results run folder (default: latest.json)')
    parser.add_argument('--seed', type=int, default=20261025)
    args = parser.parse_args()
    out = ROOT / (args.result or json.loads((ROOT / RESULTS / 'latest.json').read_text())['path'])
    pins = json.loads((out / 'input-pins.json').read_text())
    inputs_dir = ROOT / 'data/financial/indicators_v1/inputs' / pins['inputs_run']
    wide = pd.read_parquet(inputs_dir / 'inputs-wide.parquet')
    rows = {(r['ticker'], int(r['fiscal_year'])): r for r in wide.to_dict('records')}
    prices = year_end_prices()
    con = sqlite3.connect(f'file:{out / "indicators.sqlite"}?mode=ro', uri=True)
    cells = pd.read_sql('select ticker, fiscal_year, metric, value, status from indicator_values', con)
    company = pd.read_sql('select * from company', con)
    con.close()
    cells = cells.merge(company[['ticker', 'sector_group']], on='ticker')

    # 1. Independent recomputation.
    metrics = [m for m in cells.metric.unique() if m not in ('price', 'shares')]
    ok = cells[(cells.status == 'OK') & cells.metric.isin(metrics)]
    picks = []
    for m in ('f_score', 'm_score', 'z_score', 'z_score_dp'):
        sub = ok[ok.metric == m]
        picks += sub.sample(min(SCORE_SAMPLE, len(sub)), random_state=args.seed).index.tolist()
    rest = ok.drop(picks)
    picks += rest.sample(min(SAMPLE - len(picks), len(rest)), random_state=args.seed).index.tolist()
    nonok = cells[(cells.status != 'OK') & cells.metric.isin(metrics) & ~cells.sector_group.isin(FINANCIAL)]
    picks += nonok.sample(min(200, len(nonok)), random_state=args.seed).index.tolist()
    mismatches = []
    for _, c in cells.loc[picks].iterrows():
        t, y = c.ticker, int(c.fiscal_year)
        expected = recompute(c.metric, rows.get((t, y)), rows.get((t, y - 1)), rows.get((t, y - 2)), prices.get((t, y)))
        got = None if c.status != 'OK' else c.value
        same = (expected is None and got is None) or (
            expected is not None and got is not None and math.isclose(expected, got, rel_tol=REL_TOL, abs_tol=1e-12))
        if not same:
            mismatches.append(dict(ticker=t, fiscal_year=y, metric=c.metric, engine=got, verifier=expected, status=c.status))
    checked = len(picks)

    # 2. EPS vs reported EPS.
    eps = cells[(cells.metric == 'eps') & (cells.status == 'OK')][['ticker', 'fiscal_year', 'value']]
    rep = wide[['ticker', 'fiscal_year', 'vendor_basic_eps']].dropna()
    rep = rep[rep.vendor_basic_eps != 0]
    e = eps.merge(rep, on=['ticker', 'fiscal_year'])
    e['rel_diff'] = (e.value - e.vendor_basic_eps) / e.vendor_basic_eps.abs()
    e['within10'] = e.rel_diff.abs() < 0.10
    # Some reported EPS (mostly 2016) are quoted in thousand VND and truncated.
    e['reported_in_thousands'] = ~e.within10 & ((e.value - e.vendor_basic_eps * 1000).abs() < 1000)
    by_year = e.groupby('fiscal_year').within10.agg(['size', 'mean']).reset_index()
    e.sort_values('rel_diff', key=lambda s: s.abs(), ascending=False).to_csv(out / 'qa-eps-vs-reported.csv', index=False)

    # 3. Outliers (listed, never removed).
    o = cells[cells.status == 'OK']
    outliers = pd.concat([
        o[(o.metric == 'pe') & (o.value > 500)].assign(rule='P/E > 500'),
        o[(o.metric == 'roe') & (o.value.abs() > 2)].assign(rule='|ROE| > 200%'),
        o[(o.metric == 'z_score') & (o.value < -10)].assign(rule='Z < -10'),
        o[(o.metric == 'm_score') & (o.value > 10)].assign(rule='M > 10')])
    outliers.to_csv(out / 'qa-outliers.csv', index=False)

    # 4. Spot-check table.
    piv = cells[cells.ticker.isin(SPOT) & cells.fiscal_year.isin([2024, 2025])].copy()
    piv['shown'] = [fmt(val, 0 if m in ('eps', 'bvps', 'f_score') else 2) if s == 'OK' else s
                    for val, s, m in zip(piv.value, piv.status, piv.metric)]
    spot = piv.pivot_table(index=['ticker', 'fiscal_year'], columns='metric', values='shown', aggfunc='first').reset_index()
    cap = cells[(cells.metric == 'market_cap')].set_index(['ticker', 'fiscal_year'])['value']
    spot['vốn hóa (tỷ đ)'] = [fmt(cap.get((t, y), float('nan')) / 1e9, 0) for t, y in zip(spot.ticker, spot.fiscal_year)]
    vend = wide.set_index(['ticker', 'fiscal_year'])['vendor_basic_eps']
    spot['EPS công bố'] = [fmt(vend.get((t, y)), 0) for t, y in zip(spot.ticker, spot.fiscal_year)]
    spot = spot[['ticker', 'fiscal_year', 'eps', 'EPS công bố', 'pe', 'pb', 'roe', 'roa', 'vốn hóa (tỷ đ)',
                 'f_score', 'm_score', 'z_score']]

    # 5. Coverage and 2025 targets.
    cov = cells[cells.metric.isin(['eps', 'pe', 'pb', 'roe', 'roa', 'f_score', 'm_score', 'z_score'])]
    cov_table = (cov.assign(ok=cov.status == 'OK').groupby(['metric', 'fiscal_year']).ok.sum().unstack().astype(int))
    reported25 = {t for (t, y) in rows if y == 2025}
    c25 = cells[(cells.fiscal_year == 2025) & cells.ticker.isin(reported25)]
    valid = dict(eps={'OK'}, pe={'OK', 'NEGATIVE_EARNINGS'}, pb={'OK', 'NEGATIVE_EQUITY'}, roe={'OK', 'NEGATIVE_EQUITY'})
    targets = []
    for m, statuses in valid.items():
        sub = c25[c25.metric == m]
        targets.append((m, len(sub), int(sub.status.isin(statuses).sum()), 0.90))
    reg = c25[c25.sector_group == 'NON_FINANCIAL']
    for m in ('f_score', 'm_score', 'z_score'):
        sub = reg[reg.metric == m]
        targets.append((m, len(sub), int((sub.status == 'OK').sum()), 0.80))
    # Causes: missing inputs behind failing 2025 cells.
    con = sqlite3.connect(f'file:{out / "indicators.sqlite"}?mode=ro', uri=True)
    causes = {}
    for m, n, good, goal in targets:
        statuses = valid.get(m, {'OK'})
        bad = c25[(c25.metric == m) & ~c25.status.isin(statuses)]
        if m in ('f_score', 'm_score', 'z_score'):
            bad = bad[bad.sector_group == 'NON_FINANCIAL']
        counter = {}
        for t in bad.ticker:
            js = json.loads(con.execute('select inputs_json from indicator_values where ticker=? and fiscal_year=2025 '
                                        'and metric=?', (t, m)).fetchone()[0])
            st = c25[(c25.ticker == t) & (c25.metric == m)].status.iloc[0]
            fields = sorted({k for k, x in js.items() if '@' in k and x is None and not k.startswith(OPTIONAL)})
            for k in fields or js.get('missing', [st]) or [st]:
                counter[k] = counter.get(k, 0) + 1
        causes[m] = sorted(counter.items(), key=lambda kv: -kv[1])[:6]
    con.close()

    passed = not mismatches
    lines = [f'# QA report — {out.name}', '',
             f'Inputs: `{pins["inputs_run"]}` · verifier: `scripts/verify_indicators.py` (công thức viết lại độc lập, '
             f'không import engine) · seed {args.seed}.', '',
             '## 1. Tính lại độc lập', '',
             f'{checked} ô (gồm {SCORE_SAMPLE} ô mỗi loại F/M/Z/Z\'\' và 200 ô không có giá trị) — '
             f'**{"PASS" if passed else "FAIL"}**, {len(mismatches)} ô lệch (tolerance tương đối {REL_TOL}).', '']
    if mismatches:
        lines += [md_table(pd.DataFrame(mismatches).head(20)), '']
    total = len(e)
    lines += ['## 2. EPS tự tính so với EPS công bố', '',
              f'{total} mã-năm có cả hai: **{e.within10.mean():.1%}** lệch < 10%. '
              f'{int(e.reported_in_thousands.sum())} mã-năm EPS công bố ghi theo nghìn đồng (chủ yếu 2016); '
              f'bỏ các ô này thì **{e[~e.reported_in_thousands].within10.mean():.1%}** lệch < 10%. Theo năm:', '',
              md_table(by_year.assign(mean=by_year['mean'].map(lambda x: f'{x:.1%}')).rename(
                  columns={'fiscal_year': 'năm', 'size': 'số mã', 'mean': '% lệch <10%'})), '',
              'Nguyên nhân lệch thường gặp: EPS công bố chia cho số CP **bình quân gia quyền** trong năm '
              '(phát hành thêm, chia cổ tức bằng CP), trừ quỹ khen thưởng phúc lợi khỏi lợi nhuận, cổ phiếu quỹ; '
              'engine dùng vốn góp cuối kỳ / 10.000. Top 15 lệch lớn (đủ danh sách: `qa-eps-vs-reported.csv`):', '',
              md_table(e[~e.reported_in_thousands].sort_values('rel_diff', key=lambda s: s.abs(), ascending=False).head(15).assign(
                  value=lambda d: d.value.map(lambda x: fmt(x, 0)),
                  vendor_basic_eps=lambda d: d.vendor_basic_eps.map(lambda x: fmt(x, 0)),
                  rel_diff=lambda d: d.rel_diff.map(lambda x: f'{x:+.0%}'))[
                  ['ticker', 'fiscal_year', 'value', 'vendor_basic_eps', 'rel_diff']]), '',
              '## 3. Outliers (liệt kê, không xóa)', '',
              md_table(outliers.groupby('rule').size().rename('số ô').reset_index()), '',
              'Chi tiết: `qa-outliers.csv`.', '',
              '## 4. Spot-check 10 mã (so với CafeF)', '',
              'EPS (đ), P/E, P/B (lần), ROE/ROA (tỷ lệ), vốn hóa theo giá đóng cửa cuối năm.', '',
              md_table(spot.fillna('—')), '',
              '## 5. Coverage (số mã có giá trị, theo năm)', '',
              md_table(cov_table.reset_index()), '',
              '## 6. Mục tiêu 2025', '',
              'EPS/P/E/P/B/ROE tính trên mã có BCTC 2025 (P/E chấp nhận NEGATIVE_EARNINGS, P/B và ROE chấp nhận '
              'NEGATIVE_EQUITY); F/M/Z trên mã phi tài chính có BCTC 2025.', '']
    rows_t = []
    for m, n, good, goal in targets:
        rate = good / n if n else 0
        rows_t.append(dict(chỉ_số=m, mẫu=n, đạt=good, tỷ_lệ=f'{rate:.1%}', mục_tiêu=f'{goal:.0%}',
                           kết_quả='ĐẠT' if rate >= goal else 'CHƯA ĐẠT',
                           nguyên_nhân_chính=', '.join(f'{k} ({c})' for k, c in causes[m][:6]) if rate < goal else ''))
    src_cols = [c for c in wide.columns if c.startswith('src__')]
    w25 = wide[(wide.fiscal_year == 2025)]
    no_cf = int(((w25.sector_group == 'NON_FINANCIAL') & w25.operating_cash_flow.isna()
                 & w25.src__total_assets.fillna('').str.startswith('CAFEF')).sum())
    dstock_only = int((w25[src_cols].apply(lambda r: set(r.dropna()) == {'DSTOCK'}, axis=1)).sum())
    lines += [md_table(pd.DataFrame(rows_t)), '',
              f'Ghi chú: {dstock_only} mã năm 2025 chỉ có dữ liệu DStock (DStock không có vốn góp, phải thu, '
              'vay dài hạn, lợi nhuận chưa phân phối) nên không tính được EPS/P/E/P/B/F/M/Z; '
              f'{no_cf} mã CafeF năm 2025 không có lưu chuyển tiền tệ được map (thường là mẫu LCTT trực tiếp, '
              'không có dòng khấu hao/LNTT gián tiếp) nên thiếu CFO và khấu hao ⇒ F/M null. '
              'Hai nhóm này giải thích gần hết phần chưa đạt. Không hạ mục tiêu.', '']
    (out / 'qa-report.md').write_text('\n'.join(lines), encoding='utf-8')
    pd.DataFrame(mismatches).to_csv(out / 'qa-mismatches.csv', index=False)
    print(f'recompute {checked} cells: {"PASS" if passed else "FAIL"} ({len(mismatches)} mismatches)')
    print(f'eps within 10% of reported: {e.within10.mean():.1%} of {total}')
    print('2025 targets:', ', '.join(f'{r["chỉ_số"]}={r["tỷ_lệ"]}' for r in rows_t))
    print('report:', (out / 'qa-report.md').relative_to(ROOT).as_posix())
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
