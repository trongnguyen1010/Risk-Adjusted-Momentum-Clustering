"""Selective primary PDF supplement with inherited counters and immutable evidence."""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import CompactTrialTransport, read_compact
from .financial_history_pit import audit_boundaries
from .financial_user_workflow import exclusive

VERSION = 'financial-history-documents-v1'
CODE = ['src/delta_t1/experiments/financial_history_documents.py',
        'scripts/financial_history_documents.py', 'scripts/financial_history_documents.ps1',
        'src/delta_t1/ingestion/financial_compact_trial.py',
        'src/delta_t1/ingestion/financial_trial_transport.py',
        'src/delta_t1/ingestion/financial_batch_evidence.py',
        'src/delta_t1/ingestion/sources/base.py',
        'src/delta_t1/experiments/financial_history_pit.py']


def read(path):
    return json.loads(path.read_bytes())


def put(path, value):
    raw = value if isinstance(value, bytes) else encoded(value)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable artifact differs: ' + str(path))
    else:
        immutable_write(path, raw)


class DocumentTransport(CompactTrialTransport):
    def __init__(self, root, output, config, seed, **kwargs):
        output.mkdir(parents=True, exist_ok=True)
        self.old = read_compact(output) if (output / 'transport.jsonl').exists() else None
        if self.old and self.old['torn_tail_bytes']:
            raise ValueError('torn journal requires explicit review')
        super().__init__(root, output, config, resume_state=self.old['state'] if self.old else seed, **kwargs)

    def event(self, action, **detail):
        if action == 'START_OR_RESUME' and self.old:
            self.index, self.previous = self.old['events'], self.old['last_sha256']
        return super().event(action, **detail)


def prepare(root, config_path):
    config = read(inside(root, config_path))
    if config.get('version') != VERSION or len(config['jobs']) > 2:
        raise ValueError('bounded two-document supplement required')
    if config.get('accepted_facts_allowed') is not False or config.get('pit_allowed') is not False:
        raise ValueError('acquisition cannot accept facts/PIT')
    parent = inside(root, config['parent_network'])
    if digest((parent / 'transport.jsonl').read_bytes()) != config['parent_journal_sha256']:
        raise ValueError('parent journal changed')
    old = read_compact(parent)
    if old['torn_tail_bytes'] or old['state']['boundary'] or old['state']['budget_stop']:
        raise ValueError('parent is not safely inheritable')
    b = config['budgets']
    caps = dict(max_logical_requests=old['state']['logical_requests'] + 2,
                max_transport_attempts=old['state']['transport_attempts'] + 4,
                max_pdf_download_attempts=old['state']['pdf_download_attempts'] + 4,
                max_response_bytes=25_000_000, max_total_downloaded_bytes=old['state']['downloaded_bytes'] + 50_000_000,
                max_wall_seconds=259200, max_attempts_per_request=2, timeout_seconds=25)
    for key, cap in caps.items():
        if type(b.get(key)) is not int or not 1 <= b[key] <= cap:
            raise ValueError('invalid budget: ' + key)
    if b['min_seconds_between_transport_attempts'] < 2 or not 1 <= config['text_page_cap'] <= 160:
        raise ValueError('invalid spacing/text budget')
    for job in config['jobs']:
        if urlsplit(job['url']).hostname not in config['approved_hosts']:
            raise ValueError('unapproved primary host')
    out = inside(root, config['output_root'])
    out.mkdir(parents=True, exist_ok=True)
    contract_path = out / 'contract.json'
    pins = {p: digest(inside(root, p).read_bytes()) for p in CODE + [config_path]}
    if contract_path.exists():
        contract = read(contract_path)
        if contract['pins'] != pins:
            raise ValueError('frozen supplement code/config changed')
        for item in contract['boundaries']['records']:
            if digest(inside(root, item['path']).read_bytes()) != item['sha256']:
                raise ValueError('imported boundary journal changed')
    else:
        boundaries = audit_boundaries(root, {'boundary_roots': config['boundary_roots']}, out)
        if boundaries['errors']:
            raise ValueError('boundary audit failed')
        contract = dict(version=VERSION, pins=pins, boundaries=boundaries,
                        parent_network=config['parent_network'], seed=copy.deepcopy(old['state']))
        put(contract_path, contract)
    return config, out, contract


def acquire(root, config, out, contract):
    transport = None
    for job in config['jobs']:
        receipt = out / 'receipts' / (job['id'] + '.json')
        if receipt.exists():
            continue
        if urlsplit(job['url']).hostname in contract['boundaries']['blocked_hosts']:
            put(receipt, dict(job=job, status='IMPORTED_SOURCE_BOUNDARY'))
            continue
        if transport is None:
            transport = DocumentTransport(root, out / 'network', config, contract['seed'])
        prior = [v for v in transport.state['requests'].values() if v['url'] == job['url']]
        if prior:
            raise ValueError('previous request without terminal receipt; do not retry automatically')
        transport.context = dict(kind='pdf', symbol=job['symbol'], year=job['year'], report=job['id'])
        try:
            body, status = transport.get(job['url'])
            if not body.startswith(b'%PDF-'):
                raise ValueError('not a PDF response')
            path = out / 'pdf' / (job['id'] + '.pdf')
            put(path, body)
            put(receipt, dict(job=job, status='ACQUIRED', http_status=status,
                path=path.relative_to(root).as_posix(), sha256=digest(body), bytes=len(body),
                publication_evidence='UNKNOWN_NOT_INFERRED_FROM_URL', accepted=False, pit_ready=False))
        except Exception as error:
            put(receipt, dict(job=job, status='FAILED_OR_STOPPED', reason=str(error), accepted=False))
            if transport.state['boundary'] or transport.state['budget_stop']:
                break


def extract(root, config, out):
    # Reservations survive timeouts/crashes. A completed task is never extracted twice.
    for job in config['jobs']:
        rp = out / 'receipts' / (job['id'] + '.json')
        target = out / 'text' / (job['id'] + '.json')
        if not rp.exists() or read(rp)['status'] != 'ACQUIRED' or target.exists():
            continue
        receipt = read(rp)
        pdf = inside(root, receipt['path'])
        if digest(pdf.read_bytes()) != receipt['sha256']:
            raise ValueError('PDF changed')
        reserve = out / 'text-reservations' / (job['id'] + '.json')
        if reserve.exists():
            raise ValueError('interrupted text task requires review, no automatic budget reset')
        used = sum(read(p)['charged_pages'] for p in (out / 'text-reservations').glob('*.json'))
        limit = min(75, config['text_page_cap'] - used)
        if limit <= 0:
            break
        put(reserve, dict(charged_pages=limit, pdf_sha256=receipt['sha256']))
        command = [sys.executable, str(root / 'scripts/financial_history_documents.py'), 'extract-worker',
                   '--pdf', str(pdf), '--limit', str(limit)]
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=120)
            if result.returncode:
                raise ValueError(result.stderr.decode('utf-8', errors='replace')[-1000:])
            value = json.loads(result.stdout)
            put(target, dict(**value, pdf_sha256=receipt['sha256'], accepted=False, pit_ready=False))
        except Exception as error:
            put(out / 'text-errors' / (job['id'] + '.json'), dict(reason=str(error), reservation_retained=True))


def report(root, config, out, action):
    products = {}
    for path in (out / 'receipts').glob('*.json'):
        receipt = read(path)
        if receipt['status'] == 'ACQUIRED' and digest(inside(root, receipt['path']).read_bytes()) != receipt['sha256']:
            raise ValueError('acquired PDF hash mismatch')
    for folder in ['receipts', 'pdf', 'text', 'text-reservations', 'text-errors']:
        for path in sorted((out / folder).glob('*')):
            products[path.relative_to(out).as_posix()] = digest(path.read_bytes())
    network = out / 'network'
    ledger = read_compact(network) if (network / 'transport.jsonl').exists() else None
    summary = dict(status='PARTIAL', documents_acquired=sum(read(p)['status'] == 'ACQUIRED' for p in (out / 'receipts').glob('*.json')),
        inherited_counters=True, counters=ledger['state'] if ledger else None,
        text_documents=sum(1 for _ in (out / 'text').glob('*.json')), new_accepted_facts=0, new_pit_facts=0,
        financial_features_allowed=False, batch20_allowed=False)
    if ledger:
        summary['counters'] = {k: v for k, v in ledger['state'].items() if k not in ['requests', 'cache']}
        products['network/transport.jsonl'] = digest((network / 'transport.jsonl').read_bytes())
    products['contract.json'] = digest((out / 'contract.json').read_bytes())
    snapshot = out / 'results' / digest(encoded(products))[:20]
    if action == 'verify':
        if read(snapshot / 'manifest.json') != products or read(snapshot / 'summary.json') != summary:
            raise ValueError('supplement snapshot differs')
    else:
        put(snapshot / 'manifest.json', products)
        put(snapshot / 'summary.json', summary)
    return dict(status='VERIFIED' if action == 'verify' else 'PARTIAL', output=snapshot.relative_to(root).as_posix(), **{k:v for k,v in summary.items() if k!='status'})


def cli(root):
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'run', 'extract', 'verify', 'extract-worker'])
    p.add_argument('--config', default='configs/data/financial_history_documents_v1.json')
    p.add_argument('--network', action='store_true')
    p.add_argument('--pdf'); p.add_argument('--limit', type=int, default=75)
    args = p.parse_args()
    try:
        if args.action == 'extract-worker':
            from pypdf import PdfReader
            reader = PdfReader(args.pdf)
            pages = [dict(page=i+1, text=reader.pages[i].extract_text() or '') for i in range(min(len(reader.pages), args.limit))]
            print(json.dumps(dict(page_count=len(reader.pages), extracted_pages=pages), ensure_ascii=True))
            return
        config, out, contract = prepare(root, args.config)
        with exclusive(out):
            if args.action == 'run' and args.network:
                acquire(root, config, out, contract)
            if args.action == 'extract':
                extract(root, config, out)
            print(json.dumps(report(root, config, out, args.action), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED', reason=str(error)), ensure_ascii=False))
        raise SystemExit(2)
