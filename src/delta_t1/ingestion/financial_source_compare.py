"""Bounded acquisition and source-qualified benchmark candidates, never features."""
import copy
import json
import math
import os
import time
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, build_opener

from .cafef_financial import digest, encoded, now
from .cafef_financial_detail import parse_detail
from .financial_crawl_candidates import candidates, structured_request
from .financial_data_report import FIELDS
from .financial_batch_evidence import validate_url
from .sources.base import AccessControlError, NoRedirect

REPORTS = {'CDKT': 'bsheet', 'KQKD': 'incsta', 'LCTT': 'cashflow'}
COMMON = {'current_assets', 'total_assets', 'current_liabilities', 'total_liabilities',
          'total_equity', 'retained_earnings', 'net_revenue', 'gross_profit', 'net_profit',
          'parent_net_profit', 'operating_cash_flow', 'vendor_basic_eps', 'vendor_diluted_eps'}


def kbs_request(symbol, report, period, page=1, page_size=1):
    request = structured_request(symbol, report, period, page)
    parts = urlsplit(request['url'])
    params = dict(parse_qsl(parts.query))
    params['pageSize'] = str(page_size)
    request['url'] = urlunsplit(parts._replace(query=urlencode(params)))
    return dict(request, page_size=page_size)


def strict_json(body):
    def reject(value):
        raise ValueError('nonfinite JSON ' + value)
    def number(value):
        result = float(value)
        if not math.isfinite(result): reject(value)
        return result
    return json.loads(body, parse_constant=reject, parse_float=number)


def parse_kbs(body, request, company_type):
    payload = strict_json(body)
    heads, content = payload.get('Head'), payload.get('Content')
    if not isinstance(heads, list) or not isinstance(content, dict):
        raise ValueError('unexpected KBS envelope')
    cleaned = copy.deepcopy(payload)
    null_trailing = 0
    for section, records in cleaned['Content'].items():
        if not isinstance(records, list): raise ValueError('unexpected KBS report rows')
        for record in records:
            for column in list(record):
                if column.startswith('Value') and column[5:].isdigit() and int(column[5:]) > len(heads):
                    if record[column] is not None:
                        raise ValueError('non-null numeric column has no matching Head')
                    null_trailing += 1
                    del record[column]
    if not heads:
        return [], dict(status='END_OF_SERIES', null_trailing_columns=null_trailing)
    rows = candidates(cleaned, dict(request, path=request['path'], sha256=request['sha256']),
                      list(range(2019, 2027)), company_type)
    output = []
    for row in rows:
        field = row['field']
        if field == 'basic_eps': field = 'vendor_basic_eps'
        if field == 'diluted_eps': field = 'vendor_diluted_eps'
        regular = company_type == 'Regular' and type(row['header'].get('BusinessType')) is int and row['header']['BusinessType'] == 1
        ambiguous = row['header_status'] == 'AMBIGUOUS_DUPLICATED_PERIOD_COLUMNS'
        value = row['value'] if regular else None
        if regular and field in {'vendor_basic_eps', 'vendor_diluted_eps'} and not ambiguous and row['raw_value'] is not None and row['status']!='INVALID_NUMERIC_VALUE':
            value = str(Decimal(str(row['raw_value'])))  # Per-share QA hypothesis only, never monetary *1000.
        output.append(dict(provider='KBS', symbol=row['symbol'], report=request['report'],
            year=row['year'], quarter=row['quarter'], code=row['report_norm_id'], label=row['label'],
            raw_value=row['raw_value'], field=field if regular and field in COMMON else None,
            comparison_value=value, unit_basis='QUERY_UNIT_1000_OR_UNSCALED_EPS_QA_HYPOTHESIS',
            unambiguous=not ambiguous and row['year'] is not None and row['quarter'] is not None,
            header=row['header'], source_sha256=request['sha256'], source_path=request['path'],
            numeric_status=row['status'], financial_features_allowed=False))
    return output, dict(status='PARSED_CANDIDATES', null_trailing_columns=null_trailing)


def parse_cafef(body, request, company_type):
    parsed = parse_detail(body, request['symbol'], request['statement'], request['year'], request['quarter'])
    output = []
    for row in parsed['facts']:
        field = next((field for field, (statement, code, token) in FIELDS.items()
                      if statement == request['statement'] and code == row['provider_item_code']
                      and token in row['item_name'].casefold() and field in COMMON), None)
        regular = company_type == 'Regular'
        output.append(dict(provider='CAFEF', symbol=row['symbol'], report=request['report'],
            year=row['year'], quarter=row['quarter'], code=row['provider_item_code'], label=row['item_name'],
            raw_value=row['display_number_candidate'], field=field if regular else None,
            comparison_value=str(row['display_number_candidate']) if regular and field and row['display_number_candidate'] is not None else None,
            unit_basis='AS_DISPLAYED_QA_HYPOTHESIS_NOT_DISPLAY_LABEL_MULTIPLIER',
            unambiguous=True, header=dict(display_unit_labels=parsed['display_unit_labels'], requested_anchor=[request['year'], request['quarter']]),
            source_sha256=request['sha256'], source_path=request['path'], numeric_status='CANDIDATE_ONLY',
            financial_features_allowed=False))
    return output, dict(status='PARSED_CANDIDATES', null_trailing_columns=0)


class BenchmarkTransport:
    """One compact durable journal; whole-response reservation protects interruption."""
    def __init__(self, output, config, *, opener=None, clock=time.monotonic, sleep=time.sleep):
        self.output, self.c = output, config
        self.opener = opener or build_opener(NoRedirect())
        self.clock, self.sleep, self.started, self.last = clock, sleep, clock(), clock()
        self.state = dict(attempts=0, bytes_read=0, reserved_bytes=0, boundary=False)
        self.previous = None

    def event(self, action, **data):
        row = dict(at=now(), action=action, data=data, state=dict(self.state), previous_sha256=self.previous)
        raw = json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
        with (self.output/'transport.jsonl').open('ab') as stream:
            stream.write(raw.rstrip(b'\n') + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.previous = digest(raw)

    def get(self, request):
        validate_url(request['url'], self.c['approved_hosts'])
        if self.state['boundary']: raise AccessControlError('benchmark access boundary latched')
        if self.state['attempts'] >= self.c['max_attempts']: raise ValueError('benchmark request cap')
        response_cap = self.c['max_response_bytes']
        reservation = response_cap + 1
        if self.state['bytes_read'] + self.state['reserved_bytes'] + reservation > self.c['max_total_bytes']:
            raise ValueError('benchmark total byte cap')
        elapsed = self.clock() - self.started
        delay = max(0, self.c['interval_seconds'] - (self.clock() - self.last))
        if elapsed + delay >= self.c['max_seconds']: raise ValueError('benchmark time cap')
        self.sleep(delay)
        self.last = self.clock()
        self.state['attempts'] += 1
        self.state['reserved_bytes'] += reservation
        self.event('ATTEMPT_RESERVED', request=request)
        began = self.clock()
        try:
            with self.opener.open(Request(request['url'], headers={'User-Agent':'DeltaT1Research/0.4 (academic benchmark)'}),
                timeout=min(20, self.c['max_seconds']-(self.clock()-self.started))) as response:
                if response.status != 200: raise ValueError('HTTP '+str(response.status))
                chunks=[]; size=0
                while size < reservation:
                    remaining=self.c['max_seconds']-(self.clock()-self.started)
                    if remaining<=0: raise ValueError('benchmark time cap during response')
                    sock=getattr(getattr(getattr(response,'fp',None),'raw',None),'_sock',None)
                    if sock:sock.settimeout(min(20,remaining))
                    chunk=getattr(response,'read1',response.read)(min(65536,reservation-size))
                    size+=len(chunk);self.state['bytes_read']+=len(chunk);chunks.append(chunk)
                    if not chunk:break
                body=b''.join(chunks)
                self.state['reserved_bytes'] -= reservation
                if len(body) > response_cap: raise ValueError('response byte cap')
                if any(marker in body[:4096].lower() for marker in [b'captcha',b'managed challenge',b'login wall',b'cloudflare']):
                    self.state['boundary'] = True
                    raise AccessControlError('challenge boundary')
            duration = self.clock()-began
            self.event('ATTEMPT_COMPLETE', seconds=duration, bytes=len(body), sha256=digest(body))
            return body, duration
        except HTTPError as exc:
            self.state['reserved_bytes'] -= reservation  # No response body read.
            self.state['boundary'] = exc.code in (401,403,429)
            self.event('HTTP_ERROR', code=exc.code)
            if self.state['boundary']: raise AccessControlError('HTTP '+str(exc.code)) from None
            raise ValueError('HTTP '+str(exc.code)+'; no redirect/workaround') from None
        except (URLError,TimeoutError,ConnectionError) as exc:
            # Partial read length unknown; retain reservation conservatively.
            self.event('TRANSPORT_ERROR', error=str(exc))
            raise ValueError('bounded benchmark transport failure') from None
        except (ValueError,AccessControlError) as exc:
            # Persist terminal cap/challenge state, retaining unfinished reservations.
            self.event('ATTEMPT_REJECTED',error=str(exc))
            raise
