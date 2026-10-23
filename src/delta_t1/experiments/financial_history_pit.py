"""History pilot acquisition. Provider candidates and PIT acceptance stay separate."""
import csv
import io
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.cafef_financial_deep import parse_report, report_url, disclosures
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import CompactTrialTransport, read_compact
from ..ingestion.financial_trial_transport import TrialBudgetError
from ..ingestion.sources.base import AccessControlError, RateLimitError
from .financial_user_workflow import exclusive

VERSION = 'financial-history-pit-v1'
PILOT = ['BRC', 'FPT', 'MWG', 'GMD', 'VNM']
GROUPS = {'CDKT': ['TN', 'NV'], 'KQKD': ['KQKD'], 'LCTT': ['HDKD', 'HDDT', 'HDTC']}
CLOSED = dict(financial_features_allowed=False, financial_cluster_allowed=False,
              research_ready=False, full_universe_allowed=False, next_100_allowed=False)
IMPLEMENTATION = [
    'src/delta_t1/experiments/financial_history_pit.py',
    'src/delta_t1/ingestion/cafef_financial_deep.py',
    'src/delta_t1/ingestion/financial_compact_trial.py',
    'src/delta_t1/ingestion/financial_trial_transport.py',
    'scripts/financial_history_pit.py', 'scripts/financial_history_pit.ps1']


class EvidenceIntegrityError(ValueError):
    pass


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    body = encoded(value)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError('immutable output changed: ' + str(path))
    else:
        immutable_write(path, body)


def csv_bytes(rows, fields):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
                         if isinstance(v, (dict, list)) else v for k, v in row.items()})
    return out.getvalue().encode('utf-8')


def validate(config):
    if config.get('version') != VERSION or config.get('symbols') != PILOT:
        raise ValueError('history successor is bounded to pilot5; scale needs a successor gate')
    if any(config.get(k) is not False for k in CLOSED):
        raise ValueError('closed research/scale gates required')
    if config.get('years') != list(range(2013, 2026)) or config.get('auxiliary_balance_year') != 2012:
        raise ValueError('exact history range required')
    if config.get('approved_hosts') != ['apiweb.cafef.vn']:
        raise ValueError('only dedicated financial API enabled for this stage')
    caps = dict(max_logical_requests=1600, max_transport_attempts=3200,
                max_pdf_download_attempts=0, max_response_bytes=5_000_000,
                max_total_downloaded_bytes=2_000_000_000, max_wall_seconds=259200,
                max_attempts_per_request=2, timeout_seconds=20)
    for key, cap in caps.items():
        value = config['budgets'].get(key)
        if type(value) is not int or value < (0 if cap == 0 else 1) or value > cap:
            raise ValueError('invalid history budget: ' + key)
    if config['budgets']['min_seconds_between_transport_attempts'] < 2:
        raise ValueError('minimum financial spacing is 2 seconds')
    if config.get('network_concurrency') != 1 or config.get('max_campaign_days') != 90:
        raise ValueError('single transport and absolute campaign deadline required')
    return config


def task_url(task):
    if task['kind'] == 'DISCLOSURE':
        return 'https://cafef.vn/du-lieu/ajax/ajaxcongbothongtin.ashx?' + urlencode(
            dict(symbol=task['symbol'], pagesize=20, pageindex=task['page']))
    return report_url(task['symbol'], task['statement'], task['mode'], task['group'], task['page'])


def tasks(config):
    result = []
    for symbol in config['symbols']:
        for mode, pages in [('NAM', 5), ('QUY', 15), ('LUYKE', 5)]:
            for statement, groups in GROUPS.items():
                if mode == 'LUYKE' and statement == 'CDKT':
                    continue
                for group in groups:
                    for page in range(1, pages + 1):
                        series = ':'.join([symbol, statement, mode, group])
                        t = dict(kind='REPORT', symbol=symbol, statement=statement,
                                 mode=mode, group=group, page=page, series=series)
                        t['url'] = task_url(t)
                        t['id'] = digest(t['url'].encode())
                        result.append(t)
        for page in range(1, 81):
            t = dict(kind='DISCLOSURE', symbol=symbol, statement='DISCLOSURE', mode='CATALOGUE',
                     group='CATALOGUE', page=page, series=symbol + ':DISCLOSURE')
            t['url'] = task_url(t)
            t['id'] = digest(t['url'].encode())
            result.append(t)
    # Breadth-first pagination across issuer/groups; catalogue cache first.
    return sorted(result, key=lambda t: (t['page'], t['kind'], t['symbol'], t['mode'], t['statement'], t['group']))


def audit_boundaries(root, config, exclude):
    """Import old host boundaries conservatively; never reinterpret them as expiry."""
    journals = []
    for relative in config['boundary_roots']:
        journals.extend(inside(root, relative).rglob('transport.jsonl'))
    records, errors = [], []
    for path in sorted(set(journals)):
        if path.is_relative_to(exclude):
            continue
        try:
            raw = path.read_bytes()
            lines = raw.splitlines()
            if not raw.endswith(b'\n'):
                raise ValueError('torn imported boundary journal')
            events = [json.loads(line) for line in lines]
            if events and 'index' in events[0]:
                ledger = read_compact(path.parent)
                state = ledger['state']
                requests = list(state.get('requests', {}).values())
            else:
                # Older benchmark journal has data.request rather than compact index.
                state = events[-1]['state']
                requests = [e.get('data', {}).get('request', {}) for e in events]
            if type(state.get('boundary')) is not bool:
                raise ValueError('unknown boundary schema')
            hosts = sorted({urlsplit(r['url']).hostname for r in requests[-1:] if r.get('url')})
            if state['boundary'] and not hosts:
                raise ValueError('latched source without attributable host')
            records.append(dict(path=path.relative_to(root).as_posix(), sha256=digest(raw),
                                boundary=state['boundary'], hosts=hosts if state['boundary'] else [],
                                reason=state.get('stop_reason'), counters={k: state.get(k)
                                    for k in ['created_at', 'logical_requests', 'transport_attempts', 'attempts',
                                              'downloaded_bytes', 'bytes_read', 'budget_stop']}))
        except (ValueError, KeyError, TypeError) as error:
            errors.append(dict(path=path.relative_to(root).as_posix(), error=str(error)))
    return dict(records=records, errors=errors,
                blocked_hosts=sorted({h for r in records if r['boundary'] for h in r['hosts']}))


def cache_inventory(root, config):
    by_url, errors = defaultdict(list), []
    for relative in config['cache_receipt_roots']:
        for receipt in sorted(inside(root, relative).rglob('*.receipt.json')):
            r = read(receipt)
            if r.get('http_status') != 200 or not r.get('sha256') or not r.get('url'):
                continue
            uri = urlsplit(r['url'])
            if uri.hostname not in ('apiweb.cafef.vn', 'cafef.vn'):
                continue
            if uri.hostname == 'cafef.vn' and uri.path != '/du-lieu/ajax/ajaxcongbothongtin.ashx':
                continue
            try:
                path = inside(root, r['path']) if r.get('path') else receipt.parent / r['name']
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError('cache escaped root')
                if digest(path.read_bytes()) != r['sha256']:
                    raise ValueError('raw hash mismatch')
                by_url[r['url']].append(dict(path=path.relative_to(root).as_posix(), sha256=r['sha256'],
                    receipt=receipt.relative_to(root).as_posix(), receipt_sha256=digest(receipt.read_bytes())))
            except (ValueError, KeyError, FileNotFoundError) as error:
                errors.append(dict(receipt=receipt.relative_to(root).as_posix(), error=str(error)))
    return dict(urls=dict(by_url), errors=errors)


def prepare(root, config):
    validate(config)
    run = inside(root, config['output_root'], 'data')
    registry = inside(root, config['registry'])
    raw_registry = registry.read_bytes()
    if digest(raw_registry) != config['registry_sha256']:
        raise ValueError('registry changed; explicit successor assignment required')
    selected = []
    with registry.open(encoding='utf-8-sig', newline='') as stream:
        for r in csv.DictReader(stream):
            if r['ticker'] in config['symbols']:
                selected.append(dict(registry_id=r['registry_id'], symbol=r['ticker'], exchange=r['exchange'],
                    provider_partition='UNRESOLVED:' + r['registry_id'], issuer_id=r['issuer_id'] or None,
                    historical_identity_ready=False, acquisition_only=True))
    if len(selected) != 5 or len({r['symbol'] for r in selected}) != 5:
        raise ValueError('pilot membership ambiguous or absent')
    run.mkdir(parents=True, exist_ok=True)
    with exclusive(run):
        write(run / 'config.json', config)
        code = {p: digest(inside(root, p).read_bytes()) for p in IMPLEMENTATION}
        if (run / 'contract.json').exists():
            contract = read(run / 'contract.json')
            if contract['code_pins'] != code:
                raise ValueError('implementation changed; do not resume frozen run')
        else:
            contract = dict(version=VERSION, created_at=datetime.now(timezone.utc).timestamp(),
                            registry_sha256=config['registry_sha256'], code_pins=code,
                            selected=selected, **CLOSED)
            write(run / 'contract.json', contract)
        if not (run / 'cache-index.json').exists():
            write(run / 'cache-index.json', cache_inventory(root, config))
        if not (run / 'source-boundaries.json').exists():
            write(run / 'source-boundaries.json', audit_boundaries(root, config, run))
        write(run / 'task-plan.json', tasks(config))
        from .financial_cafef_pilot import FAMILIES, required_keys
        write(run / 'dependencies.json', {family: sorted(required_keys(family)) for family in FAMILIES})
        for name in ('receipts', 'raw', 'network', 'reports'):
            (run / name).mkdir(exist_ok=True)
        sealed_names = ['config.json','contract.json','cache-index.json','source-boundaries.json','task-plan.json','dependencies.json']
        frozen = {name:digest((run/name).read_bytes()) for name in sealed_names}
        write(run / 'preparation-manifest.json', frozen)
        # A new/changed legacy journal must not silently evade the imported latch.
        fresh = audit_boundaries(root, config, run)
        if fresh != read(run / 'source-boundaries.json'):
            raise ValueError('legacy boundary inventory changed; review successor before network')
    return run


class HistoryTransport(CompactTrialTransport):
    def __init__(self, root, output, config, **kwargs):
        self.old = read_compact(output) if (output / 'transport.jsonl').exists() else None
        if self.old and self.old['torn_tail_bytes']:
            raise ValueError('torn journal requires explicit recovery')
        super().__init__(root, output, config,
                         resume_state=self.old['state'] if self.old else None, **kwargs)

    def event(self, action, **detail):
        if action == 'START_OR_RESUME' and self.old:
            self.index, self.previous = self.old['events'], self.old['last_sha256']
        return super().event(action, **detail)


def parse_task(root, task, record):
    body = inside(root, record['path']).read_bytes()
    if digest(body) != record['sha256']:
        raise EvidenceIntegrityError('raw hash mismatch')
    if task['kind'] == 'DISCLOSURE':
        return disclosures(body, task['symbol'])
    cells = parse_report(body, task['symbol'], task['statement'], task['mode'], record['sha256'])
    # Decimal provider tokens stay exact as strings; raw JSON bytes remain pinned.
    cells = json.loads(json.dumps(cells, default=str))
    return [dict(r, source_path=record['path'], source_sha256=record['sha256'],
                 fiscal_scope_status='REVIEW_REQUIRED', accepted=False, pit_ready=False)
            for r in cells if r['group'] == task['group']]


def page_state(task, rows, previous):
    """Detect silent page repeats independently for each group/mode/issuer."""
    if not rows:
        return dict(stop=True, reason='SOURCE_EXHAUSTED', fingerprint=None, oldest=None)
    if task['kind'] == 'DISCLOSURE':
        keys = sorted(str(r['provider_id']) for r in rows)
        oldest = None
    else:
        keys = sorted({(r['year'], r['quarter'], r.get('provider_type')) for r in rows}, key=str)
        oldest = min((r['year'] * 4 + (r['quarter'] or 0)) for r in rows)
    fingerprint = digest(encoded(keys))
    if previous and (fingerprint in {p['fingerprint'] for p in previous} or
                     (oldest is not None and previous[-1]['oldest'] is not None and
                      oldest >= previous[-1]['oldest'])):
        return dict(stop=True, reason='PAGINATION_NON_PROGRESS', fingerprint=fingerprint, oldest=oldest)
    target = (2012 if task['statement'] == 'CDKT' and task['mode'] == 'NAM' else 2013) * 4
    if task['mode'] == 'QUY':
        target += 1
    reached = oldest is not None and oldest <= target
    return dict(stop=reached, reason='TARGET_BOUNDARY_REACHED' if reached else 'CONTINUE',
                fingerprint=fingerprint, oldest=oldest)


def regression(root, config, run):
    from .financial_pilot_completion import verify
    result = verify(root, config['baseline_result'])
    if result['completed'] != 29 or result['target'] != 30:
        raise ValueError('pilot5 regression changed')
    write(run / 'regression.json', dict(status='PASS', completed=29, target=30,
          baseline=config['baseline_result'], metric_sha256=digest(
              (inside(root, config['baseline_result']) / 'metrics.csv').read_bytes()), **CLOSED))
    return result


def acquire(root, config, run, network, max_network_requests, *, transport_factory=HistoryTransport):
    tasks_ = read(run / 'task-plan.json')
    cache = read(run / 'cache-index.json')
    boundary = read(run / 'source-boundaries.json')
    if cache['errors'] or boundary['errors']:
        raise ValueError('cache/boundary audit errors require review')
    contract = read(run / 'contract.json')
    if datetime.now(timezone.utc).timestamp() > contract['created_at'] + 90 * 86400:
        raise ValueError('absolute campaign deadline reached')
    requests = 0
    states, stopped = defaultdict(list), set()
    transport = None
    with exclusive(run):
        for task in tasks_:
            receipt_path = run / 'receipts' / (task['id'] + '.json')
            if receipt_path.exists():
                receipt = read(receipt_path)
            elif task['series'] in stopped:
                receipt = dict(task=task, status='NOT_REQUIRED_AFTER_SERIES_STOP')
                write(receipt_path, receipt)
            else:
                if task['page'] > 1 and len(states[task['series']]) != task['page'] - 1:
                    continue  # Never request a later page while its predecessor is pending.
                records = cache['urls'].get(task['url'], [])
                if len({r['sha256'] for r in records}) > 1:
                    receipt = dict(task=task, status='CACHE_VINTAGE_CONFLICT', alternatives=records)
                elif records:
                    receipt = dict(task=task, status='CACHED', record=records[0])
                elif urlsplit(task['url']).hostname in boundary['blocked_hosts']:
                    receipt = dict(task=task, status='ACCESS_BLOCKED_IMPORTED')
                elif not network or requests >= max_network_requests:
                    continue  # Pending tasks remain resumable, never called missing data.
                elif task['kind'] != 'REPORT':
                    receipt = dict(task=task, status='METADATA_NETWORK_NOT_ENABLED')
                else:
                    if transport is None:
                        if shutil.disk_usage(root).free < 30_000_000_000:
                            raise TrialBudgetError('DISK_FLOOR')
                        transport = transport_factory(root, run / 'network', config)
                    old_requests = [r for r in transport.state['requests'].values() if r['url'] == task['url']]
                    if old_requests:
                        raise ValueError('interrupted request without receipt; explicit recovery required')
                    transport.context = dict(kind='structured', symbol=task['symbol'], report=task['statement'],
                                             page=task['page'])
                    try:
                        body, status = transport.get(task['url'])
                        requests += 1
                        path = run / 'raw' / (digest(body) + '.json')
                        if path.exists():
                            if digest(path.read_bytes()) != digest(body): raise ValueError('raw object changed')
                        else:
                            immutable_write(path, body)
                        receipt = dict(task=task, status='ACQUIRED', record=dict(
                            path=path.relative_to(root).as_posix(), sha256=digest(body), http_status=status))
                    except (AccessControlError, RateLimitError, TrialBudgetError) as error:
                        write(receipt_path, dict(task=task, status='ACCESS_OR_BUDGET_STOP', error=str(error)))
                        break
                    except ValueError as error:
                        requests += 1
                        receipt = dict(task=task, status='REQUEST_FAILED', error=str(error))
                write(receipt_path, receipt)
            if receipt.get('record'):
                try:
                    rows = parse_task(root, task, receipt['record'])
                    state = page_state(task, rows, states[task['series']])
                    states[task['series']].append(state)
                    if state['stop']: stopped.add(task['series'])
                except EvidenceIntegrityError:
                    raise
                except (ValueError, KeyError, TypeError):
                    stopped.add(task['series'])
            elif receipt['status'] not in ('NOT_REQUIRED_AFTER_SERIES_STOP',):
                stopped.add(task['series'])
    return dict(network_logical_requests_this_call=requests)


def build_report(root, config, run):
    cells, documents, anomalies, statuses = [], [], [], Counter()
    task_rows = []
    histories = defaultdict(list)
    for task in read(run / 'task-plan.json'):
        p = run / 'receipts' / (task['id'] + '.json')
        receipt = read(p) if p.exists() else dict(status='PENDING')
        status = receipt['status']
        record = receipt.get('record')
        if record:
            try:
                rows = parse_task(root, task, record)
                state = page_state(task, rows, histories[task['series']])
                histories[task['series']].append(state)
                if state['reason'] == 'PAGINATION_NON_PROGRESS':
                    anomalies.append(dict(symbol=task['symbol'], task_id=task['id'], reason=state['reason']))
                if task['kind'] == 'REPORT': cells.extend(rows)
                else:
                    documents.extend(dict(r, source_path=record['path'], source_sha256=record['sha256'],
                                          publication_status='PROVIDER_DATE_CANDIDATE_NOT_PIT_VERIFIED') for r in rows)
            except EvidenceIntegrityError:
                raise
            except (ValueError, KeyError, TypeError) as error:
                status = 'PARSE_ERROR'
                anomalies.append(dict(symbol=task['symbol'], task_id=task['id'], reason=str(error)))
        statuses[status] += 1
        task_rows.append(dict(task, status=status))
    # Preserve conflicting vintages, only remove exact observation duplicates.
    unique = {digest(encoded(r)): r for r in cells}
    cells = list(unique.values())
    coverage = []
    index = defaultdict(list)
    for r in cells:
        if r['value'] is not None:
            index[(r['symbol'], r['statement'], r['mode'], r['year'], r['quarter'])].append(r)
    for symbol in config['symbols']:
        for year in config['years']:
            for mode, quarters in [('NAM', [0]), ('QUY', [1, 2, 3, 4])]:
                for q in quarters:
                    for statement, groups in GROUPS.items():
                        found = index.get((symbol, statement, mode, year, q), [])
                        observed = {r['group'] for r in found}
                        status = ('CANDIDATE_GROUPS_PRESENT' if observed >= set(groups) else
                                  'PARTIAL_CANDIDATE_GROUPS' if found else 'NO_CANDIDATE_IN_ACQUIRED_PAGES')
                        coverage.append(dict(symbol=symbol, year=year, quarter=q, mode=mode, statement=statement,
                            numeric_cells=len(found), observed_groups=sorted(observed), status=status,
                            unit_status='UNVERIFIED', accepted=False, pit_ready=False))
        found = index.get((symbol, 'CDKT', 'NAM', 2012, 0), [])
        coverage.append(dict(symbol=symbol, year=2012, quarter=0, mode='NAM', statement='CDKT',
            numeric_cells=len(found), observed_groups=sorted({r['group'] for r in found}),
            status='AUXILIARY_CANDIDATES_PRESENT' if found else 'AUXILIARY_NOT_ACQUIRED',
            unit_status='UNVERIFIED', accepted=False, pit_ready=False))
    for r in cells:
        if r['mapping_status'] == 'UNMAPPED_TEMPLATE':
            anomalies.append(dict(symbol=r['symbol'], task_id=r['source_id'], reason='UNMAPPED_TEMPLATE_CODE'))
    from .financial_cafef_pilot import FAMILIES, required_keys
    missing_inputs = [dict(symbol=symbol, year=year, family=family,
        required_field_periods=[dict(field=f,year=year+offset) for f,offset in sorted(required_keys(family))],
        reason='ACCEPTED_HISTORY_FACTS_AND_AVAILABILITY_REQUIRED',
        valuation_reason='HISTORICAL_PRICE_AND_SHARE_BASIS_REQUIRED' if family in ('PE','PB') else '',
        baseline_scope='FY2025_ONLY_SEPARATE_REFERENCE' if year==2025 else '')
        for symbol in config['symbols'] for year in config['years'] for family in FAMILIES]
    ledger = read_compact(run / 'network') if (run / 'network/transport.jsonl').exists() else None
    summary = dict(version=VERSION, status='PARTIAL', stage='F2_HISTORY_CANDIDATES',
        symbols=config['symbols'], target_years=config['years'], candidate_cells=len(cells),
        coverage_slots=len(coverage), coverage_statuses=dict(Counter(r['status'] for r in coverage)),
        task_statuses=dict(statuses), disclosure_candidates=len(documents), anomalies=len(anomalies),
        accepted_new_facts=0, baseline_reference_metrics=29, baseline_target=30,
        historical_identity_status='PROVISIONAL_PROVIDER_PARTITIONS',
        counters={k:v for k,v in ledger['state'].items() if k not in ('requests','cache')} if ledger else {}, **CLOSED)
    manifest_receipts = {p.relative_to(run).as_posix():digest(p.read_bytes())
                         for p in sorted((run / 'receipts').glob('*.json'))}
    report_id = digest(encoded(manifest_receipts))[:20]
    out = run / 'reports' / report_id
    out.mkdir(exist_ok=True)
    files = {
        'summary.json': encoded(summary),
        'candidates.jsonl': b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,
            separators=(',',':'),allow_nan=False)+'\n').encode('utf-8') for r in cells),
        'financial_coverage.csv': csv_bytes(coverage, ['symbol','year','quarter','mode','statement','numeric_cells',
            'observed_groups','status','unit_status','accepted','pit_ready']),
        'tasks.csv': csv_bytes(task_rows, ['id','symbol','statement','mode','group','page','status','url']),
        'anomalies.csv':csv_bytes(anomalies,['symbol','task_id','reason']),
        'missing_inputs.csv':csv_bytes(missing_inputs,['symbol','year','family','required_field_periods','reason','valuation_reason','baseline_scope']),
        'document_queue.json':encoded(documents),
        'receipt-pins.json':encoded(manifest_receipts),
        'metrics.csv':(inside(root, config['baseline_result'])/'metrics.csv').read_bytes(),
        'report.md': ('# Financial history pilot5\n\n**PARTIAL — candidates, chưa phải accepted history/PIT.**\n\n'
            f'{len(cells)} candidate cells; {len(documents)} disclosure candidates; '
            f'{statuses["PENDING"]} tasks pending.\n\n'
            'Các khoảng trống xem financial_coverage.csv và tasks.csv; chưa kết luận nguồn không công bố.\n'
            'metrics.csv chỉ là pinned FY2025 baseline 29/30, không phải chỉ số tính mới cho toàn lịch sử.\n'
            'Source units/scope/vintage, accounting QA và PDF review còn cần trước acceptance.\n').encode('utf-8')}
    for name, body in files.items():
        p = out / name
        if p.exists():
            if p.read_bytes() != body: raise ValueError('immutable report differs')
        else: immutable_write(p, body)
    write(out / 'manifest.json', {name:digest(body) for name,body in files.items()})
    return dict(summary, output=out.relative_to(root).as_posix())


def verify_report(root, run, result):
    folder = inside(root, result)
    if not folder.is_relative_to(run / 'reports'):
        raise ValueError('result outside history campaign')
    for name, sha in read(folder / 'manifest.json').items():
        if Path(name).name != name or digest((folder / name).read_bytes()) != sha:
            raise ValueError('report hash mismatch: ' + name)
    for path, sha in read(folder / 'receipt-pins.json').items():
        if digest(inside(run, path).read_bytes()) != sha:
            raise ValueError('receipt changed')
        record=read(inside(run,path)).get('record')
        if record and digest(inside(root,record['path']).read_bytes()) != record['sha256']:
            raise EvidenceIntegrityError('raw cache changed')
    summary = read(folder / 'summary.json')
    if any(summary.get(k) is not False for k in CLOSED): raise ValueError('gate changed')
    return dict(status='VERIFIED', output=result, candidate_cells=summary['candidate_cells'], **CLOSED)


def main(root, config_path, action, network=False, max_network_requests=25):
    root = Path(root)
    if type(max_network_requests) is not int or not 0 <= max_network_requests <= 1600:
        raise ValueError('network request wave outside 0..1600')
    config = validate(read(inside(root, config_path)))
    run = prepare(root, config)
    if action == 'doctor':
        boundary = read(run / 'source-boundaries.json')
        cache = read(run / 'cache-index.json')
        return dict(status='PASS' if not boundary['errors'] and not cache['errors'] else 'FAIL_CLOSED',
                    frozen_members=5, cache_urls=len(cache['urls']), blocked_hosts=boundary['blocked_hosts'],
                    boundary_errors=boundary['errors'], cache_errors=cache['errors'],
                    tesseract=shutil.which('tesseract'), network_enabled=network, **CLOSED)
    if action == 'plan':
        return dict(status='F0_PREPARED', tasks=len(tasks(config)), output=str(run), **CLOSED)
    if action == 'regression':
        return regression(root, config, run)
    if action in ('run', 'resume'):
        regression(root, config, run)
        acquire(root, config, run, network, max_network_requests)
    if action in ('run','resume','qa','report','verify'):
        result = build_report(root, config, run)
        if action == 'verify':
            return verify_report(root, run, result['output'])
        return result
    raise ValueError('unsupported action')
