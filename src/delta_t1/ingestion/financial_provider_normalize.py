"""Offline KBS candidates: preserve wire cells, nulls, dates and unit exceptions."""
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, parse_qs

CODEBOOK = {
    3000: 'current_assets', 2996: 'total_assets', 3014: 'current_liabilities',
    2997: 'total_liabilities', 2998: 'total_equity', 3072: 'retained_earnings',
    3022: 'gross_short_term_trade_receivables', 3035: 'net_tangible_ppe',
    3078: 'noncurrent_loans_and_finance_leases', 2216: 'net_revenue',
    2217: 'gross_profit', 2212: 'net_profit', 2214: 'parent_net_profit',
    2234: 'operating_cash_flow', 2215: 'basic_eps', 5316: 'diluted_eps',
}


def normalize_kbs(payload, request):
    if request.get('provider') != 'KBS':
        raise ValueError('unsupported provider')
    query = parse_qs(urlsplit(request['url']).query)
    if query.get('unit') != ['1000']:
        raise ValueError('explicit unit=1000 required; no magnitude inference')
    heads, content = payload.get('Head'), payload.get('Content')
    if not isinstance(heads, list) or not isinstance(content, dict):
        raise ValueError('unexpected KBS envelope')
    result = []
    for section, rows in content.items():
        if not isinstance(rows, list):
            raise ValueError('unexpected Content section')
        for row in rows:
            # Header length and requested pageSize do not create numeric columns.
            columns = sorted((k for k in row if k.startswith('Value') and k[5:].isdigit()),
                             key=lambda k: int(k[5:]))
            for column in columns:
                position = int(column[5:]) - 1
                if position < 0 or position >= len(heads):
                    raise ValueError('numeric column has no matching Head')
                head, raw = heads[position], row[column]
                code = row['ReportNormID']; field = CODEBOOK.get(code)
                cell = dict(symbol=request['symbol'], provider='KBS', section=section,
                    report_norm_id=code, label=row.get('NameEn'), column=column, header=head,
                    raw_value=raw, field=field, value=None, unit='UNVERIFIED',
                    published_at=None, available_at=None, financial_features_allowed=False,
                    source_path=request['path'], source_sha256=request['sha256'],
                    date_policy='PROVIDER_METADATA_ONLY_NOT_RELEASE_EVIDENCE')
                if raw is None:
                    cell['status'] = 'MISSING_WIRE_VALUE'
                elif field in ('basic_eps', 'diluted_eps'):
                    cell['status'] = 'PER_SHARE_UNIT_EXCEPTION_REVIEW_REQUIRED'
                elif field is None:
                    cell['status'] = 'UNMAPPED_WIRE_VALUE'
                else:
                    try:
                        if type(raw) is bool: raise ValueError('boolean')
                        number = Decimal(str(raw))
                        if not number.is_finite(): raise ValueError('nonfinite')
                        cell.update(value=str(number * 1000), unit='VND',
                            status='MONETARY_CANDIDATE_REQUIRES_PDF_VALIDATION',
                            unit_basis='REQUEST_UNIT_1000_MONETARY_CODEBOOK_CANDIDATE')
                    except (InvalidOperation, ValueError, TypeError):
                        cell['status'] = 'INVALID_NUMERIC_VALUE'
                result.append(cell)
    return result


def compare_cell(cell, reviewed_value):
    if cell['value'] is None:
        return dict(status='NOT_COMPARABLE', financial_features_allowed=False)
    difference = Decimal(cell['value']) - Decimal(str(reviewed_value))
    return dict(status='MATCH_WITHIN_THOUSAND_VND_ROUNDING' if abs(difference) <= 500 else 'VALUE_CONFLICT',
        difference_vnd=str(difference), tolerance_vnd=500, financial_features_allowed=False)
