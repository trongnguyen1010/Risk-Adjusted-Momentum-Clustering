"""Financial batch orchestration: evidence, review queue, offline references.

Engineering batch completion and financial acceptance are separate outcomes.
No pipeline switch can approve a methodology, identity, or unreviewed fact.
"""
import json
import unicodedata
from collections import Counter
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded, immutable_write, now
from ..ingestion.financial_batch_evidence import (
    GATES, Checkpoints, collect, extract_pdf, inside, seal, validate,
)
from ..ingestion.financial_documents import verify_inventory

ACCEPTANCE_REQUIREMENTS = [
    'REVIEWED_VALUE_UNIT_PERIOD_SCOPE_FRAMEWORK', 'EXACT_PDF_PUBLICATION_DATE_ALL_INPUTS',
    'REVISION_COMPATIBILITY_AS_OF_SNAPSHOT', 'ACCOUNTING_QA',
    'APPROVED_FEATURE_VARIANTS', 'HISTORICAL_SECURITY_AND_SECTOR_IDENTITY',
    'COMPATIBLE_TTM_AND_EFFECTIVE_SHARE_EVENT_BASIS_FOR_VALUATION',
    'THREE_YEAR_USABLE_HISTORY_FOR_REAL_CLUSTERING', 'FROZEN_SEPARATE_FINANCIAL_PROTOCOL',
]


def normalize(s):
    return ''.join(x for x in unicodedata.normalize('NFKD', s.lower().replace('đ', 'd')) if not unicodedata.combining(x))


def verify_pins(root, pins):
    for name, expected in pins.items():
        file = inside(root, name)
        if digest(file.read_bytes()) != expected:
            raise ValueError('flow input/code checksum mismatch: ' + name)
        if file.name == 'manifest.json':
            verify_inventory(file.parent)


def verify_flow(root, run):
    """Verify the outer run AND the exact external checkpoints/raw/text it reuses."""
    root=Path(root).resolve(); folder=inside(root,run,'data')
    verify_inventory(folder)
    result=json.loads((folder/'results.json').read_bytes())
    config=json.loads((folder/'config.json').read_bytes())
    verify_pins(root,config.get('evidence_pins',{}))
    checked=set()
    records=result['listings']+[d[k] for d in result['documents'] for k in ['acquisition','extraction'] if k in d]
    for record in records:
        if 'checkpoint_path' not in record:
            continue  # extraction skipped because acquisition was not complete
        task=inside(root,record['checkpoint_path'],'data')
        if digest((task/'manifest.json').read_bytes()) != record['checkpoint_manifest_sha256']:
            raise ValueError('reused checkpoint manifest changed')
        if task not in checked:
            verify_inventory(task);checked.add(task)
        receipt=json.loads((task/'result.json').read_bytes())
        if any(receipt[k]!=record[k] for k in ['request','status','payload']):
            raise ValueError('checkpoint receipt/result mismatch')
        payload=record['payload']
        if record['request']['operation']=='ACQUIRE' and record['status']=='COMPLETE':
            if digest(inside(root,payload['path'],'data').read_bytes())!=payload['sha256']:
                raise ValueError('external raw source changed')
        for page in payload.get('pages',[]):
            if digest(inside(root,page['text_path'],'data').read_bytes())!=page['text_sha256']:
                raise ValueError('external PDF text changed')
        for page in payload.get('ocr_pages',[]):
            for kind in ['image','ocr']:
                if digest(inside(root,page[kind+'_path'],'data').read_bytes())!=page[kind+'_sha256']:
                    raise ValueError('external OCR/page changed')
    for adapter in result['reference_runs']:
        manifest=inside(root,adapter['output']+'/manifest.json','data')
        if digest(manifest.read_bytes())!=adapter['manifest_sha256']:
            raise ValueError('reference artifact changed')
        verify_inventory(manifest.parent)
    for line in (folder/'work-log.jsonl').read_text(encoding='utf8').splitlines():json.loads(line)
    if any(result.get(k) is not False for k in GATES) or result['financial_cluster_eligible_rows']!=0:
        raise ValueError('reference flow gate violation')
    return dict(status='PASS',verified_checkpoints=len(checked),gates_closed=True)


def references(root, c, out):
    jobs = c.get('reference_jobs', [])
    if len(jobs) > 2 or len({j['adapter'] for j in jobs}) != len(jobs):
        raise ValueError('at most two reviewed adapters')
    results, rows = [], []
    for j in jobs:
        config = inside(root, j['config'])
        if digest(config.read_bytes()) != j['config_sha256']:
            raise ValueError('reference config changed')
        folder = out / 'references' / j['adapter']
        if j['adapter'] == 'THREE_SYMBOL_2025':
            from .financial_three_symbol_pilot import export
            result = export(root, j['config'], folder.relative_to(root))
            for r in result['results']:
                for name, value in r['metrics'].items():
                    basis = ('RAW_CLOSE_ANNUAL_2025_EPS' if name == 'PE' else
                             'RAW_CLOSE_2025_BOOK_SHARE_SNAPSHOT' if name == 'PB' else 'ANNUAL_2025_REVIEWED_REFERENCE')
                    rows.append(dict(symbol=r['symbol'], decision_at=r['decision_at'], task=name, value=value,
                        basis=basis, period='2025', source_result_path=str((folder/'results.json').relative_to(root)),
                        production_accepted=False, financial_cluster_eligible=False,
                        blockers=['REFERENCE_VARIANT_NOT_PRODUCTION_ACCEPTED', 'HISTORICAL_IDENTITY_UNVERIFIED']
                            + (['INPUTS_MISSING'] if value is None else [])
                            + ([] if r['all_auxiliary_publications_verified'] else ['AUXILIARY_PUBLICATION_UNVERIFIED'])))
                for name, value in [('EPS_TTM', r['ttm']['value']), ('PE_TTM', r['ttm_pe'])]:
                    rows.append(dict(symbol=r['symbol'], decision_at=r['decision_at'], task=name, value=value,
                        period='2025-07-01/2026-06-30', basis='REPORTED_NUMERATOR_SHARE_DAYS_TTM_REFERENCE',
                        source_result_path=str((folder/'results.json').relative_to(root)),
                        production_accepted=False, financial_cluster_eligible=False,
                        blockers=['REFERENCE_VARIANT_NOT_PRODUCTION_ACCEPTED'] + (['TTM_BRIDGE_UNVERIFIED'] if value is None else [])))
        elif j['adapter'] == 'FPT_2025':
            from .financial_fpt_acceptance import export
            result = export(root, j['config'], folder.relative_to(root))
            for r in result['results']:
                for m in r['metrics']:
                    rows.append(dict(symbol='FPT', decision_at=r['decision_at'], task=m['task'], value=m['value'],
                        basis=m['basis'], period=m['period'], source_result_path=str((folder/'results.json').relative_to(root)),
                        production_accepted=False, financial_cluster_eligible=False, blockers=m['limitations']))
        else:
            raise ValueError('unsupported reviewed adapter; do not infer a template from ticker')
        if any(result.get(k) is not False for k in GATES):
            raise ValueError('reference adapter attempted promotion')
        verify_inventory(folder)
        results.append(dict(adapter=j['adapter'], output=str(folder.relative_to(root)),
                            manifest_sha256=digest((folder/'manifest.json').read_bytes())))
    return results, rows


def review_queue(root, documents, exceptions, c):
    queue = list(exceptions)
    for d in documents:
        a, x = d['acquisition'], d.get('extraction', {})
        identity = {k:d[k] for k in ['symbol', 'year', 'quarter', 'url']}
        if a['status'] != 'COMPLETE':
            queue.append(dict(identity, stage='ACQUIRE', reason=a['status'], action='RESOLVE_SOURCE_OR_BUDGET_WITHOUT_BYPASS'))
            continue
        payload = x.get('payload', {})
        hints = []
        for page in payload.get('pages', []):
            text = normalize(inside(root, page['text_path'], 'data').read_text(encoding='utf8'))
            matched = [name for name, terms in c.get('note_search_terms', {}).items() if any(normalize(t) in text for t in terms)]
            if matched:
                hints.append(dict(pdf_page=page['pdf_page'], fields=matched, text_path=page['text_path']))
        queue.append(dict(identity, stage='DOCUMENT_REVIEW', reason='NEW_CANDIDATE_NOT_VISUALLY_ACCEPTED',
            action='VERIFY_ISSUER_SCOPE_VAS_VINTAGE_THEN_REVIEW_FIELDS_AND_PUBLICATION',
            pdf_path=a['payload']['path'], pdf_sha256=a['payload']['sha256'],
            extraction_status=x.get('status', 'NOT_EXECUTED'), page_hints=hints[:12],
            hint_count=len(hints), ocr_pages=payload.get('ocr_pages', []),
            low_text_pages=sum(p['low_text'] for p in payload.get('pages', [])),
            required_checks=ACCEPTANCE_REQUIREMENTS[:4], financial_cluster_eligible=False))
        if x.get('status') != 'COMPLETE':
            queue.append(dict(identity, stage='EXTRACT', reason=x.get('status', 'NOT_EXECUTED'),
                              action='RESOLVE_DEPENDENCY_PAGE_BUDGET_OR_EXTRACTION_EXCEPTION'))
    blockers = c.get('known_blockers')
    if blockers:
        file = inside(root, blockers['path'])
        if digest(file.read_bytes()) != blockers['sha256']:
            raise ValueError('blocker input checksum mismatch')
        queue.extend(dict(b, stage='PILOT_ACCEPTANCE', reason='OPEN_PILOT_BLOCKER', action='CLOSE_EXACT_INPUT_EVIDENCE')
                     for b in json.loads(file.read_bytes()))
    return queue


def run(root, config_path, output, resume_runs=(), network=False, stop_after=None, client=None, command=None):
    root = Path(root).resolve()
    path = inside(root, config_path)
    c = validate(json.loads(path.read_bytes()))
    if stop_after not in [None, 'acquire']:
        raise ValueError('invalid stage boundary')
    verify_pins(root, c.get('code_sha256', {}))
    # Source pins and review inputs are checked before any network or output mutation.
    verify_pins(root, c.get('evidence_pins', {}))
    out = inside(root, output, 'data')
    if out.exists():
        raise ValueError('immutable output already exists; choose a new run and --resume-from')
    cp = Checkpoints(root, out, c, resume_runs)
    out.mkdir(parents=True, exist_ok=False)
    immutable_write(out / 'config.json', path.read_bytes())
    log = []
    def event(stage, **details):
        log.append(dict(at=now(), stage=stage, **details))
        # Each log event is sealed independently; interrupted parents retain meaningful checkpoints.
        immutable_write(out / 'events' / f'{len(log):04d}.json', encoded(log[-1]))
        print(json.dumps(log[-1], ensure_ascii=False), flush=True)
    event('START', mode='BOUNDED_NETWORK' if network else 'OFFLINE', symbols=c['symbols'])
    acquired = collect(cp, network=network, client=client)
    event('ACQUIRE', documents=len(acquired['documents']), metrics=dict(cp.metrics), boundary=cp.boundary)
    docs = acquired['documents']
    reference_runs, metric_rows = [], []
    if stop_after is None:
        for d in docs:
            kwargs = {} if command is None else dict(command=command)
            d['extraction'] = extract_pdf(cp, d, root/'scripts/ocr_financial_pages.ps1', **kwargs)
            event('EXTRACT', symbol=d['symbol'], year=d['year'], status=d['extraction']['status'],
                  pdf_sha256=d['acquisition']['payload'].get('sha256'))
        reference_runs, metric_rows = references(root, c, out)
        event('REFERENCE', runs=len(reference_runs), metric_rows=len(metric_rows))
    queue = review_queue(root, docs, acquired['exceptions'], c)
    unique = {d['acquisition']['payload']['sha256'] for d in docs if d['acquisition']['status'] == 'COMPLETE'}
    failures = sum(d['acquisition']['status'] != 'COMPLETE' or d.get('extraction', {}).get('status') != 'COMPLETE' for d in docs)
    engineering = ('STOPPED_AFTER_ACQUIRE' if stop_after else 'HARD_STOP' if cp.boundary else
                   'PARTIAL' if failures or acquired['exceptions'] or not docs else 'COMPLETE')
    result = dict(version='financial-batch-flow-v1', engineering_status=engineering,
        acceptance_status='PARTIAL_REFERENCE_ONLY', network_enabled=network,
        source_scope='FROZEN_DISCOVERY_CACHE_EPOCH_NOT_A_LIVE_LATEST_FEED', cache_epoch=c['cache_epoch'],
        symbols=c['symbols'], metrics=cp.metrics, documents=docs, listings=acquired['listings'],
        unique_acquired_pdf_hashes=len(unique), acquired_document_candidates=sum(d['acquisition']['status']=='COMPLETE' for d in docs),
        review_queue_items=len(queue), queue_counts=dict(Counter(q['stage'] for q in queue)),
        reference_runs=reference_runs, reference_metric_rows=len(metric_rows),
        reference_values_available=sum(r['value'] is not None for r in metric_rows),
        production_accepted_metric_rows=0, financial_cluster_eligible_rows=0,
        cluster_acceptance_requirements=ACCEPTANCE_REQUIREMENTS, **GATES)
    event('FINISH', engineering_status=engineering, acceptance_status=result['acceptance_status'], metrics=cp.metrics)
    immutable_write(out/'results.json', encoded(result))
    immutable_write(out/'review-queue.json', encoded(queue))
    immutable_write(out/'reference-metrics.json', encoded(metric_rows))
    immutable_write(out/'work-log.jsonl', ''.join(json.dumps(e, ensure_ascii=False, sort_keys=True)+'\n' for e in log).encode('utf8'))
    for name in ['financial_batch_flow.py']:
        immutable_write(out/name, Path(__file__).read_bytes())
    immutable_write(out/'financial_batch_evidence.py', (root/'src/delta_t1/ingestion/financial_batch_evidence.py').read_bytes())
    md = f'''# Financial batch flow

Engineering: **{engineering}**. Acceptance: **PARTIAL_REFERENCE_ONLY**.

Flow: discovery/cache → raw PDF → embedded text → bounded scan-prefix OCR →
review queue → approved offline reference adapters → per-metric gate report.

{result['acquired_document_candidates']} document candidates, {len(unique)} unique PDF hashes.
Network logical calls: {cp.metrics['logical_requests']}; at most two HTTP attempts per logical call.
Cache hits: {cp.metrics['cache_hits']}; new text pages: {cp.metrics['text_pages']}; new OCR attempts: {cp.metrics['ocr_pages']}.
Review queue: {len(queue)} items. Reference values: {result['reference_values_available']}/{len(metric_rows)} rows,
including separate periods/bases and decisions; this is not a completion percentage.
Production/cluster-eligible rows: **0**.

## Sử dụng

Mở `review-queue.json` để xử lý issuer/scope/framework, kỳ, mapping, publication và revision.
OCR prefix chỉ hỗ trợ discovery; thuyết minh ngoài prefix cần chọn trang riêng.
Một PDF cùng URL/cache epoch là frozen evidence, không đảm bảo đó là báo cáo mới nhất.
Muốn refresh phải tạo epoch/run mới và giữ mọi vintage; không áp bản mới ngược lịch sử.
Run mới dùng `--resume-from` để đọc checkpoint có manifest; không ghi đè run cũ.
HARD_STOP trong lineage chặn network khi resume đến khi có review nguồn/access riêng.
COMPLETE engineering không mở gate financial và không chứng nhận throughput của 1.000 mã.

Các đầu vào thiếu giữ null; các giá trị reference không được ghép thành vector clustering.
Không thay protocol market-only. Gate financial cần các điều kiện trong `results.json`
và nghiệm thu độc lập trước một protocol financial riêng.
'''
    immutable_write(out/'report.md', md.encode('utf8'))
    seal(out)
    verify_flow(root,out.relative_to(root))
    return result
