"""User-facing bounded crawler: structured candidates, PDFs, QA, exports, replay."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded, immutable_write, now
from ..ingestion.cafef_financial_detail import PublicEvidenceClient
from ..ingestion.financial_batch_evidence import GATES, VERSION, Checkpoints, inside, seal, validate, validate_url
from ..ingestion.financial_documents import consolidated_rows, verify_inventory
from ..ingestion.financial_crawl_candidates import candidates, csv_bytes, structured_request, summarize
from ..ingestion.financial_crawl_pdf import extract
from .financial_batch_flow import verify_flow

USER_VERSION = 'financial-crawl-user-v1'
DEFAULT_HOSTS = ['kbbuddywts.kbsec.com.vn', 'cafef.vn', 'cafefnew.mediacdn.vn']
DEFAULT_BUDGETS = dict(max_logical_requests=60, max_pdf_downloads=20, max_documents=20,
    max_bytes=50_000_000, max_total_bytes=250_000_000, max_pdf_pages=250,
    max_text_pages=1500, max_ocr_pages=48, ocr_first_pages=0, max_seconds=1800)


def prepare(user):
    if user.get('version') != USER_VERSION:
        raise ValueError('expected version ' + USER_VERSION)
    if any(user.get(k, False) is not False for k in GATES):
        raise ValueError('candidate crawler cannot enable financial/research/full-universe gates')
    periods = user.get('periods', ['year'])
    pages = user.get('structured_pages', [1])
    if not isinstance(periods, list) or not periods or len(set(periods)) != len(periods) or any(p not in ['year', 'quarter'] for p in periods):
        raise ValueError('invalid periods')
    if not isinstance(pages, list) or not pages or len(set(pages)) != len(pages) or any(type(p) is not int or not 1 <= p <= 3 for p in pages):
        raise ValueError('structured_pages must be unique pages 1..3; no inferred pagination')
    symbols = user['symbols']
    types = user['company_types']
    if not isinstance(types, dict) or set(types) != set(symbols) or any(v not in ['Regular', 'Bank', 'Securities', 'Insurance'] for v in types.values()):
        raise ValueError('explicit company_types required for every symbol')
    for flag in ['pdf_discovery', 'pdf_extract']:
        if type(user.get(flag, True)) is not bool:
            raise ValueError('invalid ' + flag)
    quarters = user.get('pdf_quarters', [0])
    if not isinstance(quarters, list) or not quarters or len(set(quarters)) != len(quarters) or any(type(q) is not int or q not in range(5) for q in quarters):
        raise ValueError('invalid pdf_quarters')
    if not set(user.get('budgets', {})) <= set(DEFAULT_BUDGETS):
        raise ValueError('unknown budget name')
    if user.get('budgets', {}).get('ocr_first_pages', 0) != 0:
        raise ValueError('use explicit document ocr_pages, not prefix OCR')
    c = dict(version=VERSION, cache_epoch=user['cache_epoch'], symbols=symbols, years=user['years'],
        approved_hosts=user.get('approved_hosts', DEFAULT_HOSTS), documents=user.get('documents', []),
        discovery=[], cache_records=[], **(DEFAULT_BUDGETS | user.get('budgets', {})), **GATES)
    validate(c)
    if len(symbols) > 10:
        raise ValueError('pilot acceptance limit: at most 10 symbols per user run')
    for d in c['documents']:
        selected = d.get('ocr_pages', [])
        if not isinstance(selected, list) or len(set(selected)) != len(selected) or any(type(p) is not int or not 1 <= p <= c['max_pdf_pages'] for p in selected):
            raise ValueError('invalid explicit OCR page selection')
        templates = d.get('cell_templates', [])
        if templates:
            sha = d.get('pdf_sha256', '')
            if len(sha) != 64 or any(x not in '0123456789abcdef' for x in sha):
                raise ValueError('cell templates require exact pdf_sha256')
        for spec in templates:
            if spec['pdf_page'] not in selected or type(spec['year']) is not int or spec['year'] not in c['years']:
                raise ValueError('template outside OCR/target years')
            if 'box' in spec:
                box = spec['box']
                if len(box) != 4 or any(type(x) not in (int, float) or not 0 <= x <= 1 for x in box) or box[0] >= box[2] or box[1] >= box[3]:
                    raise ValueError('invalid normalized cell rectangle')
            elif not isinstance(spec.get('row_code'), str):
                raise ValueError('template requires a row_code or box')
            if 'reference_value' in spec and type(spec['reference_value']) is not int:
                raise ValueError('OCR reference must be an integer with declared template unit')
    return c


def doctor(user):
    c = prepare(user)
    needs_pdf = user.get('pdf_extract', True) and (user.get('pdf_discovery', True) or bool(c['documents']))
    deps = dict(python_version=sys.version.split()[0], python_executable=sys.executable,
        pypdf=importlib.util.find_spec('pypdf') is not None,
        pdftoppm=shutil.which('pdftoppm'), powershell=shutil.which('powershell.exe'))
    missing = []
    if sys.version_info < (3, 11):
        missing.append('Python >=3.11')
    if needs_pdf and not deps['pypdf']:
        missing.append('pypdf==6.10.0 for PDF text extraction')
    if any(d.get('ocr_pages') for d in c['documents']):
        if not deps['pdftoppm']:
            missing.append('Poppler pdftoppm on PATH')
        if not deps['powershell']:
            missing.append('Windows PowerShell with Windows en-US OCR')
    warnings = []
    planned = len(c['symbols'])*len(user.get('periods', ['year']))*3*len(user.get('structured_pages', [1]))
    if planned > c['max_logical_requests']:
        warnings.append('structured request plan exceeds budget; remaining jobs will be explicitly deferred')
    if any(d.get('ocr_pages') for d in c['documents']) and deps['powershell']:
        probe = "Add-Type -AssemblyName System.Runtime.WindowsRuntime; [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] > $null; [Windows.Globalization.Language,Windows.Foundation,ContentType=WindowsRuntime] > $null; if ($null -eq [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('en-US'))) { exit 5 }"
        try:
            p = subprocess.run([deps['powershell'], '-NoProfile', '-Command', probe], capture_output=True, timeout=20)
            deps['windows_en_us_ocr'] = p.returncode == 0
            if p.returncode:
                missing.append('Windows en-US OCR engine unavailable')
        except (OSError, subprocess.SubprocessError):
            missing.append('Windows OCR preflight failed')
    return dict(status='READY' if not missing else 'MISSING_DEPENDENCIES', dependencies=deps,
                missing=missing, network_executed=False, symbols=len(c['symbols']),
                warnings=warnings, planned_structured_requests=planned,
                request_budget=c['max_logical_requests'])


def seed_records(root, runs, c):
    records = []
    for relative in runs:
        run = inside(root, relative, 'data')
        manifest = verify_inventory(run)
        inv = json.loads((run/'inventory.json').read_bytes())
        for r in inv.get('requests', inv.get('documents', [])):
            if r.get('status') not in ['RAW_JSON_CAPTURED', 'DOWNLOADED']:
                continue
            url = r.get('url', r.get('provider_report', {}).get('Link'))
            if not url:
                continue
            validate_url(url, c['approved_hosts'])
            path = Path(r['path'])
            path = path.resolve() if path.is_absolute() else (run/path).resolve()
            if not path.is_relative_to(run) or manifest['files'].get(path.relative_to(run).as_posix()) != r['sha256']:
                raise ValueError('seed path/checksum outside exact manifest')
            kind = 'structured' if r['status'] == 'RAW_JSON_CAPTURED' else 'pdf'
            records.append(dict(run=run.relative_to(root).as_posix(), path=path.relative_to(root).as_posix(),
                kind=kind, url=url, sha256=r['sha256'], manifest_sha256=digest((run/'manifest.json').read_bytes())))
    return records


def verify_seed_receipts(root, receipts):
    data_root = Path(root).resolve()/'data'
    checked = set()
    for receipt in receipts:
        pin = receipt.get('payload', {}).get('source_manifest_sha256')
        if receipt['status'] != 'COMPLETE' or not pin:
            continue
        raw = inside(root, receipt['payload']['path'], 'data')
        matches = [parent for parent in raw.parents if parent.is_relative_to(data_root)
                   and (parent/'manifest.json').exists() and digest((parent/'manifest.json').read_bytes()) == pin]
        if len(matches) != 1:
            raise ValueError('seed source manifest changed or missing')
        if matches[0] not in checked:
            verify_inventory(matches[0])
            checked.add(matches[0])


def discover(cp, user, client, network):
    documents, listings, exceptions = list(cp.c['documents']), [], []
    if user.get('pdf_discovery', True):
        for symbol in cp.c['symbols']:
            for year in cp.c['years']:
                url = f'https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={symbol.lower()}&Type=1&Year={year}'
                r = cp.acquire(dict(symbol=symbol, year=year, kind='list', url=url), client, network)
                listings.append(r)
                if r['status'] != 'COMPLETE':
                    exceptions.append(dict(stage='PDF_DISCOVERY', symbol=symbol, year=year, reason=r['status']))
                    continue
                try:
                    body = inside(cp.root, r['payload']['path'], 'data').read_bytes()
                    if digest(body) != r['payload']['sha256']:
                        raise ValueError('listing integrity mismatch')
                    rows = [x for x in consolidated_rows(body, year)
                            if (0 if x['Quarter'] == 5 else x['Quarter']) in user.get('pdf_quarters', [0])]
                    for row in rows:
                        documents.append(dict(symbol=symbol, year=year, quarter=0 if row['Quarter'] == 5 else row['Quarter'],
                            url=row['Link'], provider_report_id=row['id'], provider_name=row['Name'],
                            listing_sha256=r['payload']['sha256'], ocr_pages=[]))
                    for q in user.get('pdf_quarters', [0]):
                        if not any((0 if x['Quarter'] == 5 else x['Quarter']) == q for x in rows):
                            exceptions.append(dict(stage='PDF_DISCOVERY', symbol=symbol, year=year, quarter=q, reason='NO_CONSOLIDATED_DOCUMENT_CANDIDATE'))
                except (ValueError, KeyError, TypeError) as exc:
                    exceptions.append(dict(stage='PDF_DISCOVERY', symbol=symbol, year=year, reason='INVALID_LISTING', error=str(exc)))
    result, seen = [], set()
    for d in documents:
        key = (d['symbol'], d['year'], d['quarter'], d['url'])
        if key in seen:
            continue  # explicit input precedes discovery, preserving explicit page selections
        seen.add(key)
        if len(result) >= cp.c['max_documents']:
            exceptions.append(dict(stage='PDF_ACQUIRE', symbol=d['symbol'], year=d['year'], reason='DOCUMENT_CAP', url=d['url']))
            continue
        try:
            # Extraction instructions are not HTTP request identity.
            item = {k:v for k,v in d.items() if k not in ['ocr_pages', 'cell_templates', 'pdf_sha256']}
            acquired = cp.acquire(dict(item, kind='pdf'), client, network)
            if acquired['status'] == 'COMPLETE' and d.get('pdf_sha256') and acquired['payload']['sha256'] != d['pdf_sha256']:
                raise ValueError('exact template PDF checksum mismatch')
            result.append(dict(d, acquisition=acquired, publication_date=None, usable_from_date=None, **GATES))
        except ValueError as exc:
            exceptions.append(dict(stage='PDF_ACQUIRE', symbol=d['symbol'], year=d['year'], reason='DOCUMENT_REVIEW_REQUIRED', error=str(exc)))
    return listings, result, exceptions


def run(root, config_path, output, resume_runs=(), seed_runs=(), network=False, client=None, command=None):
    root = Path(root).resolve()
    user = json.loads(inside(root, config_path).read_bytes())
    c = prepare(user)
    environment = doctor(user)
    if environment['status'] != 'READY':
        raise ValueError('preflight failed: ' + '; '.join(environment['missing']))
    c['cache_records'] = seed_records(root, seed_runs, c)
    validate(c)
    out = inside(root, output, 'data')
    # Verify all incoming dependencies before creating or sending anything.
    cp = Checkpoints(root, out, c, resume_runs)
    verify_seed_receipts(root, [receipt for receipt, folder in cp.cached.values()])
    out.mkdir(parents=True, exist_ok=False)
    immutable_write(out/'config.json', encoded(c))
    immutable_write(out/'user-config.json', encoded(user))
    immutable_write(out/'environment.json', encoded(environment))
    code = {}
    paths = ['src/delta_t1/experiments/financial_crawl.py', 'src/delta_t1/ingestion/financial_crawl_candidates.py',
             'src/delta_t1/ingestion/financial_crawl_pdf.py', 'src/delta_t1/ingestion/financial_provider_normalize.py',
             'src/delta_t1/ingestion/financial_batch_evidence.py', 'src/delta_t1/ingestion/cafef_financial_detail.py',
             'src/delta_t1/ingestion/cafef_financial.py', 'src/delta_t1/ingestion/financial_documents.py',
             'src/delta_t1/ingestion/financial_table_parser.py', 'src/delta_t1/ingestion/sources/base.py',
             'scripts/ocr_financial_pages.ps1', 'scripts/crawl_financial.py', 'scripts/crawl_financial.ps1']
    for path in paths:
        source = root/path
        if source.exists():
            body = source.read_bytes()
            immutable_write(out/'code'/path, body)
            code[path] = digest(body)
    immutable_write(out/'code-pins.json', encoded(code))
    client = client or PublicEvidenceClient(approved_hosts=c['approved_hosts'], max_bytes=c['max_bytes'])
    def log(stage, **data):
        line = dict(at=now(), stage=stage, **data)
        with (out/'work-log.jsonl').open('a', encoding='utf8') as f:
            f.write(json.dumps(line, ensure_ascii=False) + '\n')
        print(json.dumps(line, ensure_ascii=False), flush=True)
    log('START', symbols=c['symbols'], mode='NETWORK' if network else 'OFFLINE')
    cells, structured, exceptions = [], [], []
    for symbol in c['symbols']:
        for period in user.get('periods', ['year']):
            for page in user.get('structured_pages', [1]):
                for report in ['CDKT', 'KQKD', 'LCTT']:
                    request = structured_request(symbol, report, period, page)
                    receipt = cp.acquire(request, client, network)
                    parsed = dict(request, acquisition=receipt, status=receipt['status'])
                    if receipt['status'] == 'COMPLETE':
                        try:
                            body = inside(root, receipt['payload']['path'], 'data').read_bytes()
                            if digest(body) != receipt['payload']['sha256']:
                                raise ValueError('structured raw integrity mismatch')
                            raw_path = 'raw/' + receipt['payload']['sha256'] + '.json'
                            if not (out/raw_path).exists():
                                immutable_write(out/raw_path, body)
                            def reject_constant(token):
                                raise ValueError('nonfinite JSON number: ' + token)
                            rows = candidates(json.loads(body, parse_constant=reject_constant), dict(request, path=raw_path,
                                sha256=receipt['payload']['sha256']), c['years'], user['company_types'][symbol])
                            cells.extend(rows)
                            parsed.update(status='PARSED_CANDIDATES' if rows else 'EMPTY_RESPONSE', wire_cells=len(rows))
                        except (ValueError, KeyError, TypeError) as exc:
                            parsed.update(status='INVALID_PROVIDER_PAYLOAD', error=str(exc))
                    if parsed['status'] != 'PARSED_CANDIDATES':
                        exceptions.append(dict(stage='STRUCTURED', symbol=symbol, report=report, period=period, reason=parsed['status']))
                    structured.append(parsed)
                    log('STRUCTURED', symbol=symbol, period=period, report=report, page=page, status=parsed['status'])
    listings, documents, doc_errors = discover(cp, user, client, network)
    exceptions.extend(doc_errors)
    for d in documents:
        if user.get('pdf_extract', True):
            kwargs = dict(command=command) if command else {}
            d['extraction'] = extract(cp, d, root/'scripts/ocr_financial_pages.ps1', **kwargs)
        else:
            d['extraction'] = dict(status='EXTRACTION_NOT_REQUESTED', payload={})
        log('PDF', symbol=d['symbol'], year=d['year'], acquisition=d['acquisition']['status'], extraction=d['extraction']['status'])
    summary = summarize(cells, dict(user, periods=user.get('periods', ['year'])))
    queue = [dict(stage='CORE_MAPPING', **r) for r in summary['coverage'] if r['missing_core_fields']]
    queue += [dict(stage='RECONCILIATION', **r) for r in summary['conflicts']]
    queue += [dict(stage='ACCOUNTING', **r) for r in summary['accounting_qa'] if r['status'] != 'CANDIDATE_ARITHMETIC_PASS']
    queue += [dict(stage='STRUCTURED_SEMANTICS_RELEASE', symbol=r['symbol'], report=r['report'], year=r['year'],
        quarter=r['quarter'], required=['VALUE_UNIT_SCOPE_FRAMEWORK', 'DURATION_OR_INSTANT', 'EXACT_VINTAGE_PUBLICATION',
                                      'REVISIONS_AND_AS_OF_COMPATIBILITY'], financial_features_allowed=False)
        for r in summary['coverage'] if r['fields_with_candidates']]
    ambiguous_headers = {(r['symbol'],r['report'],r['source_sha256'],r['column']):r for r in cells
                         if r['header_status']=='AMBIGUOUS_DUPLICATED_PERIOD_COLUMNS'}
    queue += [dict(stage='PROVIDER_HEADER_REVIEW', symbol=r['symbol'], report=r['report'], column=r['column'],
                   header=r['header'], source_sha256=r['source_sha256'], reason=r['header_status'],
                   financial_features_allowed=False) for r in ambiguous_headers.values()]
    queue += exceptions
    for d in documents:
        p = d['extraction']['payload']
        queue.append(dict(stage='DOCUMENT_SEMANTICS_PUBLICATION', symbol=d['symbol'], year=d['year'], quarter=d['quarter'],
            url=d['url'], pdf_sha256=d['acquisition']['payload'].get('sha256'),
            acquisition_status=d['acquisition']['status'], extraction_status=d['extraction']['status'],
            acquisition_error=d['acquisition'].get('error'), extraction_error=d['extraction'].get('error'),
            low_text_pages=p.get('low_text_pages', []), selected_ocr_pages=[r['pdf_page'] for r in p.get('ocr_pages', [])],
            deferred_ocr_pages=p.get('deferred_ocr_pages', []),
            required=['PDF_IDENTITY_SCOPE_FRAMEWORK', 'VALUE_UNIT_PERIOD', 'PUBLICATION_EXACT_VINTAGE', 'REVISIONS'],
            financial_features_allowed=False))
    if not documents:
        queue.append(dict(stage='DOCUMENT_SEMANTICS_PUBLICATION', reason='NO_DOCUMENT_EVIDENCE_IN_RUN', financial_features_allowed=False))
    complete = not exceptions and all(r['status'] == 'PARSED_CANDIDATES' for r in structured)
    complete &= all(d['acquisition']['status'] == 'COMPLETE' and
                    d['extraction']['status'] in ('COMPLETE', 'EXTRACTION_NOT_REQUESTED') for d in documents)
    status = 'HARD_STOP' if cp.boundary else 'COMPLETE' if complete else 'PARTIAL'
    result = dict(version=USER_VERSION, engineering_status=status, acceptance_status='UNVERIFIED_CANDIDATES_ONLY',
        coverage_status='CANDIDATE_CORE_PRESENT' if all(not r['missing_core_fields'] for r in summary['coverage']) else 'PARTIAL',
        structured=structured, listings=[r['acquisition'] for r in structured]+listings,
        documents=documents, exceptions=exceptions, metrics=cp.metrics, summary=summary,
        review_queue_items=len(queue), reference_runs=[], financial_cluster_eligible_rows=0, **GATES)
    immutable_write(out/'candidates.jsonl', ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True,
        allow_nan=False)+'\n' for r in cells).encode('utf8'))
    immutable_write(out/'candidates.csv', csv_bytes(cells, ['symbol', 'report', 'year', 'quarter', 'field', 'label',
        'raw_value', 'value', 'unit', 'status', 'in_target', 'header', 'source_path', 'source_sha256']))
    immutable_write(out/'coverage.csv', csv_bytes(summary['coverage'], ['symbol', 'report', 'year', 'quarter',
        'wire_cells', 'fields_with_candidates', 'missing_core_fields', 'status', 'verified']))
    immutable_write(out/'review-queue.json', encoded(queue))
    immutable_write(out/'results.json', encoded(result))
    report = f'''# Kết quả financial crawler

Collection: **{status}**. Coverage: **{result['coverage_status']}**.
{len(c['symbols'])} mã; {summary['wire_cells']} wire cells; {summary['in_target_cells']} cells trong target.
Accepted facts: **0**; financial cluster eligible: **0**.

Structured requests thành công: {sum(r['status']=='PARSED_CANDIDATES' for r in structured)}/{len(structured)}.
PDF candidates: {len(documents)}; text pages mới: {cp.metrics['text_pages']}; OCR attempts mới: {cp.metrics['ocr_pages']}.
Network logical calls: {cp.metrics['logical_requests']}; cache hits: {cp.metrics['cache_hits']}.

Xem `coverage.csv` để biết mã/kỳ/field còn thiếu, `review-queue.json` để xử lý,
`candidates.jsonl` để xem raw/header/provenance và `work-log.jsonl` để theo dõi quá trình.
CSV là bản xem thuận tiện; JSONL/raw mới giữ đầy đủ kiểu dữ liệu null/numeric.
Accounting QA chỉ kiểm tra arithmetic trên candidate cùng header/response; không chứng minh
PIT, đơn vị, nguồn gốc hay đúng định nghĩa score. Quarterly flow chưa được gán standalone/YTD.
Provider dates không thành publication; không chọn latest vintage hoặc điền missing=0.
Tài liệu scan chưa OCR toàn bộ vẫn nằm trong review queue kể cả Collection COMPLETE.

Tiếp tục: cấu hình đúng trang OCR/template theo exact PDF, chạy output mới với resume-from;
review value/unit/scope và publication; dùng các reference calculators đã được review riêng.
Mở accepted-data scale và financial clustering cần acceptance policy/protocol riêng.
'''
    immutable_write(out/'report.md', report.encode('utf8'))
    log('FINISH', engineering_status=status, wire_cells=summary['wire_cells'], metrics=cp.metrics)
    seal(out)
    verify(root, out.relative_to(root).as_posix())
    return result


def verify(root, relative):
    result = verify_flow(root, relative)
    out = inside(root, relative, 'data')
    flow = json.loads((out/'results.json').read_bytes())
    verify_seed_receipts(root, flow['listings']+[d['acquisition'] for d in flow['documents']])
    for line in (out/'candidates.jsonl').read_text(encoding='utf8').splitlines():
        cell = json.loads(line)
        path = (out/cell['source_path']).resolve()
        if not path.is_relative_to(out) or digest(path.read_bytes()) != cell['source_sha256']:
            raise ValueError('portable candidate raw integrity mismatch')
    return result
