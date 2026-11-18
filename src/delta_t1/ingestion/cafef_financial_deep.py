"""Dedicated CafeF report/disclosure adapters. Preserve group and raw-code identity.

These are candidates, never accepted accounting facts. A template label does not
prove that the provider populated its code with the correct accounting value.
"""
import json
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
from urllib.parse import urlencode

ROUTES = {'CDKT': ('v2', 'GetReportCDKT'), 'KQKD': ('v1', 'GetReportDetail'),
          'LCTT': ('v1', 'GetReportLCTT')}


def report_url(symbol, statement, mode='NAM', group='ALL', page=1):
    version, route = ROUTES[statement]
    return 'https://apiweb.cafef.vn/api/' + version + '/BCTC/' + route + '?' + urlencode(
        dict(symbol=symbol, pageIndex=page, pageSize=4, reportType=group, TypeTime=mode))


def parse_report(body, symbol, statement, mode, source_id):
    payload = json.loads(body, parse_float=Decimal)
    if payload.get('isSuccess') is not True:
        raise ValueError('provider did not report success')
    value = payload['value']
    template = value.get('templace', [])
    fingerprint = sha256(json.dumps(template, ensure_ascii=False, sort_keys=True,
                                   default=str).encode()).hexdigest()
    labels = {}
    if statement == 'KQKD':
        template_groups = [dict(code='KQKD', data=template)]
        data_groups = [dict(code='KQKD', data=value.get('data', []))]
    else:
        template_groups, data_groups = template, value.get('data', [])
    for group in template_groups:
        for row in group.get('data', []):
            key = (group['code'], row['code'])
            if key in labels:
                raise ValueError('duplicate template code')
            labels[key] = row['name']
    result = []
    for group in data_groups:
        # Every group has its own period headers and pagination.
        for period in group.get('data', []):
            if period['symbol'].upper() != symbol.upper():
                raise ValueError('report issuer mismatch')
            year, quarter = int(period['year']), int(period['quater'])
            # A QUY cashflow may be YTD. Do not manufacture an interval.
            interval = ('ANNUAL' if mode == 'NAM' else
                        'H1_REVIEWED' if mode == 'LUYKE' and quarter == 2 else
                        'INTERVAL_UNRESOLVED' if statement == 'LCTT' else 'QUARTER')
            for cell in period.get('data', []):
                raw = cell.get('value')
                numeric = None
                if raw is not None and not isinstance(raw, bool) and str(raw).strip() not in ['', '-', '—']:
                    numeric = str(Decimal(str(raw)))
                label = labels.get((group['code'], cell['code']))
                result.append(dict(source_id=source_id, symbol=symbol.upper(), statement=statement,
                    route_version=ROUTES[statement][0], template_sha256=fingerprint,
                    group=group['code'], raw_code=cell['code'], label=label,
                    year=year, quarter=quarter, header=period.get('time'),
                    provider_type=period.get('type'), mode=mode, interval=interval,
                    provider_unit=value.get('unit'), raw_value=raw, value=numeric,
                    unit_status='FIELD_UNIT_REVIEW_REQUIRED',
                    mapping_status='UNMAPPED_TEMPLATE' if label is None else 'CANDIDATE_ONLY'))
    return result


def disclosures(body, symbol):
    payload = json.loads(body)
    rows = payload.get('Data', {}).get('BctcList', [])
    output = []
    for r in rows:
        if r['Symbol'].upper() != symbol.upper():
            raise ValueError('disclosure issuer mismatch')
        match = re.fullmatch(r'/Date\((\d+)(?:[+-]\d+)?\)/', r.get('CreateDate', ''))
        day = (datetime.fromtimestamp(int(match[1]) / 1000, timezone(timedelta(hours=7))).date().isoformat()
               if match else None)
        output.append(dict(symbol=symbol, provider_id=r['Id'], year=r['Year'],
            quarter=r['Quarter'], provider_type=r['ReportType'], title=r['Content'],
            link_file=r['LinkFile'], create_date_raw=r.get('CreateDate'),
            publication_date=day, precision='DATE_ONLY' if day else 'UNKNOWN'))
    return output


def compare_candidate(candidate, expected, tolerance='0'):
    """Quarantine a code+label+template conflict; never shift adjacent row values."""
    if candidate['value'] is None:
        return 'NOT_EXTRACTED'
    if not candidate.get('label'):
        return 'MAPPING_CONFLICT'
    return ('MATCH' if abs(Decimal(candidate['value']) - Decimal(str(expected))) <= Decimal(tolerance)
            else 'MAPPING_CONFLICT')
