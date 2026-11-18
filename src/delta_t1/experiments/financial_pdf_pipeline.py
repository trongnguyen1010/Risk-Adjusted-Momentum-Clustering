"""Durable PDF pilot: source -> cache -> acquire -> text -> review/OCR queue."""
import argparse
import copy
import csv
import io
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from .financial_history_documents import put, read, DocumentTransport
from .financial_user_workflow import exclusive
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from ..ingestion.financial_pdf_flow import annual_links, extraction_state

VERSION = 'financial-pdf-pipeline-v1'
CODE = ['src/delta_t1/experiments/financial_pdf_pipeline.py', 'src/delta_t1/ingestion/financial_pdf_flow.py',
        'scripts/financial_pdf_pipeline.py', 'scripts/financial_pdf_pipeline.ps1',
        'src/delta_t1/experiments/financial_history_documents.py', 'src/delta_t1/ingestion/financial_compact_trial.py',
        'src/delta_t1/ingestion/financial_trial_transport.py', 'src/delta_t1/ingestion/financial_batch_evidence.py',
        'src/delta_t1/experiments/financial_user_workflow.py', 'src/delta_t1/ingestion/cafef_financial.py']


def file_hash(path):
    import hashlib
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_journal(path):
    """Streaming compact-chain replay, including request snapshots and counters."""
    import hashlib
    previous, count, requests, cache, state = None, 0, {}, {}, None
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for line in stream:
            hasher.update(line)
            if not line.endswith(b'\n'):
                raise ValueError('torn journal')
            e = json.loads(line)
            if e['index'] != count+1 or e['previous_sha256'] != previous:
                raise ValueError('journal chain changed')
            state = e['state']; detail = e['detail']
            requests.update(state.get('requests', {})); cache.update(state.get('cache', {}))
            if detail.get('request_key') and detail.get('request_snapshot'):
                requests[detail['request_key']] = detail['request_snapshot']
            if e['action'] == 'CACHE_COMMIT':
                cache[detail['url']] = detail['record']
            count += 1; previous = digest(line.rstrip(b'\n'))
    if state is None or state['logical_requests'] != len(requests) or state['transport_attempts'] != sum(r['attempts'] for r in requests.values()):
        raise ValueError('journal counters changed')
    return dict(state=dict(state, requests=requests, cache=cache), sha256=hasher.hexdigest())


class PipelineTransport(DocumentTransport):
    def __init__(self, *args, batch_deadline, campaign_deadline, **kwargs):
        self.batch_deadline, self.campaign_deadline = batch_deadline, campaign_deadline
        super().__init__(*args, **kwargs)

    def remaining_seconds(self):
        return max(0, min(super().remaining_seconds(), self.batch_deadline-self.utc(), self.campaign_deadline-self.utc()))


def prepare(root, config_path):
    c = read(inside(root, config_path)); out = inside(root, c['output_root'])
    if c['version'] != VERSION or c.get('accepted_facts_allowed') is not False or c.get('research_promotion_allowed') is not False:
        raise ValueError('candidate-only pipeline contract required')
    if c['pdf_cap'] != 10 or c['concurrency'] != 1 or c['budgets']['min_seconds_between_transport_attempts'] < 2:
        raise ValueError('approved pilot10 limits required')
    if c['budgets']['max_attempts_per_request'] != 2 or c['budgets']['max_response_bytes'] > 25_000_000:
        raise ValueError('attempt/response cap changed')
    if c['batch_deadline'] != c['batch_created_at']+259200 or c['campaign_deadline'] > c['campaign_created_at']+90*86400:
        raise ValueError('deadline reset')
    pins = {}
    def pin(path, expected=None):
        sha = file_hash(inside(root, path))
        if expected is not None and expected != sha:
            raise ValueError('source changed: '+path)
        pins[path] = sha
    for path in CODE+[config_path]:
        pin(path)
    pin(c['parent_journal']['path'], c['parent_journal']['sha256'])
    pin(c['boundary_snapshot']['path'], c['boundary_snapshot']['sha256'])
    pin(c['pdf_inventory'], c['pdf_inventory_sha256'])
    batch = c['batch100']; pin(batch['path'], batch['sha256'])
    expected = [(r['registry_id'], r['symbol'], r['missing_years'][0]) for r in read(inside(root, batch['path']))[:10]]
    if [(r['registry_id'], r['symbol'], r['year']) for r in c['targets']] != expected:
        raise ValueError('pilot membership changed')
    out.mkdir(parents=True, exist_ok=True)
    if (out/'contract.json').exists():
        contract = read(out/'contract.json')
        if contract['pins'] != pins:
            raise ValueError('frozen pipeline inputs changed')
        for path, sha in contract['boundary_pins'].items():
            if file_hash(inside(root, path)) != sha:
                raise ValueError('imported boundary changed')
        return c, out, contract
    seed = load_journal(inside(root, c['parent_journal']['path']))['state']
    if seed['boundary'] or seed['budget_stop'] or seed['reserved_bytes']:
        raise ValueError('unsafe counter parent')
    # Pin the snapshot importing all earlier host latches. Any later journal must also be inspected.
    spec = c['boundary_snapshot']
    snapshot = read(inside(root, spec['path']))['boundaries']
    if snapshot['errors']:
        raise ValueError('boundary snapshot errors')
    boundary_pins = {r['path']: r['sha256'] for r in snapshot['records']}
    blocked = set(snapshot['blocked_hosts'])
    for base in c['boundary_roots']:
        for path in inside(root, base).rglob('transport.jsonl'):
            if path.is_relative_to(out):
                continue
            rel = path.relative_to(root).as_posix()
            if rel in boundary_pins:
                if file_hash(path) != boundary_pins[rel]:
                    raise ValueError('boundary journal changed: '+rel)
                continue
            ledger = load_journal(path); boundary_pins[rel] = ledger['sha256']
            state = ledger['state']
            if state['boundary']:
                hosts = {urlsplit(r['url']).hostname for r in list(state['requests'].values())[-1:]}
                if not hosts or None in hosts:
                    raise ValueError('unattributed source boundary')
                blocked.update(hosts)
    b = c['budgets']
    for key, extra in [('max_logical_requests', 40), ('max_transport_attempts', 80), ('max_pdf_download_attempts', 20), ('max_total_downloaded_bytes', 300_000_000)]:
        counter = {'max_logical_requests':'logical_requests', 'max_transport_attempts':'transport_attempts', 'max_pdf_download_attempts':'pdf_download_attempts', 'max_total_downloaded_bytes':'downloaded_bytes'}[key]
        if not seed[counter] <= b[key] <= seed[counter]+extra:
            raise ValueError('pilot cumulative budget changed')
    if seed['pdf_download_attempts']+20 > 2000 or shutil.disk_usage(root).free < 30_000_000_000:
        raise ValueError('campaign PDF/disk budget closed')
    contract = dict(version=VERSION, pins=pins, boundary_pins=boundary_pins, blocked_hosts=sorted(blocked), seed=seed,
        batch_created_at=c['batch_created_at'], campaign_created_at=c['campaign_created_at'],
        approval='OWNER_APPROVED_BATCH100_AND_REUSABLE_PILOT10_FLOW', automatic_acceptance=False)
    put(out/'contract.json', contract)
    return c, out, contract


def index_cache(root, inventory_path):
    """Resolve anonymous raw.pdf files by their acquisition metadata, not filename."""
    index, unknown = {}, []
    rows = list(csv.DictReader(io.StringIO(inside(root, inventory_path).read_text(encoding='utf-8-sig'))))
    for row in rows:
        p = inside(root, row['path']); matched = False
        candidates = list(p.parent.glob('*.receipt.json'))
        if (p.parent/'result.json').exists():
            candidates.append(p.parent/'result.json')
        # Document supplements store a sibling receipts folder and exact job/PDF id.
        rp = p.parent.parent/'receipts'/(p.stem+'.json')
        if rp.exists():
            candidates.append(rp)
        for metadata in candidates:
            record = read(metadata); payload = record.get('payload', record)
            url = (record.get('request') or record.get('job') or record).get('url')
            rawpath = payload.get('path')
            if url and rawpath and inside(root, rawpath).resolve() == p.resolve() and payload.get('sha256') == row['sha256']:
                index.setdefault(url, []).append(dict(path=row['path'], sha256=row['sha256'], metadata=metadata.relative_to(root).as_posix(), metadata_sha256=file_hash(metadata)))
                matched = True
        if not matched:
            unknown.append(row['path'])
    return dict(by_url=index, unknown_metadata=unknown, total_files=len(rows))


def request(root, out, c, contract, transport, url, kind, symbol, year):
    key = digest(encoded(dict(url=url, kind=kind))); receipt = out/'requests'/(key+'.json')
    if receipt.exists():
        r = read(receipt)
        if r.get('path') and file_hash(inside(root, r['path'])) != r['sha256']:
            raise ValueError('request cache changed')
        return r
    if urlsplit(url).hostname in contract['blocked_hosts']:
        result = dict(url=url, kind=kind, status='IMPORTED_SOURCE_BOUNDARY')
    elif urlsplit(url).hostname not in c['approved_hosts']:
        result = dict(url=url, kind=kind, status='UNAPPROVED_DESTINATION_REVIEW_REQUIRED')
    else:
        if any(r['url'] == url for r in transport.state['requests'].values()):
            # No retry after a crash between I/O and receipt commit, nor forgotten old failure.
            result = dict(url=url, kind=kind, status='PRIOR_REQUEST_WITHOUT_PIPELINE_RECEIPT_REVIEW_REQUIRED')
        else:
            transport.context = dict(kind=kind, symbol=symbol, year=year)
            original_cap = transport.b['max_response_bytes']
            original_timeout = transport.b['timeout_seconds']
            transport.b['max_response_bytes'] = original_cap if kind == 'pdf' else min(5_000_000, original_cap)
            transport.b['timeout_seconds'] = original_timeout if kind == 'pdf' else min(20, original_timeout)
            try:
                body, status = transport.get(url)
                if kind == 'pdf' and not body.startswith(b'%PDF-'):
                    raise ValueError('response is not PDF')
                suffix = '.pdf' if kind == 'pdf' else '.html'
                path = out/'raw'/(digest(body)+suffix); put(path, body)
                result = dict(url=url, kind=kind, status='ACQUIRED', http_status=status, path=path.relative_to(root).as_posix(), sha256=digest(body), bytes=len(body), accepted=False)
            except Exception as error:
                result = dict(url=url, kind=kind, status='FAILED_OR_STOPPED', reason=str(error), accepted=False)
            finally:
                transport.b['max_response_bytes'] = original_cap
                transport.b['timeout_seconds'] = original_timeout
    put(receipt, result)
    return result


def execute(root, c, out, contract, network):
    targets = c['targets']; cache = index_cache(root, c['pdf_inventory'])
    put(out/'cache-index.json', cache)
    transport = None
    if network:
        if time.time() >= min(c['batch_deadline'], c['campaign_deadline']):
            raise ValueError('batch/campaign deadline expired')
        transport = PipelineTransport(root, out/'network', c, contract['seed'], batch_deadline=c['batch_deadline'], campaign_deadline=c['campaign_deadline'])
    for target in targets:
        tid = target['symbol']+'-'+str(target['year'])
        terminal = out/'targets'/(tid+'.json')
        if terminal.exists():
            continue
        document = None; links = []; catalogues = target.get('catalogues', [])
        if not catalogues:
            put(terminal, dict(target=target, status='SOURCE_DISCOVERY_REQUIRED', accepted=False)); continue
        if not network:
            continue  # Offline status must not make a pending network task terminal.
        for url in catalogues:
            response = request(root, out, c, contract, transport, url, 'html', target['symbol'], target['year'])
            if response['status'] != 'ACQUIRED':
                continue
            text = inside(root, response['path']).read_text(encoding='utf-8', errors='replace')
            links.extend(dict(r, catalogue_path=response['path'], catalogue_sha256=response['sha256']) for r in annual_links(text, url, target['year'], target['source_scope_filter']))
        links = list({r['url']:r for r in links}.values())
        # Resolve only direct PDF anchors; ambiguous or detail-page links remain explicit review work.
        pdfs = [r for r in links if urlsplit(r['url']).path.lower().endswith('.pdf')]
        put(out/'discovery'/(tid+'.json'), dict(target=target, links=links, pdf_candidates=pdfs))
        if len(pdfs) != 1:
            put(terminal, dict(target=target, status='DOCUMENT_SELECTION_REVIEW_REQUIRED' if links else 'NO_ANNUAL_DOCUMENT_IN_OBSERVED_CATALOGUE', candidate_count=len(pdfs), accepted=False)); continue
        selected = pdfs[0]; matches = cache['by_url'].get(selected['url'], [])
        if len({r['sha256'] for r in matches}) > 1:
            put(terminal, dict(target=target, status='CACHE_VINTAGE_CONFLICT', accepted=False)); continue
        if matches:
            document = dict(matches[0], status='REUSED_CACHE', url=selected['url'])
            if file_hash(inside(root, document['path'])) != document['sha256']:
                raise ValueError('reused PDF changed')
        else:
            document = request(root, out, c, contract, transport, selected['url'], 'pdf', target['symbol'], target['year'])
        if document['status'] not in ['ACQUIRED', 'REUSED_CACHE']:
            put(terminal, dict(target=target, status='DOCUMENT_ACQUISITION_HELD', document=document, accepted=False)); continue
        reservation = out/'text-reservations'/(document['sha256']+'.json')
        extracted = out/'text'/(document['sha256']+'.json')
        if not extracted.exists():
            if reservation.exists():
                put(terminal, dict(target=target, status='INTERRUPTED_EXTRACTION_REVIEW_REQUIRED', document=document, accepted=False)); continue
            used = sum(read(p)['reserved_pages'] for p in (out/'text-reservations').glob('*.json'))
            if used+c['max_text_pages_per_pdf'] > c['max_text_pages_batch']:
                put(terminal, dict(target=target, status='DEFERRED_TEXT_BUDGET', document=document, accepted=False)); continue
            put(reservation, dict(pdf_sha256=document['sha256'], reserved_pages=c['max_text_pages_per_pdf']))
            try:
                completed = subprocess.run([sys.executable, str(root/'scripts/financial_pdf_pipeline.py'), 'extract-worker', '--pdf', str(inside(root, document['path'])), '--limit', str(c['max_text_pages_per_pdf'])], cwd=root, capture_output=True, timeout=120, check=True)
                value = json.loads(completed.stdout)
                put(extracted, dict(pdf_sha256=document['sha256'], **value))
            except Exception as error:
                put(terminal, dict(target=target, status='EXTRACTION_FAILED_RESERVATION_RETAINED', document=document, reason=str(error), accepted=False)); continue
        pages = read(extracted)['pages']; review = extraction_state(pages)
        put(out/'review'/(tid+'.json'), dict(target=target, document=document, text_path=extracted.relative_to(root).as_posix(), text_sha256=file_hash(extracted), **review))
        if review['low_text_pages'] or review['missing_candidate_fields']:
            put(out/'ocr-review'/(tid+'.json'), dict(target=target, pdf_path=document['path'], pdf_sha256=document['sha256'],
                low_text_pages=review['low_text_pages'], missing_candidate_fields=review['missing_candidate_fields'],
                status='EXPLICIT_PAGE_SELECTION_REQUIRED', automatic_whole_document_ocr_allowed=False,
                per_pdf_page_cap=40, campaign_config='configs/data/financial_ocr_campaign_v10.json', accepted=False))
        put(terminal, dict(target=target, status=review['status'], document=document, candidate_fields_found=review['candidate_fields_found'], low_text_pages=review['low_text_pages'], accepted=False))
        print(json.dumps(dict(symbol=target['symbol'], status=review['status'])), flush=True)


def snapshot(root, c, out, verify=False):
    inventory = {'contract.json': file_hash(out/'contract.json')}
    for folder in ['requests', 'raw', 'targets', 'discovery', 'text', 'text-reservations', 'review', 'ocr-review']:
        for p in sorted((out/folder).glob('*')):
            inventory[p.relative_to(out).as_posix()] = file_hash(p)
    if (out/'cache-index.json').exists():
        inventory['cache-index.json'] = file_hash(out/'cache-index.json')
    if (out/'network/transport.jsonl').exists():
        inventory['network/transport.jsonl'] = file_hash(out/'network/transport.jsonl')
    targets = [read(p) for p in (out/'targets').glob('*.json')]
    from collections import Counter
    summary = dict(status='PARTIAL_REAL_PILOT', targets=10, terminal_task_states=len(targets), status_counts=dict(Counter(r['status'] for r in targets)), pdfs_acquired=sum(r.get('document', {}).get('status')=='ACQUIRED' for r in targets), pdfs_reused=sum(r.get('document', {}).get('status')=='REUSED_CACHE' for r in targets), text_documents=len(list((out/'text').glob('*.json'))), ocr_pages_executed=0, reviewed_vectors_accepted=0, new_feature_rows=0, full10=463, strict_pit_ready=False, research_ready=False, next50_allowed=False)
    result = out/'results'/digest(encoded(inventory))[:20]
    if verify:
        if read(result/'manifest.json') != inventory or read(result/'summary.json') != summary:
            raise ValueError('pipeline snapshot changed')
    else:
        put(result/'manifest.json', inventory); put(result/'summary.json', summary)
    return dict(path=result.relative_to(root).as_posix(), summary=summary)


def cli(root):
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['prepare', 'run', 'status', 'verify', 'extract-worker'])
    p.add_argument('--config', default='configs/data/financial_pdf_pipeline_v1.json'); p.add_argument('--network', action='store_true')
    p.add_argument('--pdf'); p.add_argument('--limit', type=int)
    args = p.parse_args()
    if args.action == 'extract-worker':
        from pypdf import PdfReader
        reader = PdfReader(args.pdf)
        if reader.is_encrypted or len(reader.pages) > args.limit:
            raise ValueError('encrypted or excessive-page PDF requires review')
        print(json.dumps(dict(total_pages=len(reader.pages), pages=[dict(page=i+1, text=page.extract_text() or '') for i, page in enumerate(reader.pages)]), ensure_ascii=True)); return
    c, out, contract = prepare(root, args.config)
    with exclusive(out):
        if args.action == 'run':
            execute(root, c, out, contract, args.network)
        print(json.dumps(snapshot(root, c, out, args.action=='verify'), ensure_ascii=False))
