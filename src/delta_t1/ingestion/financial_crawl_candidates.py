"""Provider candidates and coverage; arithmetic checks do not establish PIT."""
import csv
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from .financial_provider_normalize import normalize_kbs

REPORT_FIELDS = {
    'CDKT': {'current_assets', 'total_assets', 'current_liabilities', 'total_liabilities',
             'total_equity', 'retained_earnings', 'gross_short_term_trade_receivables',
             'net_tangible_ppe', 'noncurrent_loans_and_finance_leases'},
    'KQKD': {'net_revenue', 'gross_profit', 'net_profit', 'parent_net_profit', 'basic_eps', 'diluted_eps'},
    'LCTT': {'operating_cash_flow'},
}


def structured_request(symbol, report, period, page=1):
    term = 1 if period == 'year' else 2
    query = dict(page=page, pageSize=12, type=report, unit=1000, termtype=term)
    if report == 'LCTT':
        query.update(code=symbol, termType=term)
    else:
        query['languageid'] = 1
    return dict(symbol=symbol, provider='KBS', report=report, period=period, page=page,
                kind='structured', url='https://kbbuddywts.kbsec.com.vn/iis-server/investment/stock/finance-info/'
                + symbol + '?' + urlencode(query))


def candidates(payload, request, years, company_type):
    """Keep every wire column; requested headers alone never create observations."""
    cells = normalize_kbs(payload, request)
    heads_by_column = {cell['column']:cell['header'] for cell in cells}
    if any(not isinstance(head, dict) for head in heads_by_column.values()):
        raise ValueError('KBS Head must contain report metadata objects')
    def period_key(head):
        return tuple(head.get(k) for k in ['YearPeriod','TermCode','United','PeriodBegin','PeriodEnd'])
    identities = Counter(period_key(head) for head in heads_by_column.values())
    for cell in cells:
        head = cell['header']
        if not isinstance(head, dict):
            raise ValueError('KBS Head must contain report metadata objects')
        year, term = head.get('YearPeriod'), head.get('TermCode')
        valid_year = type(year) is int
        quarter = 0 if term == 'N' else int(term[1:]) if isinstance(term, str) and term in ('Q1', 'Q2', 'Q3', 'Q4') else None
        period_ok = quarter == 0 if request['period'] == 'year' else quarter in (1, 2, 3, 4)
        cell.update(report=request['report'], requested_period=request['period'], requested_page=request['page'],
                    year=year if valid_year else None, quarter=quarter,
                    in_target=valid_year and year in years and period_ok,
                    company_type=company_type, scope_status='PROVIDER_METADATA_NOT_PDF_VERIFIED',
                    duration_status='INSTANT_CANDIDATE' if request['report'] == 'CDKT' else 'DURATION_REVIEW_REQUIRED',
                    framework_status='UNVERIFIED', revision_status='CURRENT_PROVIDER_VINTAGE_ONLY')
        cell['header_status'] = 'PROVIDER_PERIOD_CANDIDATE'
        if identities[period_key(head)] > 1:
            cell.update(in_target=False, value=None, header_status='AMBIGUOUS_DUPLICATED_PERIOD_COLUMNS',
                        status='HEADER_PERIOD_DUPLICATION_REVIEW_REQUIRED')
        # Numeric codes shared by different report or sector templates must not acquire a false mapping.
        if company_type != 'Regular' or head.get('BusinessType') not in (None, 1):
            cell.update(field=None, value=None, unit='UNVERIFIED', status='SECTOR_TEMPLATE_REVIEW_REQUIRED')
        elif cell['field'] and cell['field'] not in REPORT_FIELDS[request['report']]:
            cell.update(field=None, value=None, unit='UNVERIFIED', status='REPORT_TEMPLATE_REVIEW_REQUIRED')
        if cell['raw_value'] is not None:
            try:
                if type(cell['raw_value']) is bool or not Decimal(str(cell['raw_value'])).is_finite():
                    raise ValueError('nonfinite or boolean numeric cell')
            except (InvalidOperation, ValueError, TypeError):
                cell.update(value=None, status='INVALID_NUMERIC_VALUE')
    return cells


def summarize(cells, config):
    grouped, conflicts = defaultdict(list), []
    for cell in cells:
        if not cell['in_target']:
            continue
        key = (cell['symbol'], cell['report'], cell['year'], cell['quarter'], cell['report_norm_id'],
               cell['header'].get('United'), cell['header'].get('PeriodBegin'), cell['header'].get('PeriodEnd'))
        grouped[key].append(cell)
    for key, rows in sorted(grouped.items(), key=lambda x: str(x[0])):
        values = sorted({json.dumps(r['raw_value'], sort_keys=True) for r in rows})
        if len(values) > 1:
            conflicts.append(dict(key=list(key), raw_values=values, status='VALUE_CONFLICT_REVIEW_REQUIRED'))
    coverage = []
    for symbol in config['symbols']:
        for period in config['periods']:
            for report, fields in REPORT_FIELDS.items():
                for year in config['years']:
                    for quarter in ([0] if period == 'year' else [1, 2, 3, 4]):
                        selected = [r for r in cells if r['symbol'] == symbol and r['report'] == report
                                    and r['year'] == year and r['quarter'] == quarter and r['in_target']]
                        present = {r['field'] for r in selected if r['field'] and r['raw_value'] is not None
                                   and r['status'] != 'INVALID_NUMERIC_VALUE'}
                        coverage.append(dict(symbol=symbol, report=report, year=year, quarter=quarter,
                            wire_cells=len(selected), fields_with_candidates=sorted(present),
                            missing_core_fields=sorted(fields - present),
                            status='CANDIDATES_PRESENT' if present else 'MISSING_OR_UNMAPPED_PERIOD',
                            verified=False, published_at=None))
    qa = []
    # Only compare values from the same response/header. Never splice pages/scopes/vintages.
    bs = defaultdict(lambda: defaultdict(list))
    for r in cells:
        if r['in_target'] and r['report'] == 'CDKT' and r['value'] is not None:
            bs[(r['symbol'], r['source_sha256'], json.dumps(r['header'], sort_keys=True))][r['field']].append(r)
    for (symbol, sha, header), fields in sorted(bs.items()):
        required = ['total_assets', 'total_liabilities', 'total_equity']
        check = dict(symbol=symbol, source_sha256=sha, header=json.loads(header),
                     check='ASSETS_EQUALS_LIABILITIES_PLUS_EQUITY', tolerance_vnd=1500,
                     financial_features_allowed=False)
        if any(len(fields.get(f, [])) != 1 for f in required):
            check['status'] = 'MISSING_OR_AMBIGUOUS_INPUT'
        else:
            a, l, e = [Decimal(fields[f][0]['value']) for f in required]
            residual = a - l - e
            check.update(residual_vnd=str(residual), status='CANDIDATE_ARITHMETIC_PASS'
                         if abs(residual) <= 1500 else 'CANDIDATE_ARITHMETIC_CONFLICT')
        qa.append(check)
    return dict(wire_cells=len(cells), in_target_cells=sum(r['in_target'] for r in cells),
                statuses=dict(Counter(r['status'] for r in cells)), coverage=coverage,
                conflicts=conflicts, accounting_qa=qa, accepted_facts=0)


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fields, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        record = {}
        for field in fields:
            value = row.get(field)
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            # Safe when an upstream label is opened in a spreadsheet.
            if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
                value = "'" + value
            record[field] = value
        writer.writerow(record)
    return ('\ufeff' + stream.getvalue()).encode('utf8')
