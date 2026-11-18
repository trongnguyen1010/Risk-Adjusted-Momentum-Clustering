"""Persistent trial-wide counters and finite public HTTPS transport.

Reservations are sealed before I/O so interruption cannot reset attempt/byte caps.
No credentials, redirects, boundary retries, or provider fallback.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from .cafef_financial import digest, encoded, immutable_write, now
from .financial_batch_evidence import inside, seal, validate_url
from .financial_documents import verify_inventory
from .sources.base import AccessControlError, NoRedirect, RateLimitError


class TrialBudgetError(ValueError):
    pass


def read_ledger(folder, verified_outer=False):
    """Read only sealed events; reject gaps and modified cumulative history."""
    folder = Path(folder)
    events, previous, requests = [], None, {}
    for child in sorted(folder.glob('[0-9]*')):
        if not (child/'manifest.json').exists():
            # Only the final event may have been interrupted while writing.
            if child != sorted(folder.glob('[0-9]*'))[-1]:
                raise ValueError('unsealed event inside ledger chain')
            continue
        # A verified outer run pins every event AND its manifest already.
        if not verified_outer:
            verify_inventory(child)
        event = json.loads((child/'event.json').read_bytes())
        if event['index'] != len(events)+1 or event['previous_sha256'] != previous:
            raise ValueError('trial ledger chain mismatch')
        requests.update(event['state'].get('requests', {}))
        if event['detail'].get('request_key') and event['detail'].get('request_snapshot'):
            requests[event['detail']['request_key']] = event['detail']['request_snapshot']
        events.append(event)
        previous = digest((child/'event.json').read_bytes())
    if events:
        events[-1]['state']['requests'] = requests
    return events


class TrialTransport:
    def __init__(self, root, output, config, resume_state=None, *, opener=None,
                 sleep=time.sleep, clock=time.monotonic, utc=None):
        self.root, self.output, self.config = Path(root), Path(output), config
        self.b = config['budgets']
        self.opener = opener or build_opener(NoRedirect())
        self.sleep, self.clock = sleep, clock
        self.utc = utc or (lambda: datetime.now(timezone.utc).timestamp())
        self.last = self.clock()  # Keep spacing on the first attempt after resume too.
        self.context = {}
        self.previous, self.index = None, 0
        self.journal = []
        self.state = json.loads(json.dumps(resume_state)) if resume_state else dict(
            created_at=self.utc(), logical_requests=0, transport_attempts=0,
            pdf_download_attempts=0, downloaded_bytes=0, reserved_bytes=0,
            text_pages=0, reserved_text_pages=0,
            requests={}, boundary=False, budget_stop=False, stop_reason=None)
        if 'text_pages' not in self.state or 'reserved_text_pages' not in self.state:
            raise ValueError('old trial ledger lacks global page counters; cannot reset counters on resume')
        self.event('START_OR_RESUME')

    def event(self, action, **detail):
        self.index += 1
        state = {k:v for k,v in self.state.items() if k != 'requests'}
        if action == 'START_OR_RESUME':
            state['requests'] = self.state['requests']
        if detail.get('request_key'):
            detail['request_snapshot'] = self.state['requests'][detail['request_key']]
        event = dict(index=self.index, previous_sha256=self.previous, at=now(),
                     action=action, detail=detail, state=json.loads(json.dumps(state)))
        folder = self.output/'ledger'/f'{self.index:06d}'
        immutable_write(folder/'event.json', encoded(event))
        seal(folder)
        self.previous = digest((folder/'event.json').read_bytes())
        self.journal.append(json.loads(json.dumps(dict(index=event['index'],at=event['at'],action=action,detail=detail,
                                 counters={k:v for k,v in state.items() if k!='requests'}))))

    def remaining_seconds(self):
        return max(0, self.state['created_at'] + self.b['max_wall_seconds'] - self.utc())

    def stop_budget(self, reason):
        self.state.update(budget_stop=True, stop_reason=reason)
        self.event('BUDGET_STOP', reason=reason)
        raise TrialBudgetError(reason)

    def check(self):
        if self.state['boundary']:
            raise AccessControlError('trial-wide access boundary remains latched')
        if self.state['budget_stop']:
            raise TrialBudgetError(self.state['stop_reason'])
        if self.remaining_seconds() <= 0:
            self.stop_budget('WALL_TIME_CAP')

    def boundary(self, reason):
        self.state.update(boundary=True, stop_reason=reason)
        self.event('HARD_STOP', reason=reason)
        if '429' in reason:
            raise RateLimitError(reason)
        raise AccessControlError(reason)

    def get(self, url):
        self.check()
        validate_url(url, self.config['approved_hosts'])
        key = digest(encoded(dict(url=url, kind=self.context.get('kind'),
                                  cache_epoch=self.config['cache_epoch'])))
        request = self.state['requests'].get(key)
        if request is None:
            if self.state['logical_requests'] >= self.b['max_logical_requests']:
                self.stop_budget('LOGICAL_REQUEST_CAP')
            request = self.state['requests'][key] = dict(url=url,kind=self.context.get('kind'),attempts=0,
                **{k:self.context[k] for k in ['symbol','report','period','page','year'] if k in self.context})
            self.state['logical_requests'] += 1
            self.event('REQUEST_RESERVED', request_key=key, request=request)
        if request['attempts'] >= self.b['max_attempts_per_request']:
            raise ValueError('request attempt cap exhausted across resumes')
        while request['attempts'] < self.b['max_attempts_per_request']:
            self.check()
            if self.state['transport_attempts'] >= self.b['max_transport_attempts']:
                self.stop_budget('TRANSPORT_ATTEMPT_CAP')
            if request['kind'] == 'pdf' and self.state['pdf_download_attempts'] >= self.b['max_pdf_download_attempts']:
                self.stop_budget('PDF_ATTEMPT_CAP')
            delay = max(0, self.b['min_seconds_between_transport_attempts']-(self.clock()-self.last))
            if delay >= self.remaining_seconds():
                self.stop_budget('WALL_TIME_CAP')
            self.sleep(delay)
            self.check()
            request['attempts'] += 1
            self.state['transport_attempts'] += 1
            self.state['pdf_download_attempts'] += int(request['kind'] == 'pdf')
            self.event('ATTEMPT_START', request_key=key, attempt=request['attempts'])
            self.last = self.clock()
            try:
                timeout = min(self.b['timeout_seconds'], self.remaining_seconds())
                with self.opener.open(Request(url, headers={'User-Agent': 'DeltaT1Research/0.3 (academic; non-commercial demo)'}), timeout=timeout) as response:
                    if response.status in (401,403,429):
                        self.boundary('HTTP '+str(response.status))
                    if response.status != 200:
                        raise ValueError('HTTP '+str(response.status))
                    body = bytearray()
                    while True:
                        self.check()
                        remaining = self.b['max_total_downloaded_bytes']-self.state['downloaded_bytes']-self.state['reserved_bytes']
                        response_remaining = self.b['max_response_bytes']-len(body)
                        if response_remaining <= 0:
                            raise ValueError('RESPONSE_BYTE_CAP: response at cap requires review')
                        if remaining <= 0:
                            self.stop_budget('TOTAL_BYTE_CAP')
                        count = min(65536, remaining, response_remaining)
                        # Interrupted reads retain the reservation as conservative budget use.
                        self.state['reserved_bytes'] += count
                        self.event('READ_RESERVED', request_key=key, bytes=count)
                        sock = getattr(getattr(getattr(response, 'fp', None), 'raw', None), '_sock', None)
                        if sock:
                            sock.settimeout(min(self.b['timeout_seconds'], self.remaining_seconds()))
                        reader = getattr(response, 'read1', response.read)
                        chunk = reader(count)
                        if len(chunk) > count:
                            raise ValueError('transport returned more bytes than requested')
                        self.state['reserved_bytes'] -= count
                        self.state['downloaded_bytes'] += len(chunk)
                        self.event('READ_FINISHED', request_key=key, bytes=len(chunk))
                        body.extend(chunk)
                        marker = bytes(body[:4096]).lower()
                        if any(m in marker for m in (b'captcha',b'managed challenge',b'login wall',b'cloudflare')):
                            self.boundary('challenge boundary')
                        if not chunk:
                            break
                    self.event('ATTEMPT_COMPLETE', request_key=key, http_status=response.status,
                               sha256=digest(bytes(body)), bytes=len(body))
                    return bytes(body), response.status
            except HTTPError as exc:
                if exc.code in (401,403,429):
                    self.boundary('HTTP '+str(exc.code))
                self.event('HTTP_ERROR', request_key=key, http_status=exc.code)
                if exc.code not in (500,502,503,504):
                    raise ValueError('HTTP '+str(exc.code)+'; no redirect/workaround') from None
            except (URLError, TimeoutError, ConnectionError) as exc:
                self.event('TRANSPORT_ERROR', request_key=key, error=str(exc))
        raise ValueError('bounded transport attempts exhausted')
