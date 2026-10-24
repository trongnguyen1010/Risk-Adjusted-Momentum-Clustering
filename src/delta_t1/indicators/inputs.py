"""Standardized annual input table for product indicators (D-IND-01).

Sources, in priority order for one (ticker, fiscal_year, field) cell:
1. CafeF annual statements, consolidated provider types before separate ones.
2. DStock annual statements (Regular template only, field accepted by overlap QA).

Missing stays missing: no zero fill, no forward fill between years.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import pandas as pd

from ..experiments.financial_template_candidates import parse_candidates
from ..ingestion.dstock_financial import SCHEMA as DSTOCK_SCHEMA

YEARS = range(2015, 2026)  # 2015 only serves as the prior year of 2016.
FIELDS = (
    'administrative_expense', 'aggregate_fixed_property_depreciation_amortization', 'associate_profit',
    'cash_equity_proceeds_group', 'cash_nci_contributions', 'cashflow_interest_adjustment',
    'cashflow_profit_before_tax', 'common_share_capital_amount', 'cost_of_goods_sold', 'current_assets',
    'current_liabilities', 'current_tax_expense', 'deferred_tax_expense', 'finance_expense', 'finance_income',
    'finance_lease_ppe', 'gross_profit', 'gross_revenue', 'intangible_assets', 'interest_expense', 'net_profit',
    'net_revenue', 'net_tangible_ppe', 'noncontrolling_interests', 'noncontrolling_profit', 'noncurrent_assets',
    'noncurrent_liabilities', 'noncurrent_loans_and_finance_leases', 'operating_cash_flow', 'other_expense',
    'other_income', 'other_profit', 'other_short_term_payables', 'owned_tangible_ppe_accumulated_depreciation',
    'owned_tangible_ppe_cost', 'paid_in_capital_amount', 'parent_net_profit', 'profit_before_tax', 'receivables',
    'reported_operating_profit', 'retained_earnings', 'revenue_deductions', 'selling_expense',
    'short_term_loans_and_finance_leases', 'total_assets', 'total_capital', 'total_equity', 'total_liabilities',
    'vendor_basic_eps', 'vendor_diluted_eps')
# Expense lines are stored as positive magnitudes; providers mix sign conventions.
COST_FIELDS = ('cost_of_goods_sold', 'interest_expense', 'selling_expense', 'administrative_expense', 'finance_expense')
# CafeF returns exactly -1 for lines absent from a period (e.g. whole cash-flow
# blocks); a real -1 VND line is not plausible, so it is treated as missing.
CAFEF_ABSENT = -1.0
# Consolidated first (H*), then separate/parent-only types; audited before unaudited.
PROVIDER_PRIORITY = ('HK', 'H', 'HTK', 'K', 'MK', 'M', 'N', 'S')
DSTOCK_QA_FIELDS = ('total_assets', 'net_revenue', 'total_equity', 'net_profit')
DSTOCK_TOLERANCE = 0.005
DSTOCK_MIN_PASS = 0.95
INSURANCE = frozenset({'ABI', 'AIC', 'BHI', 'BIC', 'BLI', 'BMI', 'BVH', 'MIG', 'PGI', 'PRE', 'PTI', 'PVI', 'VNR'})


def nlabel(text):
    text = unicodedata.normalize('NFD', (text or '').casefold()).replace('đ', 'd')
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^0-9a-z]+', '', text)


# Bank / securities / insurance templates are not mapped by the Regular
# field-input job. Exact (statement, label) pins; unmatched labels are ignored.
_FINANCIAL_LABELS = [
    # Bank (TT49 template). 'VIII VỐN CHỦ SỞ HỮU' excludes minority interest (line 700).
    ('CDKT', 'TỔNG TÀI SẢN', 'total_assets'),
    ('CDKT', 'TỔNG NỢ PHẢI TRẢ', 'total_liabilities'),
    ('CDKT', 'VIII VỐN CHỦ SỞ HỮU', '_equity_ex_nci'),
    ('CDKT', 'IX.Lợi ích của cổ đông thiểu số', 'noncontrolling_interests'),
    ('CDKT', 'TỔNG NỢ PHẢI TRẢ VÀ VỐN CHỦ SỞ HỮU', 'total_capital'),
    ('CDKT', 'a. Vốn điều lệ', 'paid_in_capital_amount'),
    ('CDKT', '5. Lợi nhuận chưa phân phối', 'retained_earnings'),
    ('KQKD', 'XI. Tổng lợi nhuận trước thuế', 'profit_before_tax'),
    ('KQKD', 'XIII. Lợi nhuận sau thuế', 'net_profit'),
    ('KQKD', 'XIV. Lợi ích của cổ đông thiểu số', 'noncontrolling_profit'),
    ('KQKD', 'XV. Lợi nhuận sau thuế của cổ đông của Ngân hàng mẹ', 'parent_net_profit'),
    ('KQKD', 'Lãi cơ bản trên cổ phiếu (Đồng/1 cổ phiếu)', 'vendor_basic_eps'),
    ('KQKD', 'Tổng thu nhập hoạt động', 'net_revenue'),
    ('LCTT', 'I. Lưu chuyền tiền thuần từ hoạt động kinh doanh', 'operating_cash_flow'),
    # Securities (TT334 template).
    ('CDKT', 'TỔNG CỘNG TÀI SẢN', 'total_assets'),
    ('CDKT', 'C. NỢ PHẢI TRẢ', 'total_liabilities'),
    ('CDKT', 'D. VỐN CHỦ SỞ HỮU', 'total_equity'),
    ('CDKT', '8. Lợi ích của cổ đông không nắm quyền kiểm soát', 'noncontrolling_interests'),
    ('CDKT', 'TỔNG CỘNG NỢ PHẢI TRẢ VÀ VỐN CHỦ SỜ HỮU', 'total_capital'),
    ('CDKT', 'a. Cổ phiếu phổ thông có quyền biểu quyết', 'common_share_capital_amount'),
    ('CDKT', '1.1 Vốn góp của chủ sở hữu', 'paid_in_capital_amount'),
    ('CDKT', '7. Lợi nhuận chưa phân phối', 'retained_earnings'),
    ('CDKT', 'A. TÀI SẢN NGẮN HẠN', 'current_assets'),
    ('CDKT', 'I. Nợ phải trả ngắn hạn', 'current_liabilities'),
    ('KQKD', 'Cộng doanh thu hoạt động', 'net_revenue'),
    ('KQKD', 'IX. TỔNG LỢI NHUẬN KẾ TOÁN TRƯỚC THUẾ', 'profit_before_tax'),
    ('KQKD', 'XI. LỢI NHUẬN KẾ TOÁN SAU THUẾ TNDN', 'net_profit'),
    ('KQKD', '11.1. Lợi nhuận sau thuế phân bổ cho chủ sở hữu', 'parent_net_profit'),
    ('KQKD', '11.2. Lợi nhuận sau thuế trích các Quỹ', '_profit_to_funds'),
    ('KQKD', '11.3. Lợi nhuận thuần phân bổ cho lợi ích cổ đông không kiểm soát', 'noncontrolling_profit'),
    ('KQKD', '13.1.Lãi cơ bản trên cổ phiếu (Đồng/1 cổ phiếu)', 'vendor_basic_eps'),
    # Insurance (TT232 template).
    ('CDKT', 'D VỐN CHỦ SỞ HỮU', 'total_equity'),
    ('CDKT', '13. Lợi ích cổ đông không kiểm soát', 'noncontrolling_interests'),
    ('CDKT', 'TỔNG CỘNG NGUỒN VỐN', 'total_capital'),
    ('CDKT', '- Cổ phiếu phổ thông có quyền biểu quyết', 'common_share_capital_amount'),
    ('CDKT', '1. Vốn góp của chủ sở hữu', 'paid_in_capital_amount'),
    ('CDKT', '11. Lợi nhuận sau thuế chưa phân phối', 'retained_earnings'),
    ('CDKT', 'I. Nợ ngắn hạn', 'current_liabilities'),
    ('KQKD', '5. Doanh thu thuần từ HĐKD BH', 'net_revenue'),
    ('KQKD', '25. Tổng lợi nhuận kế toán trước thuế', 'profit_before_tax'),
    ('KQKD', '28. Lợi nhuận sau thuế thu nhập doanh nghiệp', 'net_profit'),
    ('KQKD', '29. Lợi nhuận sau thuế của cổ đông Công ty mẹ', 'parent_net_profit'),
    ('KQKD', '30. Lợi nhuận sau thuế của cố đông không kiểm soát', 'noncontrolling_profit'),
    ('KQKD', '31. Lãi cơ bản trên cổ phiếu (Đồng/1 cổ phiếu)', 'vendor_basic_eps'),
]
FINANCIAL_LABELS = {(s, nlabel(label)): field for s, label, field in _FINANCIAL_LABELS}


def sector_group(ticker, family):
    if family == 'Bank':
        return 'BANK'
    if family == 'Securities':
        return 'SECURITIES'
    if ticker in INSURANCE:
        return 'INSURANCE'
    return 'NON_FINANCIAL' if family == 'Regular' else 'OTHER'


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Pins:
    """Records the sha256 of every file read so the run can be replayed."""

    def __init__(self, root):
        self.root = Path(root)
        self.files = {}

    def read(self, relative):
        body = (self.root / relative).read_bytes()
        self.files[Path(relative).as_posix()] = hashlib.sha256(body).hexdigest()
        return body


def load_families(pins, readiness_csv):
    import io
    frame = pd.read_csv(io.BytesIO(pins.read(readiness_csv)), usecols=['symbol', 'registry_id', 'diagnostic_template_family'])
    return frame.rename(columns={'symbol': 'ticker', 'diagnostic_template_family': 'template_family'})


def _pick_provider(frame):
    """One value per (ticker, year, field): earliest provider type in PROVIDER_PRIORITY."""
    rank = {p: i for i, p in enumerate(PROVIDER_PRIORITY)}
    frame = frame.assign(_rank=frame['provider_type'].map(rank).fillna(len(rank)))
    frame = frame.sort_values(['ticker', 'fiscal_year', 'field', '_rank'])
    return frame.drop_duplicates(['ticker', 'fiscal_year', 'field'], keep='first').drop(columns='_rank')


# The current CafeF KQKD template inserted line 21 (investment-property gains)
# and moved line 27 (associates), but annual values keep the old row order:
# code 21 carries finance income, 22 finance expense, 23 interest, 24 associates.
# The 1.522 review job mapped by code, so its four fields are one row off.
# Verified with the operating-profit identity on raw payloads (~90% of
# sampled periods) and against DStock interest/finance expense.
FINANCE_BLOCK_SHIFT = {'finance_income': 'finance_expense', 'finance_expense': 'interest_expense',
                       'interest_expense': 'associate_profit'}


def realign_finance_block(frame):
    """Relabel the shifted block; true finance income (raw code 21) is not mapped, so it stays missing."""
    frame = frame[~frame['field'].isin(['associate_profit'])].copy()
    shifted = frame['field'].isin(FINANCE_BLOCK_SHIFT)
    frame.loc[shifted, 'field'] = frame.loc[shifted, 'field'].map(FINANCE_BLOCK_SHIFT)
    return frame


def load_cafef_regular(pins, job, families):
    """Regular-template field inputs already mapped by the 1.522 review job."""
    import io
    parts, stats = [], Counter()
    for rid in families.loc[families.template_family == 'Regular', 'registry_id']:
        rel = f'{job}/symbols/{rid}/field-inputs.csv'
        if not (pins.root / rel).exists():
            stats['missing_file'] += 1
            continue
        body = pins.read(rel)
        if len(body) < 200:
            stats['empty_file'] += 1
            continue
        parts.append(pd.read_csv(io.BytesIO(body), usecols=['field', 'provider_type', 'symbol', 'value', 'year'],
                                 dtype={'value': str}))
    frame = pd.concat(parts, ignore_index=True).rename(columns={'symbol': 'ticker', 'year': 'fiscal_year'})
    frame['value'] = pd.to_numeric(frame['value'], errors='coerce')
    stats['cells'] = len(frame)
    stats['absent_sentinel'] = int((frame['value'] == CAFEF_ABSENT).sum())
    frame = frame[frame['value'].notna() & (frame['value'] != CAFEF_ABSENT) & frame['fiscal_year'].isin(YEARS)]
    # A zero balance-sheet total is a placeholder, not a fact.
    zero = frame['field'].isin(('total_assets', 'total_capital', 'total_equity')) & (frame['value'] == 0)
    stats['zero_placeholder'] = int(zero.sum())
    frame = _pick_provider(frame[~zero])
    frame = realign_finance_block(frame)
    frame['source'] = 'CAFEF:' + frame['provider_type'].astype(str)
    return frame[['ticker', 'fiscal_year', 'field', 'value', 'source']], dict(stats)


def load_cafef_financial(pins, job, families):
    """Bank/securities/insurance values parsed from pinned raw CafeF annual payloads."""
    rows, stats = [], Counter()
    targets = families[families.template_family != 'Regular']
    for ticker, rid in targets[['ticker', 'registry_id']].itertuples(index=False):
        sources = json.loads(pins.read(f'{job}/symbols/{rid}/input-pins.json'))['sources']
        buckets = defaultdict(set)
        for path, sha in sources.items():
            if '/receipts/' not in path:
                continue
            receipt = json.loads(pins.read(path))
            task = receipt['task']
            if task['kind'] != 'REPORT' or task['mode'] != 'NAM' or not receipt.get('record'):
                continue
            record = receipt['record']
            body = pins.read(record['path'])
            for cell in parse_candidates(body, task, record['path'], record['sha256']):
                if cell['quarter'] != 0 or cell['year'] not in YEARS or cell['value_status'] != 'NUMERIC_CANDIDATE':
                    continue
                if cell['mapping_status'] != 'UNIQUE_CODE_LABEL_CANDIDATE':
                    continue
                field = FINANCIAL_LABELS.get((cell['statement'], nlabel(cell['label'])))
                if not field:
                    continue
                value = float(cell['value'])
                if value == CAFEF_ABSENT:
                    stats['absent_sentinel'] += 1
                    continue
                buckets[cell['year'], cell['provider_type'], field].add(value)
        for (year, ptype, field), values in buckets.items():
            if len(values) != 1:
                stats['conflicting_cells'] += 1
                continue
            rows.append(dict(ticker=ticker, fiscal_year=year, field=field, value=values.pop(), provider_type=ptype))
        stats['tickers_with_rows'] += any(True for _ in buckets)
    frame, gate_stats = gate_financial(pd.DataFrame(rows))
    stats.update(gate_stats)
    frame = _pick_provider(frame)
    # Bank equity line excludes minority interest; product total_equity includes it.
    wide = frame.pivot_table(index=['ticker', 'fiscal_year'], columns='field', values='value', aggfunc='first')
    if '_equity_ex_nci' in wide:
        ex = wide['_equity_ex_nci'].dropna()
        nci = wide.get('noncontrolling_interests', pd.Series(dtype=float)).reindex(ex.index)
        derived = (ex + nci.fillna(0)).rename('value').reset_index()
        derived['field'] = 'total_equity'
        ptypes = frame[frame.field == '_equity_ex_nci'].set_index(['ticker', 'fiscal_year'])['provider_type']
        derived['provider_type'] = derived.set_index(['ticker', 'fiscal_year']).index.map(ptypes)
        frame = pd.concat([frame[frame.field != '_equity_ex_nci'], derived], ignore_index=True)
        stats['bank_equity_without_nci_line'] = int(nci.isna().sum())
    frame['source'] = 'CAFEF_RAW:' + frame['provider_type'].astype(str)
    stats['cells'] = len(frame)
    return frame[['ticker', 'fiscal_year', 'field', 'value', 'source']], dict(stats)


ZERO_IS_MISSING = ('total_assets', 'total_liabilities', 'total_equity', '_equity_ex_nci', 'total_capital',
                   'paid_in_capital_amount', 'common_share_capital_amount', 'net_revenue')


def gate_financial(frame):
    """Statement-level plausibility for raw bank/securities/insurance cells.

    The raw payloads contain placeholder zeros and periods whose lines do not
    add up; such cells are dropped (never repaired) so another provider type or
    nothing at all is used instead.
    """
    stats = Counter()
    key = ['ticker', 'fiscal_year', 'provider_type']
    w = frame.pivot_table(index=key, columns='field', values='value', aggfunc='first')
    for f in ZERO_IS_MISSING:
        if f in w:
            stats['zero_placeholder'] += int((w[f] == 0).sum())
            w.loc[w[f] == 0, f] = float('nan')
    col = lambda f: w[f] if f in w else pd.Series(float('nan'), index=w.index)  # noqa: E731
    equity = col('total_equity').fillna(col('_equity_ex_nci') + col('noncontrolling_interests').fillna(0))
    gap = (col('total_assets') - col('total_liabilities') - equity).abs() / col('total_assets').abs()
    bad = gap > 0.01
    stats['balance_identity_dropped'] = int(bad.sum())
    for f in ('total_assets', 'total_liabilities', 'total_equity', '_equity_ex_nci', 'noncontrolling_interests', 'total_capital'):
        if f in w:
            w.loc[bad, f] = float('nan')
    ni, parent, nci = col('net_profit'), col('parent_net_profit'), col('noncontrolling_profit')
    # Securities firms also allocate part of after-tax profit to funds (line 11.2).
    funds = col('_profit_to_funds').fillna(0)
    split = (ni - parent - nci - funds).abs() > 0.01 * ni.abs() + 1e6
    stats['attribution_dropped'] = int(split.sum())
    # A zero parent line is a blank placeholder: keep the minority line so the
    # engine can fall back to net_profit - noncontrolling_profit. Otherwise
    # it is unknown which line is wrong, so both go.
    if 'parent_net_profit' in w:
        if 'noncontrolling_profit' in w:
            w.loc[split & (parent != 0), 'noncontrolling_profit'] = float('nan')
        w.loc[split, 'parent_net_profit'] = float('nan')
    w = w.drop(columns=[c for c in ('_profit_to_funds',) if c in w])
    long = w.stack().rename('value').reset_index()
    return long[long['value'].notna()], dict(stats)


def load_dstock(pins, raw_files, tickers):
    """DStock annual statements; NON_FINANCE item codes only, Regular tickers only."""
    values = defaultdict(set)
    for rel in raw_files:
        payload = json.loads(pins.read(rel))
        for r in payload.get('data', []) if isinstance(payload, dict) else []:
            if 'itemCode' not in r or r.get('reportType') != 'ANNUAL' or r.get('code') not in tickers:
                continue
            code = int(r['itemCode'])
            if code not in DSTOCK_SCHEMA or r.get('numericValue') is None or not str(r['fiscalDate']).endswith('-12-31'):
                continue
            year = int(r['fiscalDate'][:4])
            if year in YEARS:
                values[r['code'], year, DSTOCK_SCHEMA[code][0]].add(float(r['numericValue']))
    rows = [dict(ticker=t, fiscal_year=y, field=f, value=next(iter(v))) for (t, y, f), v in values.items() if len(v) == 1]
    frame = pd.DataFrame(rows, columns=['ticker', 'fiscal_year', 'field', 'value'])
    frame['source'] = 'DSTOCK'
    return frame, dict(cells=len(frame), conflicting_cells=sum(len(v) > 1 for v in values.values()))


def normalize_signs(frame):
    frame = frame.copy()
    mask = frame['field'].isin(COST_FIELDS)
    frame.loc[mask, 'value'] = frame.loc[mask, 'value'].abs()
    return frame


def validate_dstock(cafef, dstock, min_overlap=30):
    """Per-field agreement on cells both sources have. QA fields must pass to keep DStock at all."""
    a = normalize_signs(cafef).set_index(['ticker', 'fiscal_year', 'field'])['value']
    b = normalize_signs(dstock).set_index(['ticker', 'fiscal_year', 'field'])['value']
    both = pd.concat([a.rename('cafef'), b.rename('dstock')], axis=1, join='inner').reset_index()
    denom = both[['cafef', 'dstock']].abs().max(axis=1)
    both['ok'] = ((both.cafef - both.dstock).abs() <= DSTOCK_TOLERANCE * denom) | (denom == 0)
    report = both.groupby('field').ok.agg(overlap='size', pass_rate='mean').reset_index()
    report['accepted'] = (report.overlap >= min_overlap) & (report.pass_rate >= DSTOCK_MIN_PASS)
    qa = report[report.field.isin(DSTOCK_QA_FIELDS)]
    if len(qa) < len(DSTOCK_QA_FIELDS) or not qa.accepted.all():
        report['accepted'] = False  # Mapping itself is not trusted.
    return report


def combine(cafef_parts, dstock, accepted_fields):
    primary = pd.concat(cafef_parts, ignore_index=True)
    have = pd.MultiIndex.from_frame(primary[['ticker', 'fiscal_year', 'field']])
    fill = dstock[dstock.field.isin(accepted_fields)]
    fill = fill[~pd.MultiIndex.from_frame(fill[['ticker', 'fiscal_year', 'field']]).isin(have)]
    return normalize_signs(pd.concat([primary, fill], ignore_index=True))


def pivot_wide(long, families, securities):
    values = long.pivot_table(index=['ticker', 'fiscal_year'], columns='field', values='value', aggfunc='first')
    sources = long.pivot_table(index=['ticker', 'fiscal_year'], columns='field', values='source', aggfunc='first')
    values = values.reindex(columns=list(FIELDS))
    sources = sources.reindex(columns=list(FIELDS)).add_prefix('src__')
    wide = values.join(sources).reset_index()
    meta = families[['ticker', 'template_family']].merge(securities, on='ticker', how='left')
    meta['sector_group'] = [sector_group(t, f) for t, f in zip(meta.ticker, meta.template_family)]
    return meta.merge(wide, on='ticker', how='right')[
        ['ticker', 'fiscal_year', 'name', 'exchange', 'template_family', 'sector_group'] + list(FIELDS)
        + ['src__' + f for f in FIELDS]].sort_values(['ticker', 'fiscal_year']).reset_index(drop=True)


JUMP_FIELDS = ('total_assets', 'total_liabilities', 'total_equity', 'net_revenue')


def run_checks(wide):
    """Flags only; nothing is corrected."""
    out = []
    for r in wide.itertuples(index=False):
        ta, tl, te = r.total_assets, r.total_liabilities, r.total_equity
        if pd.notna(ta) and pd.notna(tl) and pd.notna(te) and ta:
            gap = abs(ta - (tl + te)) / abs(ta)
            if gap >= 0.01:
                out.append((r.ticker, r.fiscal_year, 'BALANCE_IDENTITY', f'{gap:.4f}'))
        if pd.notna(ta) and ta <= 0:
            out.append((r.ticker, r.fiscal_year, 'NONPOSITIVE_TOTAL_ASSETS', str(ta)))
        if pd.notna(r.net_revenue) and r.net_revenue < 0:
            out.append((r.ticker, r.fiscal_year, 'NEGATIVE_NET_REVENUE', str(r.net_revenue)))
        ie, fe = r.interest_expense, r.finance_expense
        if pd.notna(ie) and pd.notna(fe) and ie > fe * 1.001 + 1:
            out.append((r.ticker, r.fiscal_year, 'INTEREST_EXCEEDS_FINANCE_EXPENSE', f'{ie}>{fe}'))
        cf = r.cashflow_interest_adjustment
        if pd.notna(ie) and pd.notna(cf) and abs(ie - abs(cf)) > 0.05 * max(ie, abs(cf)) + 1e6:
            out.append((r.ticker, r.fiscal_year, 'INTEREST_VS_CASHFLOW_INTEREST', f'{ie}/{cf}'))
    for field in JUMP_FIELDS:
        s = wide[['ticker', 'fiscal_year', field]].dropna()
        prev = s.groupby('ticker')[field].shift()
        prev_year = s.groupby('ticker')['fiscal_year'].shift()
        ratio = (s[field].abs() / prev.abs()).where((prev_year == s.fiscal_year - 1) & (prev.abs() > 0) & (s[field].abs() > 0))
        flagged = (ratio >= 100) | (ratio <= 0.01)
        for t, y, v in zip(s.loc[flagged, 'ticker'], s.loc[flagged, 'fiscal_year'], ratio[flagged]):
            out.append((t, y, 'UNIT_JUMP_X100:' + field, f'{v:.4g}'))
    return pd.DataFrame(out, columns=['ticker', 'fiscal_year', 'check', 'detail'])


def coverage(wide):
    present = wide[list(FIELDS)].notna().astype(int)
    return pd.concat([wide[['ticker', 'fiscal_year', 'template_family']], present], axis=1)
