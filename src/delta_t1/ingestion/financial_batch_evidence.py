"""Checkpointed, bounded financial evidence acquisition and PDF discovery.

Every completed task has its own immutable manifest. A new run can resume a
partially written run without trusting unsealed files. These are candidates,
never automatically accepted financial facts or publication dates.
"""
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

from .cafef_financial import digest, encoded, immutable_write, now
from .cafef_financial_detail import PublicEvidenceClient
from .financial_documents import consolidated_rows, verify_inventory
from .sources.base import AccessControlError, RateLimitError

VERSION = 'financial-batch-evidence-v1'
GATES = dict(financial_features_allowed=False, research_ready=False, full_universe_allowed=False)


def inside(root, relative, area=None):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root / area if area else root):
        raise ValueError('path outside permitted workspace area: ' + str(relative))
    return path


def seal(folder):
    immutable_write(folder / 'manifest.json', encoded(dict(files={
        p.relative_to(folder).as_posix(): digest(p.read_bytes())
        for p in sorted(folder.rglob('*')) if p.is_file()})))


def validate(c):
    if c.get('version') != VERSION or any(c.get(k) is not False for k in GATES):
        raise ValueError('bounded evidence contract required')
    for name, maximum in [('symbols', 30), ('years', 7)]:
        values = c[name]
        if not isinstance(values, list) or not 1 <= len(values) <= maximum or len(set(values)) != len(values):
            raise ValueError('invalid ' + name)
    if any(not isinstance(s, str) or not re.fullmatch(r'[A-Z0-9]{1,10}', s) for s in c['symbols']):
        raise ValueError('invalid symbols')
    if any(type(y) is not int or not 2019 <= y <= 2026 for y in c['years']):
        raise ValueError('invalid years')
    bounds = dict(max_logical_requests=(0, 60), max_pdf_downloads=(0, 24), max_documents=(1, 40),
                  max_bytes=(1, 50_000_000), max_total_bytes=(1, 300_000_000),
                  max_text_pages=(1, 1500), max_pdf_pages=(1, 250),
                  max_ocr_pages=(0, 48), ocr_first_pages=(0, 8), max_seconds=(1, 3600))
    for name, (low, high) in bounds.items():
        if type(c.get(name)) is not int or not low <= c[name] <= high:
            raise ValueError('invalid budget: ' + name)
    if not isinstance(c.get('cache_epoch'), str) or not c['cache_epoch']:
        raise ValueError('explicit frozen cache epoch required')
    hosts = c.get('approved_hosts', [])
    if not hosts or any(not isinstance(h, str) or not re.fullmatch(r'[a-z0-9.-]+', h) for h in hosts):
        raise ValueError('invalid approved hosts')
    for d in c.get('discovery', []):
        if d['symbol'] not in c['symbols'] or d['year'] not in c['years']:
            raise ValueError('discovery outside batch')
    if len(c.get('discovery', [])) > 60 or len(c.get('documents', [])) > c['max_documents']:
        raise ValueError('input task cap exceeded')
    for d in c.get('documents', []):
        if d['symbol'] not in c['symbols'] or d['year'] not in c['years'] or type(d.get('quarter')) is not int or d['quarter'] not in range(5):
            raise ValueError('document outside batch')
        validate_url(d['url'], hosts)
    if len(c.get('cache_records', [])) > 80:
        raise ValueError('cache seed cap exceeded')
    return c


def validate_url(url, hosts):
    uri = urlsplit(url)
    if uri.scheme != 'https' or uri.username or uri.password or uri.hostname not in hosts or uri.fragment:
        raise ValueError('unapproved source URL')


def task_key(request):
    return digest(encoded(request))


class Checkpoints:
    def __init__(self, root, output, c, resume_runs=()):
        self.root, self.output, self.c = Path(root).resolve(), Path(output), c
        self.cached, self.boundary = {}, False
        self.local = {}
        self.metrics = dict(logical_requests=0, pdf_download_attempts=0, downloaded_bytes=0,
                            cache_hits=0, new_checkpoints=0, text_pages=0, ocr_pages=0)
        self.started = time.monotonic()
        for relative in resume_runs:
            run = inside(self.root, relative, 'data')
            sealed = (run / 'manifest.json').exists()
            if sealed:
                verify_inventory(run)
            receipts = set((run / 'tasks').glob('*/result.json'))
            if sealed and (run/'results.json').exists():
                summary = json.loads((run/'results.json').read_bytes())
                self.boundary |= summary.get('engineering_status') == 'HARD_STOP'
                refs = summary['listings'] + [d[k] for d in summary['documents']
                        for k in ['acquisition', 'extraction'] if k in d]
                for ref in refs:
                    if 'checkpoint_path' not in ref:
                        continue
                    task = inside(self.root, ref['checkpoint_path'], 'data')
                    verify_inventory(task)
                    if (ref.get('checkpoint_manifest_sha256') and
                            digest((task/'manifest.json').read_bytes()) != ref['checkpoint_manifest_sha256']):
                        raise ValueError('resume external checkpoint manifest changed')
                    receipt = task/'result.json'
                    saved = json.loads(receipt.read_bytes())
                    if any(saved[k] != ref[k] for k in ['request', 'status', 'payload']):
                        raise ValueError('resume external receipt changed')
                    receipts.add(receipt)
            # Explicitly support an interrupted parent: only independently sealed tasks count.
            for receipt in sorted(receipts):
                if not (receipt.parent / 'manifest.json').exists():
                    continue
                verify_inventory(receipt.parent)
                r = json.loads(receipt.read_bytes())
                if r['request'].get('version') != VERSION:
                    raise ValueError('checkpoint version mismatch')
                key = task_key(r['request'])
                if key != receipt.parent.name:
                    raise ValueError('checkpoint identity mismatch')
                if r['status'] in ['HARD_STOP', 'DEFERRED_BOUNDARY_REVIEW']:
                    self.boundary = True
                if r['status'] == 'COMPLETE':
                    old = self.cached.get(key)
                    # Identical raw bytes from separate runs are one value even if paths/times differ.
                    compare = (lambda p: p['sha256']) if r['request']['operation'] == 'ACQUIRE' else (lambda p: p)
                    if old and compare(old[0]['payload']) != compare(r['payload']):
                        raise ValueError('competing checkpoint values; no source priority')
                    self.cached[key] = (r, receipt.parent)
        self.seeds = {}
        verified = set()
        for record in c.get('cache_records', []):
            run = inside(self.root, record['run'], 'data')
            if digest((run / 'manifest.json').read_bytes()) != record['manifest_sha256']:
                raise ValueError('seed manifest mismatch')
            if run not in verified:
                manifest = verify_inventory(run)
                verified.add(run)
            else:
                manifest = json.loads((run / 'manifest.json').read_bytes())
            path = inside(self.root, record['path'], 'data')
            if not path.is_relative_to(run) or manifest['files'].get(path.relative_to(run).as_posix()) != record['sha256']:
                raise ValueError('seed file outside pinned inventory')
            validate_url(record['url'], c['approved_hosts'])
            # A seed must have exact URL/body association in its acquired inventory/metadata.
            inv = json.loads((run / 'inventory.json').read_bytes()) if (run / 'inventory.json').exists() else {}
            rows = inv.get('requests', inv.get('documents', []))
            association = any((r.get('url', r.get('provider_report', {}).get('Link')) == record['url']
                               and r.get('sha256') == record['sha256']) for r in rows)
            metadata = path.with_suffix('.metadata.json')
            if metadata.exists():
                m = json.loads(metadata.read_bytes())
                association |= m.get('url') == record['url'] and m.get('sha256') == record['sha256']
            if not association:
                raise ValueError('seed URL/body provenance missing')
            key = (record['url'], record['kind'])
            if key in self.seeds and self.seeds[key]['sha256'] != record['sha256']:
                raise ValueError('competing seed vintages; choose a frozen epoch explicitly')
            self.seeds[key] = record

    def cached_result(self, request):
        key = task_key(request)
        if key in self.local:
            return self.local[key]
        match = self.cached.get(key)
        if not match:
            return None
        result, old = match
        self.metrics['cache_hits'] += 1
        result = dict(result, checkpoint_path=str(old.relative_to(self.root)),
                      checkpoint_manifest_sha256=digest((old/'manifest.json').read_bytes()), reused=True)
        return result

    def commit(self, request, status, payload, folder=None, error=None):
        folder = folder or self.output / 'tasks' / task_key(request)
        folder.mkdir(parents=True, exist_ok=True)
        result = dict(request=request, status=status, payload=payload, error=error,
                      completed_at=now(), **GATES)
        immutable_write(folder / 'result.json', encoded(result))
        seal(folder)
        self.metrics['new_checkpoints'] += 1
        result = dict(result, checkpoint_path=str(folder.relative_to(self.root)),
                      checkpoint_manifest_sha256=digest((folder/'manifest.json').read_bytes()), reused=False)
        self.local[task_key(request)] = result
        return result

    def acquire(self, item, client, network):
        request = dict(version=VERSION, operation='ACQUIRE', cache_epoch=self.c['cache_epoch'], **item)
        old = self.cached_result(request)
        if old:
            if old['status'] == 'COMPLETE':
                file = inside(self.root, old['payload']['path'], 'data')
                if digest(file.read_bytes()) != old['payload']['sha256']:
                    raise ValueError('cached raw changed')
            return old
        validate_url(item['url'], self.c['approved_hosts'])
        seed = self.seeds.get((item['url'], item['kind']))
        if seed:
            # The raw remains in its original immutable run; no publication inference.
            self.metrics['cache_hits'] += 1
            return self.commit(request, 'COMPLETE', dict(path=seed['path'], sha256=seed['sha256'],
                    origin='PINNED_EXISTING_RAW', source_manifest_sha256=seed['manifest_sha256']))
        if self.boundary:
            return self.commit(request, 'DEFERRED_BOUNDARY_REVIEW', {})
        if not network:
            return self.commit(request, 'DEFERRED_OFFLINE_CACHE_MISS', {})
        if (self.metrics['logical_requests'] >= self.c['max_logical_requests']
                or self.metrics['downloaded_bytes'] >= self.c['max_total_bytes']
                or time.monotonic() - self.started >= self.c['max_seconds']
                or (item['kind'] == 'pdf' and self.metrics['pdf_download_attempts'] >= self.c['max_pdf_downloads'])):
            return self.commit(request, 'DEFERRED_BUDGET', {})
        self.metrics['logical_requests'] += 1
        self.metrics['pdf_download_attempts'] += int(item['kind'] == 'pdf')
        try:
            body, status = client.get(item['url'])
            if status != 200 or len(body) > self.c['max_bytes'] or (item['kind'] == 'pdf' and not body.startswith(b'%PDF')):
                raise ValueError('response status/size/PDF signature invalid')
            if self.metrics['downloaded_bytes'] + len(body) > self.c['max_total_bytes']:
                raise ValueError('total response byte cap exceeded')
            self.metrics['downloaded_bytes'] += len(body)
            folder = self.output / 'tasks' / task_key(request)
            file = folder / ('raw.pdf' if item['kind'] == 'pdf' else 'raw.json')
            immutable_write(file, body)
            return self.commit(request, 'COMPLETE', dict(path=str(file.relative_to(self.root)),
                    sha256=digest(body), origin='HTTP_RESPONSE', http_status=status, fetched_at=now()), folder)
        except (AccessControlError, RateLimitError) as exc:
            self.boundary = True
            return self.commit(request, 'HARD_STOP', {}, error=str(exc))
        except (OSError, ValueError) as exc:
            return self.commit(request, 'FAILED', {}, error=str(exc))


def collect(checkpoints, network=False, client=None):
    c, root = checkpoints.c, checkpoints.root
    client = client or PublicEvidenceClient(approved_hosts=c['approved_hosts'], max_bytes=c['max_bytes'])
    documents = list(c.get('documents', []))
    listings, exceptions = [], []
    for d in c.get('discovery', []):
        url = f"https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={d['symbol'].lower()}&Type=1&Year={d['year']}"
        r = checkpoints.acquire(dict(d, kind='list', url=url), client, network)
        listings.append(r)
        if r['status'] != 'COMPLETE':
            exceptions.append(dict(stage='DISCOVERY', symbol=d['symbol'], year=d['year'], reason=r['status']))
            continue
        try:
            path = inside(root, r['payload']['path'], 'data')
            if digest(path.read_bytes()) != r['payload']['sha256']:
                raise ValueError('cached listing hash changed')
            rows = [x for x in consolidated_rows(path.read_bytes(), d['year']) if x['Quarter'] == 5]
            if not rows:
                exceptions.append(dict(stage='DISCOVERY', symbol=d['symbol'], year=d['year'], reason='NO_CONSOLIDATED_ANNUAL_CANDIDATE'))
            for row in rows:
                documents.append(dict(symbol=d['symbol'], year=d['year'], quarter=0, url=row['Link'],
                    provider_report_id=row['id'], provider_name=row['Name'], listing_sha256=r['payload']['sha256']))
        except (ValueError, KeyError, TypeError) as exc:
            exceptions.append(dict(stage='DISCOVERY', symbol=d['symbol'], year=d['year'], reason='INVALID_LISTING', error=str(exc)))
    output, seen = [], set()
    for d in documents:
        key = (d['symbol'], d['year'], d['quarter'], d['url'])
        if key in seen:
            continue
        seen.add(key)
        if len(output) >= c['max_documents']:
            exceptions.append(dict(stage='ACQUIRE', symbol=d['symbol'], year=d['year'], reason='DOCUMENT_CAP', url=d['url']))
            continue
        try:
            r = checkpoints.acquire(dict(d, kind='pdf'), client, network)
        except ValueError as exc:
            exceptions.append(dict(stage='ACQUIRE', symbol=d['symbol'], year=d['year'], reason='UNAPPROVED_ATTACHMENT', url=d['url'], error=str(exc)))
            continue
        output.append(dict(d, acquisition=r, actual_document_identity='UNVERIFIED',
                           publication_date=None, usable_from_date=None, **GATES))
    return dict(listings=listings, documents=output, exceptions=exceptions)


def extract_pdf(checkpoints, document, ocr_script, renderer='pdftoppm', command=subprocess.run):
    c, root = checkpoints.c, checkpoints.root
    acquired = document['acquisition']
    if acquired['status'] != 'COMPLETE':
        return dict(status=acquired['status'], payload={})
    raw = acquired['payload']
    pdf = inside(root, raw['path'], 'data')
    body = pdf.read_bytes()
    if digest(body) != raw['sha256'] or not body.startswith(b'%PDF'):
        raise ValueError('PDF source checksum/signature changed')
    try:
        import pypdf
        from pypdf import PdfReader
    except ImportError:
        request = dict(version=VERSION, operation='PDF_EXTRACTION_DEPENDENCY', pdf_sha256=raw['sha256'])
        old = checkpoints.cached_result(request)
        return old or checkpoints.commit(request, 'DEFERRED_DEPENDENCY', {}, error='pypdf unavailable; use bundled Python')
    binary = shutil.which(renderer)
    engine = dict(pypdf=pypdf.__version__, extractor_sha256=digest(Path(__file__).read_bytes()),
                  ocr_script_sha256=digest(Path(ocr_script).read_bytes()),
                  renderer_sha256=digest(Path(binary).read_bytes()) if binary else 'UNAVAILABLE')
    request = dict(version=VERSION, operation='PDF_TEXT_OCR_CANDIDATE', pdf_sha256=raw['sha256'],
                   max_pdf_pages=c['max_pdf_pages'], ocr_first_pages=c['ocr_first_pages'], engine=engine)
    previous = checkpoints.cached_result(request)
    if previous:
        return previous
    folder = checkpoints.output / 'tasks' / task_key(request)
    try:
        reader = PdfReader(pdf)
        if reader.is_encrypted:
            raise ValueError('encrypted PDF; explicit handling required')
        count = len(reader.pages)
        if time.monotonic() - checkpoints.started >= c['max_seconds']:
            return checkpoints.commit(request, 'DEFERRED_TIME_BUDGET', dict(total_pdf_pages=count))
        if count > c['max_pdf_pages'] or checkpoints.metrics['text_pages'] + count > c['max_text_pages']:
            return checkpoints.commit(request, 'DEFERRED_TEXT_PAGE_BUDGET', dict(total_pdf_pages=count))
        folder.mkdir(parents=True, exist_ok=False)
        pages, planned = [], []
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ''
            file = folder / 'text' / f'page-{number:03d}.txt'
            immutable_write(file, text.encode('utf8'))
            pages.append(dict(pdf_page=number, text_path=str(file.relative_to(root)), text_sha256=digest(file.read_bytes()),
                              text_characters=len(text), low_text=len(text.strip()) < 80))
            if number <= c['ocr_first_pages'] and len(text.strip()) < 80:
                planned.append(number)
        checkpoints.metrics['text_pages'] += count
        ocr_pages, deferred = [], []
        for number in planned:
            if checkpoints.metrics['ocr_pages'] >= c['max_ocr_pages']:
                deferred.append(number)
                continue
            images = folder / f'ocr-{number:03d}'
            images.mkdir()
            checkpoints.metrics['ocr_pages'] += 1
            command([renderer, '-f', str(number), '-l', str(number), '-scale-to', '2200', '-png', str(pdf), str(images / 'page')], check=True, timeout=90)
            command(['powershell.exe', '-NoProfile', '-File', str(ocr_script), '-ImageDirectory', str(images)], check=True, timeout=90)
            records = list(images.glob('*.ocr.json'))
            if len(records) != 1:
                raise ValueError('OCR did not produce exactly one page')
            record = json.loads(records[0].read_bytes())
            image = records[0].with_name(records[0].name.replace('.ocr.json', '.png'))
            if digest(image.read_bytes()) != record['image_sha256']:
                raise ValueError('OCR image checksum mismatch')
            ocr_pages.append(dict(pdf_page=number, image_path=str(image.relative_to(root)), image_sha256=record['image_sha256'],
                                  ocr_path=str(records[0].relative_to(root)), ocr_sha256=digest(records[0].read_bytes())))
        payload = dict(pdf_sha256=raw['sha256'], total_pdf_pages=count, pages=pages, ocr_pages=ocr_pages,
                       deferred_ocr_pages=deferred, extraction_scope='ALL_EMBEDDED_TEXT_AND_BOUNDED_SCAN_PREFIX',
                       acceptance='CANDIDATE_REQUIRES_VISUAL_SEMANTIC_PUBLICATION_REVIEW')
        # A page-cap result can be retried under a new budget; never cache an incomplete OCR plan as complete.
        return checkpoints.commit(request, 'PARTIAL_OCR_BUDGET' if deferred else 'COMPLETE', payload, folder)
    except (ValueError, OSError, subprocess.SubprocessError, getattr(getattr(pypdf, 'errors', None), 'PyPdfError', ValueError)) as exc:
        return checkpoints.commit(request, 'FAILED_PDF_EXTRACTION', {}, folder, str(exc))
