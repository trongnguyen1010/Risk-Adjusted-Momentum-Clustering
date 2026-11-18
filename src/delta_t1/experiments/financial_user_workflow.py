"""Local frozen50 work queue. Candidates and manual references never open gates."""
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from .financial_scale_analysis import candidate_math, hints
from .financial_scale_probe import CLOSED
from ..features.financial_reference import calculate
from ..features.financial_vas_reference import (M_FIELDS, calculate_disclosed_basic_eps,
    calculate_vas_f_score, calculate_vas_m_score)
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside, seal, validate_url
from ..ingestion.financial_compact_trial import CompactTrialTransport, read_compact
from ..ingestion.financial_date_pit import next_session
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_pilot_readiness import SIGNALS
from ..ingestion.financial_task_readiness import ANNUAL_TASKS
from ..ingestion.financial_trial_transport import TrialBudgetError
from ..ingestion.sources.base import AccessControlError, RateLimitError

VERSION = 'financial-user-workflow-v1'
GOOD = {'DOWNLOADED', 'CACHED'}
TASKS = ['EPS_RECOMPUTE', 'Z_SCORE', 'F_SCORE', 'M_SCORE', 'PE', 'PB']


def load(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, body):
    """Publish a complete immutable file; interruption leaves only an ignored temp."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('immutable output exists: ' + str(path))
    temp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    with temp.open('xb') as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


@contextmanager
def exclusive(run):
    """OS lock releases on process death; another terminal must not run concurrently."""
    path = Path(run) / 'work.lock'
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def pin(root, path, sha):
    p = inside(root, path)
    if digest(p.read_bytes()) != sha:
        raise ValueError('input changed: ' + str(path))
    return p


def validate(c, members):
    if c.get('version') != VERSION or any(c.get(k) is not False for k in CLOSED):
        raise ValueError('closed workflow required')
    if len(members) != 50 or c['symbols'] != [m['ticker'] for m in members]:
        raise ValueError('exact frozen50 membership required')
    if c['target_years'] != [2025] or c['document_years'] != [2023, 2024, 2025]:
        raise ValueError('v1 reviews FY2025 with two historical annual years')
    b = c['budgets']
    caps = {'max_logical_requests': 300, 'max_transport_attempts': 300,
        'max_pdf_download_attempts': 150, 'max_response_bytes': 25_000_000,
        'max_total_downloaded_bytes': 1_500_000_000, 'max_wall_seconds': 86400,
        'max_attempts_per_request': 1, 'timeout_seconds': 30}
    if any(type(b.get(k)) is not int or not 1 <= b[k] <= cap for k, cap in caps.items()):
        raise ValueError('workflow network budget exceeded')
    if type(b.get('min_seconds_between_transport_attempts')) is not int or not 2 <= b['min_seconds_between_transport_attempts'] <= 30:
        raise ValueError('request spacing required')
    if set(c['approved_hosts']) != {'cafef.vn', 'cafefnew.mediacdn.vn'}:
        raise ValueError('live acquisition restricted to CafeF')
    if not 1 <= c['max_ocr_pages'] <= 6000 or not 1 <= c['preview_pages'] <= 16:
        raise ValueError('bounded OCR required')


def open_run(root, relative):
    run = inside(root, relative, 'data')
    verify_inventory(run / 'frozen')
    c = load(run / 'frozen/config.json')
    for path, sha in load(run / 'frozen/pins.json').items():
        pin(root, path, sha)
    members = load(inside(root, c['trial_run']) / 'plan.json')['members']
    validate(c, members)
    return run, c, members


def seeds(root, c):
    cache = {}; documents = []; ocr = {}
    probe = load(inside(root, c['probe_run']) / 'results.json')
    for row in probe['requests']:
        if row['status'] in GOOD or row['status'] == 'FAILED':
            cache[row['url']] = row
    for d in probe['documents']:
        a = d['acquisition']
        if a['status'] in GOOD:
            documents.append(dict(symbol=d['symbol'], year=d['year'], url=a['url'],
                path=a['path'], sha256=a['sha256'], status='CACHED', scope='UNREVIEWED',
                listing_name=d['provider_report']['Name']))
    for d in c['extra_cached_pdfs']:
        documents.append(dict(d, status='CACHED', scope='UNREVIEWED'))
        if d.get('url'):
            cache[d['url']] = dict(d, status='CACHED')
    index = load(inside(root, c['ocr_run']) / 'index.json')
    for d in index['documents']:
        if d['status'] == 'OCR_CANDIDATE_COMPLETE':
            ocr[d['pdf_sha256']] = d['pages']
    return cache, documents, ocr


def make_plan(root, config_path, output):
    root = Path(root).resolve(); cfg = inside(root, config_path, 'configs')
    c = load(cfg); members = load(inside(root, c['trial_run']) / 'plan.json')['members']
    validate(c, members)
    pins = dict(c['input_pins'])
    for name in c['code_paths']:
        pins[name] = digest(inside(root, name).read_bytes())
    for name, sha in pins.items():
        pin(root, name, sha)
    pins[cfg.relative_to(root).as_posix()] = digest(cfg.read_bytes())
    _, documents, _ = seeds(root, c)
    for d in documents:
        pin(root, d['path'], d['sha256'])
    out = inside(root, output, 'data'); out.mkdir(parents=True, exist_ok=False)
    jobs = [dict(symbol=s, year=y, kind='list',
        url=f'https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={s.lower()}&Type=1&Year={y}')
        for y in reversed(c['document_years']) for s in c['symbols']]
    frozen = out / 'frozen'
    write_new(frozen / 'config.json', cfg.read_bytes())
    write_new(frozen / 'pins.json', encoded(pins))
    write_new(frozen / 'plan.json', encoded(dict(jobs=jobs, seed_documents=documents,
        stage='LOCAL_READINESS_AND_MANUAL_REFERENCE_REVIEW', **CLOSED)))
    seal(frozen)
    return dict(status='PLAN_FROZEN', symbols=50, listing_jobs=len(jobs),
        target_years=c['target_years'], run=out.relative_to(root).as_posix(), **CLOSED)


def receipts(run):
    result = {}
    for folder in sorted((run / 'receipts').glob('*')):
        if not (folder / 'manifest.json').exists():
            continue
        verify_inventory(folder)
        r = load(folder / 'receipt.json'); result[r['job_key']] = r
    return result


def job_key(job):
    return digest(encoded({k: job[k] for k in ['kind', 'symbol', 'year', 'url']}))


def annual_rows(body, year):
    p = json.loads(body)
    if not isinstance(p, dict) or p.get('Success') is not True or not isinstance(p.get('Data'), list):
        raise ValueError('invalid listing envelope')
    rows = [r for r in p['Data'] if r.get('Year') == year and r.get('Quarter') == 5]
    for r in rows:
        if not isinstance(r.get('Name'), str) or not isinstance(r.get('Link'), str):
            raise ValueError('invalid annual candidate')
    # Retain unlabeled/separate/fiscal exceptions for review, never accept scope here.
    return rows


def transport_state(run):
    folders = sorted((run / 'transport').glob('*'))
    for folder in reversed(folders):
        p = folder / 'transport.jsonl'
        if p.exists() and p.stat().st_size:
            return read_compact(folder)['state']
    return None


def acquire(root, relative, network=False, limit=10, factory=CompactTrialTransport):
    root = Path(root).resolve(); run, c, _ = open_run(root, relative)
    if not 1 <= limit <= 300:
        raise ValueError('job limit must be 1..300')
    cache, _, _ = seeds(root, c); plan = load(run / 'frozen/plan.json')
    with exclusive(run):
        done = receipts(run); queue = list(plan['jobs']); transport = None; count = 0
        prior_state = transport_state(run)
        cache.update((prior_state or {}).get('cache', {}))
        for r in done.values():
            if r['kind'] == 'list':
                queue.extend(r.get('pdf_jobs', []))
        # Cached work costs no network budget. Old terminal failures are not retried.
        for job in queue:
            key = job_key(job)
            if key in done:
                continue
            if count >= limit:
                break
            body = None; cached = cache.get(job['url']); record = dict(job, job_key=key)
            if cached and cached['status'] in GOOD:
                p = pin(root, cached['path'], cached['sha256']); body = p.read_bytes()
                record.update(status='CACHED', path=p.relative_to(root).as_posix(), sha256=digest(body))
            elif cached and cached['status'] == 'FAILED':
                record.update(status='KNOWN_SOURCE_FAILURE', error=cached.get('error', 'prior failure'))
            elif not network:
                continue  # Offline is not a terminal job; a later live command may acquire it.
            else:
                if transport is None:
                    folder = run / 'transport' / stamp()
                    folder.mkdir(parents=True)
                    transport = factory(root, folder, dict(c, cache_epoch=relative), transport_state(run))
                if transport.state['boundary'] or transport.state['budget_stop']:
                    break
                transport.context = dict(kind=job['kind'], symbol=job['symbol'], year=job['year'])
                try:
                    body, _ = transport.get(job['url'])
                    if job['kind'] == 'pdf' and not body.startswith(b'%PDF'):
                        raise ValueError('invalid PDF signature')
                    path = run / 'raw' / (digest(body) + ('.pdf' if job['kind'] == 'pdf' else '.json'))
                    if not path.exists():
                        write_new(path, body)
                    record.update(status='DOWNLOADED', path=path.relative_to(root).as_posix(), sha256=digest(body))
                    transport.commit_cache(job['url'], {k:record[k] for k in ['status', 'path', 'sha256']})
                except (AccessControlError, RateLimitError, TrialBudgetError):
                    break  # Durable global latch; resume cannot reset it.
                except (OSError, ValueError) as exc:
                    record.update(status='FAILED', error=str(exc)); body = None
            if body is not None and job['kind'] == 'list':
                try:
                    rows = annual_rows(body, job['year'])
                    pdf_jobs = []
                    for r in rows:
                        validate_url(r['Link'], c['approved_hosts'])
                        pdf_jobs.append(dict(symbol=job['symbol'], year=job['year'], kind='pdf',
                            url=r['Link'], listing_name=r['Name'], listing_sha256=record['sha256'],
                            scope='UNREVIEWED'))
                    record.update(pdf_jobs=pdf_jobs, annual_candidates=len(rows))
                    queue.extend(pdf_jobs)
                except (ValueError, KeyError, TypeError) as exc:
                    record.update(status='INVALID_LISTING', error=str(exc), pdf_jobs=[])
            dest = run / 'receipts' / (key + '-' + uuid4().hex[:8])
            write_new(dest / 'receipt.json', encoded(record)); seal(dest)
            done[key] = record; count += 1
            print(job['symbol'], job['year'], job['kind'], record['status'], flush=True)
        state = transport.state if transport else transport_state(run)
        return dict(status='GLOBAL_STOP' if state and (state['boundary'] or state['budget_stop']) else 'BATCH_COMPLETE',
            completed_jobs=count, total_receipts=len(done), network=network,
            counters={k:v for k,v in (state or {}).items() if k not in ['requests', 'cache']}, **CLOSED)


def stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid4().hex[:6]


def document_index(root, run, c):
    _, documents, _ = seeds(root, c)
    documents += [r for r in receipts(run).values() if r['kind'] == 'pdf' and r['status'] in GOOD]
    unique = {}
    for d in documents:
        unique.setdefault((d['symbol'], d['year'], d['sha256']), d)
    return list(unique.values())


def page_index(root, run, c):
    _, _, cached = seeds(root, c)
    pages = {(sha, p['pdf_page']): p for sha, ps in cached.items() for p in ps}
    for folder in sorted((run / 'extract').glob('*')):
        if not (folder / 'manifest.json').exists():
            continue
        verify_inventory(folder)
        r = load(folder / 'result.json')
        for p in r.get('pages', []):
            pages[r['pdf_sha256'], p['pdf_page']] = p
    return pages


def ocr_reserved(run):
    return sum(load(p)['reserved_ocr_pages'] for p in (run / 'extract').glob('*/reservation.json'))


def extract(root, relative, limit=8, full_ocr=False, worker=None, symbols=None, retry_failed=False):
    root = Path(root).resolve(); run, c, _ = open_run(root, relative)
    if not 1 <= limit <= 8:
        raise ValueError('extract batch is 1..8 PDFs')
    renderer = shutil.which('pdftoppm')
    if not renderer:
        raise ValueError('pdftoppm missing; run doctor')
    with exclusive(run):
        pages = page_index(root, run, c); count = 0; batch_pages = 0
        docs = document_index(root, run, c)
        if symbols:
            if not set(symbols) <= set(c['symbols']):
                raise ValueError('extract symbols outside frozen50')
            docs = [d for d in docs if d['symbol'] in symbols]
        failed = {load(p)['pdf_sha256'] for p in (run / 'extract').glob('*/result.json')
                  if load(p)['status'] == 'EXTRACTION_FAILED'}
        docs.sort(key=lambda d:(-d['year'], d['symbol'] not in ['MWG', 'GMD', 'VHC', 'DGC'], d['symbol']))
        for d in docs:
            if count >= limit:
                break
            if d['sha256'] in failed and not retry_failed:
                continue
            pdf = pin(root, d['path'], d['sha256'])
            if shutil.disk_usage(run).free < c['min_free_disk_bytes']:
                raise ValueError('free disk below configured OCR safety margin')
            # Read headers only here; full text extraction stays in a timeout worker.
            from pypdf import PdfReader
            reader = PdfReader(pdf)
            if reader.is_encrypted:
                continue
            total = len(reader.pages)
            if not 1 <= total <= 250:
                continue
            end = total if full_ocr else min(total, c['preview_pages'])
            needed = [n for n in range(1, end + 1) if (d['sha256'], n) not in pages]
            if not needed:
                continue
            allowance = min(320 - batch_pages, c['max_ocr_pages'] - ocr_reserved(run))
            needed = needed[:max(0, allowance)]
            if not needed:
                break
            folder = run / 'extract' / stamp(); folder.mkdir(parents=True)
            reservation = dict(symbol=d['symbol'], year=d['year'], pdf_path=d['path'],
                pdf_sha256=d['sha256'], reserved_ocr_pages=len(needed), requested_pages=needed,
                full_ocr=full_ocr, total_pdf_pages=total)
            write_new(folder / 'reservation.json', encoded(reservation))
            result = dict(reservation, status='EXTRACTION_FAILED', pages=[])
            start = time.monotonic()
            try:
                text_output = folder / 'text.json'
                command = [sys.executable, str(worker), '--worker-pdf', str(pdf),
                    '--worker-output', str(text_output), '--max-pages', str(total)]
                try:
                    subprocess.run(command, check=True, timeout=90, capture_output=True)
                    result['text_path'] = text_output.relative_to(root).as_posix()
                    result['text_sha256'] = digest(text_output.read_bytes())
                    result['page_hints'] = hints(load(text_output)['pages'])
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    result['text_error'] = str(exc)  # Scan fallback still runs.
                # Render contiguous missing ranges without changing an existing evidence file.
                groups = []
                for n in needed:
                    if groups and n == groups[-1][-1] + 1:
                        groups[-1].append(n)
                    else:
                        groups.append([n])
                for group in groups:
                    subprocess.run([renderer, '-f', str(group[0]), '-l', str(group[-1]),
                        '-scale-to', '2200', '-png', str(pdf), str(folder / 'page')],
                        check=True, timeout=360, capture_output=True)
                subprocess.run(['powershell.exe', '-NoProfile', '-File', str(root / 'scripts/ocr_financial_pages.ps1'),
                    '-ImageDirectory', str(folder)], check=True, timeout=600, capture_output=True)
                for path in sorted(folder.glob('page-*.ocr.json')):
                    x = load(path); image = path.with_name(path.name.replace('.ocr.json', '.png'))
                    if digest(image.read_bytes()) != x['image_sha256']:
                        raise ValueError('OCR image mismatch')
                    n = int(path.name.split('-')[1].split('.')[0])
                    result['pages'].append(dict(pdf_page=n, image_path=image.relative_to(root).as_posix(),
                        image_sha256=x['image_sha256'], ocr_path=path.relative_to(root).as_posix(),
                        ocr_sha256=digest(path.read_bytes())))
                if sorted(p['pdf_page'] for p in result['pages']) != needed:
                    raise ValueError('incomplete OCR page output')
                result['status'] = 'OCR_CANDIDATES_COMPLETE'
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                result.update(status='EXTRACTION_FAILED', error=str(exc), pages=[])
            result['seconds'] = time.monotonic() - start
            write_new(folder / 'result.json', encoded(result)); seal(folder)
            count += 1; batch_pages += len(needed)
            pages.update({(d['sha256'], p['pdf_page']): p for p in result['pages']})
            print(d['symbol'], d['year'], result['status'], flush=True)
        return dict(status='BATCH_COMPLETE', processed_documents=count, reserved_pages_this_batch=batch_pages,
            total_reserved_ocr_pages=ocr_reserved(run), **CLOSED)


def inputs_for(task):
    if task == 'EPS_RECOMPUTE':
        return [('eps_adjusted_earnings_numerator', 0), ('weighted_average_basic_shares', 0)]
    if task == 'F_SCORE':
        return sorted({('net_profit' if f == 'income_before_extraordinary_items' else f, o)
            for req in SIGNALS.values() for f, o in req})
    if task == 'M_SCORE':
        return [(f, o) for f in M_FIELDS for o in [0, -1]] + [('net_profit', 0), ('operating_cash_flow', 0)]
    return ANNUAL_TASKS[task]


def baseline_references(root, c):
    rows = load(inside(root, c['integration_run']) / 'reference-ledger.json')
    result = [r for r in rows if type(r.get('year')) is int and r['year'] in c['target_years']]
    for r in load(inside(root, c['review_run']) / 'references.json'):
        for task, value in [('EPS_RECOMPUTE', (r['disclosed_basic_eps_reference'] or {}).get('value')),
                            ('Z_SCORE', (r['z_reference'] or {}).get('em_z_double_prime_reference'))]:
            if value is not None:
                result.append(dict(symbol=r['symbol'], year=r['year'], task=task, value=value,
                    pit_status=r['date_pit_status'], usable_from_date=r['usable_from_date'],
                    basis='DISCLOSED_BASIC_EPS' if task == 'EPS_RECOMPUTE' else 'EM_Z_DOUBLE_PRIME',
                    production_accepted=False))
    return result


def review_references(root, run, c):
    rows = []
    for folder in sorted((run / 'reviews').glob('*')):
        verify_inventory(folder)
        rows.extend(load(folder / 'references.json'))
    return rows


def assessment(requirements, members, references, target_years):
    lookup = {(r['symbol'], r['year'], r['field']): r for r in requirements}
    refs = {}
    for r in references:
        refs.setdefault((r['symbol'], r['year'], r['task']), []).append(r)
    rows = []
    for m in members:
        for year in target_years:
            diagnostic = candidate_math(requirements, m['ticker'], year, m['proposed_company_type'])
            for task in TASKS:
                fields = []
                for field, offset in inputs_for(task):
                    values = lookup.get((m['ticker'], year + offset, field), {}).get('candidate_values', [])
                    status = 'UNVERIFIED_CANDIDATE' if len(values) == 1 else 'VALUE_CONFLICT' if values else 'MISSING'
                    fields.append(dict(field=field, year=year + offset, status=status))
                reviewed = refs.get((m['ticker'], year, task), [])
                # Multiple vintage/basis references remain separate; no implicit priority.
                numeric = [r for r in reviewed if r.get('value') is not None and task not in ['PE', 'PB']]
                other_basis = [r for r in reviewed if r.get('value') is not None and task in ['PE', 'PB']]
                status = 'REFERENCE_CALCULATED' if numeric else 'REFERENCE_OTHER_BASIS_ONLY' if other_basis else 'SECTOR_TEMPLATE_REQUIRED' if m['proposed_company_type'] != 'Regular' else 'UNREVIEWED_INPUTS' if all(f['status'] == 'UNVERIFIED_CANDIDATE' for f in fields) else 'MISSING_OR_CONFLICTING_INPUTS'
                rows.append(dict(symbol=m['ticker'], year=year, task=task, company_type=m['proposed_company_type'],
                    status=status, candidate_input_count=sum(f['status'] == 'UNVERIFIED_CANDIDATE' for f in fields),
                    required_input_count=len(fields), inputs=fields,
                    missing_fields=[f"{f['field']}@{f['year']}:{f['status']}" for f in fields if f['status'] != 'UNVERIFIED_CANDIDATE'],
                    references=reviewed, numeric_reference_count=len(numeric), other_basis_reference_count=len(other_basis),
                    diagnostic_z=diagnostic.get('z_arithmetic') if task == 'Z_SCORE' else None,
                    diagnostic_printed_eps=diagnostic.get('vendor_basic_eps') if task == 'EPS_RECOMPUTE' else None,
                    external_blockers=(['EXACT_TTM_EPS', 'RAW_PRICE_AND_SHARE_EVENT_BASIS'] if task == 'PE' else
                        ['PARENT_EQUITY_SHARES_PRICE_DATE_AND_EVENT_ALIGNMENT'] if task == 'PB' else []),
                    publication_review_required=not numeric or any(not r.get('usable_from_date') for r in numeric),
                    production_value=None, **CLOSED))
    return rows


def report(root, relative):
    root = Path(root).resolve(); run, c, members = open_run(root, relative)
    with exclusive(run):
        requirements = load(inside(root, c['trial_run']) / 'requirements.json')
        references = baseline_references(root, c) + review_references(root, run, c)
        rows = assessment(requirements, members, references, c['target_years'])
        docs = document_index(root, run, c); pages = page_index(root, run, c)
        rs = list(receipts(run).values()); state = transport_state(run)
        exceptions = [r for r in rs if r['status'] not in GOOD or
                      (r['kind'] == 'list' and not r.get('annual_candidates'))]
        extraction_failures = [load(p) for p in (run / 'extract').glob('*/result.json')
                              if load(p)['status'] == 'EXTRACTION_FAILED']
        requests = load(run / 'frozen/plan.json')['jobs']
        pdf_jobs = [j for r in rs for j in r.get('pdf_jobs', [])]
        done = {r['job_key'] for r in rs}
        pending = [j for j in requests + pdf_jobs if job_key(j) not in done]
        queue = [dict(symbol=r['symbol'], year=r['year'], task=r['task'], status=r['status'],
            missing_fields=r['missing_fields'], next_action='REVIEW_EXACT_PDF_NOTES_AND_PUBLICATION',
            external_blockers=r['external_blockers']) for r in rows if r['status'] != 'REFERENCE_CALCULATED']
        out = run / 'reports' / stamp()
        docreview = []
        for d in docs:
            available = sorted(p['pdf_page'] for (sha, _), p in pages.items() if sha == d['sha256'])
            docreview.append(dict(d, ocr_pages=available, review_status='UNREVIEWED'))
        summary = dict(version=VERSION, symbols=len(members), target_years=c['target_years'], tasks=len(rows),
            symbols_with_references=len({r['symbol'] for r in rows if r['numeric_reference_count']}),
            reference_task_cells=sum(r['numeric_reference_count'] > 0 for r in rows),
            reference_cells_by_task={t:sum(r['task'] == t and r['numeric_reference_count'] > 0 for r in rows) for t in TASKS},
            available_pdf_vintages=len(docs), cached_or_new_ocr_pages=len(pages),
            pending_acquisition_jobs=len(pending), source_exceptions=len(exceptions),
            extraction_failures=len(extraction_failures),
            total_reserved_ocr_pages=ocr_reserved(run),
            transport_counters={k:v for k,v in (state or {}).items() if k not in ['requests', 'cache']},
            production_ready_symbols=0, **CLOSED)
        for name, obj in [('summary.json', summary), ('readiness.json', rows), ('missing-queue.json', queue),
                          ('documents.json', docreview), ('pending-acquisition.json', pending),
                          ('exceptions.json', dict(source=exceptions, extraction=extraction_failures)),
                          ('previous-valuation-references.json', [r for r in load(inside(root, c['integration_run']) / 'reference-ledger.json')
                                                                 if r['task'] in ['PE', 'PB'] or type(r.get('year')) is not int])]:
            write_new(out / name, encoded(obj))
        fields = ['symbol', 'year', 'task', 'company_type', 'status', 'candidate_input_count',
            'required_input_count', 'missing_fields', 'numeric_reference_count', 'publication_review_required',
            'external_blockers', 'production_value', 'financial_cluster_allowed']
        stream = io.StringIO(newline=''); writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
        write_new(out / 'readiness.csv', stream.getvalue().encode('utf-8-sig'))
        text = ('# Kết quả financial user workflow\n\n'
            f"Đã đánh giá {len(rows)} ô chỉ số cho {len(members)} mã, FY2025. "
            f"{summary['symbols_with_references']}/50 mã có ít nhất một reference; "
            f"{summary['reference_task_cells']}/{len(rows)} ô có reference. Production-ready: 0.\n\n"
            f"Có {len(docs)} PDF vintage, {len(pages)} trang OCR dùng lại/mới; "
            f"còn {len(pending)} acquisition jobs.\n\n"
            'Reference không tự trở thành accepted/PIT/cluster-ready. Một mã chưa review không có nghĩa không tính được. '
            'Candidate input count chỉ đo sự hiện diện, chưa xác minh units/scope/notes/vintage. '
            'PE/PB ở bảng là task strict; annual PE arithmetic được lưu riêng trong review.\n\n'
            '[Bảng chỉ số](readiness.csv), [chi tiết input/reference](readiness.json), '
            '[danh sách thiếu](missing-queue.json), [PDF và trang OCR](documents.json), '
            '[công việc tải còn lại](pending-acquisition.json), [counters](summary.json).\n')
        write_new(out / 'report.md', text.encode('utf-8')); seal(out)
        return dict(summary, report=out.relative_to(root).as_posix())


def template(root, relative, symbol, year=2025, pdf_sha=None):
    root = Path(root).resolve(); run, c, members = open_run(root, relative)
    if symbol not in c['symbols'] or year not in c['target_years']:
        raise ValueError('review outside current stage')
    docs = [d for d in document_index(root, run, c) if d['symbol'] == symbol and d['year'] == year]
    if pdf_sha:
        docs = [d for d in docs if d['sha256'] == pdf_sha]
    if len(docs) != 1:
        raise ValueError('select exactly one --pdf-sha from report documents.json')
    d = docs[0]; pages = page_index(root, run, c)
    fields = sorted({x for t in TASKS[:4] for x in inputs_for(t)} |
                    {('vendor_basic_eps', 0), ('profit_before_tax', 0), ('interest_expense', 0)})
    facts = [dict(field=f, year=year+o, value=None, unit='SHARES' if f == 'weighted_average_basic_shares' else
        'VND_PER_SHARE' if f == 'vendor_basic_eps' else 'INDICATOR' if f == 'parent_common_equity_issuance_verified' else 'VND',
        pdf_page=None, locator='', review_status='UNREVIEWED') for f, o in fields]
    member = next(m for m in members if m['ticker'] == symbol)
    value = dict(version=VERSION, symbol=symbol, year=year, reviewer='', reviewed_at='',
        pdf_path=d['path'], pdf_sha256=d['sha256'], company_type=member['proposed_company_type'],
        scope='UNREVIEWED', framework='UNREVIEWED', period_start=f'{year}-01-01', period_end=f'{year}-12-31',
        vintage_basis='UNREVIEWED_CURRENT_AND_COMPARATIVE_IN_EXACT_PDF',
        ebit_basis='UNREVIEWED', receivables_basis='UNREVIEWED', publication=None, supporting_documents=[], facts=facts,
        page_evidence=[dict(p) for (sha, _), p in pages.items() if sha == d['sha256']], **CLOSED)
    with exclusive(run):
        dest = run / 'review-inputs' / f'{symbol}-{year}-{stamp()}.json'
        write_new(dest, encoded(value))
    return dict(status='EDITABLE_REVIEW_TEMPLATE_CREATED', path=dest.relative_to(root).as_posix())


def calculate_review(d, pages, calendar, decision_date, exchange):
    """Human-attested transcription. Same PDF vintage, explicit semantic choices."""
    if any(d.get(k) is not False for k in CLOSED) or not d.get('reviewer') or not d.get('reviewed_at'):
        raise ValueError('reviewer/date and closed gates required')
    year = d['year']
    if (d['company_type'] != 'Regular' or d['scope'] != 'CONSOLIDATED' or d['framework'] != 'VAS'
            or d['period_start'] != f'{year}-01-01' or d['period_end'] != f'{year}-12-31'
            or d['vintage_basis'] != 'CURRENT_AND_COMPARATIVE_IN_EXACT_PDF_REVIEWED'):
        raise ValueError('sector/scope/fiscal/vintage requires separate adapter')
    values = {}; present = []
    for f in d['facts']:
        if f.get('value') is None:
            continue
        if f.get('review_status') != 'VISUALLY_VERIFIED_REFERENCE_ONLY' or not f.get('locator') or type(f.get('pdf_page')) is not int:
            raise ValueError('fact requires explicit visual page and locator')
        source_sha = f.get('source_pdf_sha256', d['pdf_sha256'])
        if (source_sha, f['pdf_page']) not in pages:
            raise ValueError('reviewed page not in verified OCR evidence')
        offset = f['year'] - year
        if type(f['year']) is not int or offset not in [-2, -1, 0]:
            raise ValueError('invalid comparative year')
        expected = 'SHARES' if f['field'] == 'weighted_average_basic_shares' else 'VND_PER_SHARE' if f['field'] == 'vendor_basic_eps' else 'INDICATOR' if f['field'] == 'parent_common_equity_issuance_verified' else 'VND'
        if f['unit'] != expected or type(f['value']) is bool:
            raise ValueError('explicit compatible units required')
        key = (f['field'], offset); v = Decimal(str(f['value']))
        if key in values or not v.is_finite():
            raise ValueError('duplicate/nonfinite review input')
        if f['field'] == 'parent_common_equity_issuance_verified' and (v not in [0, 1] or f.get('derivation') != 'PARENT_COMMON_ISSUANCE_OCCURRED_VERIFIED'):
            raise ValueError('issuance indicator requires explicit parent-issuance evidence')
        values[key] = v; present.append(f)
    sources = {x['pdf_sha256']:x for x in [d] + d.get('supporting_documents', [])}
    dates = {}
    for sha, source in sources.items():
        pub = source.get('publication'); usable = None
        if pub:
            if pub.get('pdf_sha256') != sha or pub.get('precision') != 'DATE_ONLY' or pub.get('validation_status') != 'EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED':
                raise ValueError('publication must identify exact PDF')
            usable, _ = next_session(pub['publication_date'], exchange, calendar)
            if pub['publication_date'] <= source['period_end']:
                raise ValueError('publication must follow report period')
        dates[sha] = usable
    outputs = {}
    current = {f:v for (f, o), v in values.items() if o == 0}
    required_balance = {'total_assets', 'total_liabilities', 'total_equity'}
    balanced = required_balance <= current.keys() and abs(current['total_assets'] - current['total_liabilities'] - current['total_equity']) <= Decimal('1')
    if balanced and d['ebit_basis'] == 'EBT_PLUS_DISCLOSED_EXPENSED_INTEREST_EXCLUDING_ISSUANCE_FEES':
        if 'profit_before_tax' in current and 'interest_expense' in current:
            current['document_reconciled_ebit'] = current['profit_before_tax'] + current['interest_expense']
        outputs['Z_SCORE'] = calculate('Z_SCORE', current)
    elif balanced and d['ebit_basis'] == 'DIRECT_DOCUMENT_RECONCILED_EBIT':
        outputs['Z_SCORE'] = calculate('Z_SCORE', current)
    else:
        outputs['Z_SCORE'] = dict(value=None, status='BALANCE_OR_EBIT_REVIEW_REQUIRED')
    eps = calculate_disclosed_basic_eps(current.get('eps_adjusted_earnings_numerator'), current.get('weighted_average_basic_shares'), 12)
    if eps['value'] is not None and str(current.get('vendor_basic_eps')) != eps['rounded']:
        eps = dict(eps, value=None, status='PRINTED_EPS_ROUNDING_CHECK_FAILED')
    outputs['EPS_RECOMPUTE'] = eps
    outputs['F_SCORE'] = calculate_vas_f_score(values)
    outputs['M_SCORE'] = calculate_vas_m_score(values, d['receivables_basis'])
    rows = []
    for task, result in outputs.items():
        v = result.get('value')
        if task == 'Z_SCORE' and isinstance(v, dict):
            v = v['em_z_double_prime_reference']
        required_keys = set(inputs_for(task))
        if task == 'Z_SCORE':
            required_keys |= {('total_assets', 0), ('total_liabilities', 0), ('total_equity', 0)}
            if d['ebit_basis'] == 'EBT_PLUS_DISCLOSED_EXPENSED_INTEREST_EXCLUDING_ISSUANCE_FEES':
                required_keys |= {('profit_before_tax', 0), ('interest_expense', 0)}
        used_sources = {f.get('source_pdf_sha256', d['pdf_sha256']) for f in present
                        if (f['field'], f['year']-year) in required_keys} | {d['pdf_sha256']}
        if not used_sources <= set(sources):
            raise ValueError('fact source has no explicit document metadata')
        covered = all(dates[x] for x in used_sources)
        usable = max(dates[x] for x in used_sources) if covered else None
        pit_status = 'DATE_ONLY_ALL_REVIEWED_INPUT_DOCUMENTS_VERIFIED' if covered else 'EXACT_INPUT_VINTAGE_PUBLICATION_MISSING'
        rows.append(dict(symbol=d['symbol'], year=year, task=task, value=v, details=result,
            pdf_sha256=d['pdf_sha256'], pit_status=pit_status, usable_from_date=usable,
            date_eligible_at_snapshot=bool(usable and usable <= decision_date),
            basis=result.get('variant', 'EM_Z_DOUBLE_PRIME' if task == 'Z_SCORE' else 'DISCLOSED_BASIC_EPS'),
            acceptance='MANUAL_REVIEW_REQUIRED', production_accepted=False, **CLOSED))
    return rows


def review(root, relative, review_file):
    root = Path(root).resolve(); run, c, members = open_run(root, relative)
    source = inside(root, review_file, 'data'); d = load(source)
    if d.get('version') != VERSION or d['symbol'] not in c['symbols'] or d['year'] not in c['target_years']:
        raise ValueError('review outside frozen stage')
    docs = document_index(root, run, c)
    if not any(x['symbol'] == d['symbol'] and x['year'] == d['year'] and x['sha256'] == d['pdf_sha256'] and x['path'] == d['pdf_path'] for x in docs):
        raise ValueError('review document not acquired in this workflow')
    pin(root, d['pdf_path'], d['pdf_sha256'])
    allpages = page_index(root, run, c)
    sources = [d] + d.get('supporting_documents', [])
    source_hashes = set()
    for x in sources:
        if x['pdf_sha256'] in source_hashes:
            raise ValueError('duplicate supporting vintage')
        source_hashes.add(x['pdf_sha256'])
        if not any(z['symbol'] == d['symbol'] and z['sha256'] == x['pdf_sha256'] and z['path'] == x['pdf_path'] for z in docs):
            raise ValueError('supporting PDF not acquired for same symbol')
        if x.get('scope') != 'CONSOLIDATED' or x.get('framework') != 'VAS' or x.get('vintage_basis') != 'CURRENT_AND_COMPARATIVE_IN_EXACT_PDF_REVIEWED':
            raise ValueError('supporting scope/framework/vintage unreviewed')
        source_year = int(x['period_end'][:4])
        if source_year not in c['document_years'] or x['period_start'] != f'{source_year}-01-01' or x['period_end'] != f'{source_year}-12-31':
            raise ValueError('supporting fiscal period requires separate adapter')
        pin(root, x['pdf_path'], x['pdf_sha256'])
        pub = x.get('publication')
        if pub:
            pin(root, pub['evidence_path'], pub['evidence_sha256'])
    pages = {(sha, n):p for (sha, n), p in allpages.items() if sha in source_hashes}
    for f in d['facts']:
        if f.get('value') is not None:
            source_doc = next((x for x in sources if x['pdf_sha256'] == f.get('source_pdf_sha256', d['pdf_sha256'])), None)
            if not source_doc or not int(source_doc['period_end'][:4])-2 <= f['year'] <= int(source_doc['period_end'][:4]):
                raise ValueError('fact year does not belong to source vintage')
            ev = pages.get((f.get('source_pdf_sha256', d['pdf_sha256']), f.get('pdf_page')))
            if not ev:
                raise ValueError('OCR page missing; run extract -FullOcr')
            pin(root, ev['image_path'], ev['image_sha256']); pin(root, ev['ocr_path'], ev['ocr_sha256'])
    m = next(m for m in members if m['ticker'] == d['symbol'])
    if d['company_type'] != m['proposed_company_type']:
        raise ValueError('cannot override sector routing')
    calendar = [json.loads(x) for x in inside(root, c['calendar_path']).read_text(encoding='utf8').splitlines()]
    rows = calculate_review(d, pages, calendar, c['decision_date'], m['exchange'])
    requirements = load(inside(root, c['trial_run']) / 'requirements.json')
    qa = []
    for f in d['facts']:
        if f.get('value') is None:
            continue
        provider = sorted({v for r in requirements if r['symbol'] == d['symbol'] and r['year'] == f['year']
                           and r['field'] == f['field'] for v in r.get('candidate_values', [])})
        qa.append(dict(field=f['field'], year=f['year'], reviewed_value=f['value'], provider_values=provider,
            status='NO_PROVIDER_FIELD' if not provider else 'MATCH' if len(provider) == 1 and Decimal(provider[0]) == Decimal(str(f['value'])) else 'VALUE_OR_VINTAGE_DIFFERENCE_REVIEW_REQUIRED',
            canonical_value=None))
    with exclusive(run):
        out = run / 'reviews' / stamp()
        write_new(out / 'review.json', source.read_bytes()); write_new(out / 'references.json', encoded(rows))
        write_new(out / 'qa.json', encoded(qa)); seal(out)
    return dict(status='REFERENCE_REVIEW_RECORDED', reference_values=sum(r['value'] is not None for r in rows),
        output=out.relative_to(root).as_posix(), **CLOSED)


def verify(root, relative):
    root = Path(root).resolve(); run, c, _ = open_run(root, relative)
    with exclusive(run):
        for d in document_index(root, run, c):
            pin(root, d['path'], d['sha256'])
        for r in receipts(run).values():
            if r['status'] in GOOD:
                pin(root, r['path'], r['sha256'])
        for p in page_index(root, run, c).values():
            pin(root, p['image_path'], p['image_sha256']); pin(root, p['ocr_path'], p['ocr_sha256'])
        for area in ['reports', 'reviews']:
            for folder in (run / area).glob('*'):
                verify_inventory(folder)
        state = transport_state(run)
        return dict(status='VERIFIED', interrupted_extract_attempts=sum(not (p.parent / 'manifest.json').exists()
            for p in (run / 'extract').glob('*/reservation.json')), transport_latched=bool(state and (state['boundary'] or state['budget_stop'])), **CLOSED)
