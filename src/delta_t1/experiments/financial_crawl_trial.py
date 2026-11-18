"""Explicit bounded 50-symbol experiment; pilot runner and feature gates stay closed."""
import csv
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded, immutable_write, now
from ..ingestion.financial_batch_evidence import Checkpoints, GATES, inside, seal, validate_url
from ..ingestion.financial_crawl_candidates import candidates, csv_bytes, structured_request, summarize
from ..ingestion.financial_documents import consolidated_rows, verify_inventory
from ..ingestion.financial_task_readiness import ANNUAL_TASKS, EXTERNAL
from ..ingestion.financial_trial_transport import TrialTransport, TrialBudgetError, read_ledger
from .financial_batch_flow import verify_flow

VERSION = 'financial-crawl-trial-v1'
REPORTS = ['CDKT','KQKD','LCTT']
CAPS = dict(max_logical_requests=450, max_transport_attempts=900,
    max_pdf_download_attempts=20, max_wall_seconds=14400, max_response_bytes=50000000,
    max_total_downloaded_bytes=600000000, max_pdf_pages_per_document=250,
    max_total_text_pages=1000, max_total_selected_ocr_pages=40,
    max_attempts_per_request=2, timeout_seconds=20)
CLOSED = dict(**GATES, financial_cluster_allowed=False, unattended_numeric_acceptance_allowed=False)


def prepare(root, user):
    root = Path(root).resolve()
    if user.get('version') != VERSION or any(user.get(k, False) is not False for k in CLOSED):
        raise ValueError('bounded trial contract with closed gates required')
    path = inside(root, user['plan_path'], 'configs')
    if digest(path.read_bytes()) != user['plan_sha256']:
        raise ValueError('frozen planning input changed')
    plan = json.loads(path.read_bytes())
    if plan.get('branch') and (root/'.git').exists():
        branch = subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True,timeout=5).strip()
        if branch!=plan['branch']:
            raise ValueError('wrong branch for this trial: '+branch)
    members = plan['members']
    symbols = [m['ticker'] for m in members]
    if not 1 <= len(symbols) <= 50 or len(set(symbols)) != len(symbols):
        raise ValueError('trial supports at most 50 unique plan members')
    if plan['version'] != 'financial-crawl-50-plan-v1' or plan.get('executable') is not False:
        raise ValueError('expected frozen planning contract')
    source = inside(root, plan['universe_source']['path'], 'artifacts')
    if digest(source.read_bytes()) != plan['universe_source']['sha256']:
        raise ValueError('market membership snapshot changed')
    rows = list(csv.DictReader(source.read_text(encoding='utf-8-sig').splitlines()))
    for m in members:
        found = [r for r in rows if r['ticker'] == m['ticker'] and r['security_id'] == m['security_id']]
        if len(found) != 1 or found[0]['market_feature_ready_v2'] != 'True':
            raise ValueError('trial member not uniquely ready at frozen market snapshot')
        if m['proposed_company_type'] not in ('Regular','Bank','Securities','Insurance'):
            raise ValueError('invalid proposed company type')
    flattened = [s for w in plan['waves'] for s in w['symbols']]
    if flattened != symbols or any(not 1 <= len(w['symbols']) <= 10 for w in plan['waves']):
        raise ValueError('ordered waves must partition the plan, at most ten per wave')
    b = user['budgets']
    if set(b) != set(CAPS)|{'min_seconds_between_transport_attempts'}:
        raise ValueError('unknown or missing trial budget')
    for key, cap in CAPS.items():
        low = 0 if key in ('max_pdf_download_attempts','max_total_selected_ocr_pages') else 1
        if type(b[key]) is not int or not low <= b[key] <= cap:
            raise ValueError('invalid trial cap: '+key)
    if type(b['min_seconds_between_transport_attempts']) not in (int,float) or not 2 <= b['min_seconds_between_transport_attempts'] <= 60:
        raise ValueError('trial interval must be 2..60 seconds')
    for key in ['annual_years','quarter_years','score_years']:
        v = user[key]
        if not isinstance(v,list) or not v or len(v)!=len(set(v)) or any(type(y) is not int or not 2019<=y<=2026 for y in v):
            raise ValueError('invalid '+key)
    if not set(user['score_years']) <= set(user['annual_years']):
        raise ValueError('score years outside annual target')
    if not isinstance(user['cache_epoch'],str) or not user['cache_epoch']:
        raise ValueError('explicit shared cache epoch required')
    if user['approved_hosts'] != sorted(set(user['approved_hosts'])) or not user['approved_hosts']:
        raise ValueError('sorted unique approved hosts required')
    for key, cap in [('history_requests',90),('document_requests',60),('document_symbols',20)]:
        if type(user[key]) is not int or not 0 <= user[key] <= cap:
            raise ValueError('invalid '+key)
    if type(user['documents_enabled']) is not bool:
        raise ValueError('documents_enabled must be boolean')
    for d in user['explicit_documents']:
        if d['symbol'] not in symbols or d['year'] not in user['annual_years'] or d['quarter'] != 0:
            raise ValueError('explicit document outside trial')
        validate_url(d['url'],user['approved_hosts'])
        if d.get('ocr_pages') or d.get('cell_templates'):
            raise ValueError('trial v1 exports scan-page queue; selected numeric OCR uses reviewed pilot runner separately')
    c = dict(user, symbols=symbols, years=user['annual_years'], documents=[], cache_records=[],
        max_logical_requests=b['max_logical_requests'], max_pdf_downloads=b['max_pdf_download_attempts'],
        max_bytes=b['max_response_bytes'], max_total_bytes=b['max_total_downloaded_bytes'],
        max_documents=20, max_pdf_pages=b['max_pdf_pages_per_document'],
        max_text_pages=b['max_total_text_pages'], max_ocr_pages=0, ocr_first_pages=0,
        max_seconds=b['max_wall_seconds'], **CLOSED)
    return plan, c


def doctor(root, user):
    plan, c = prepare(root,user)
    missing = []
    if sys.version_info < (3,11):
        missing.append('Python >=3.11')
    if user['documents_enabled'] and not importlib.util.find_spec('pypdf'):
        missing.append('pypdf==6.10.0; install configs/data/financial_crawl_requirements.txt')
    disk = shutil.disk_usage(root).free
    if disk < 2_000_000_000:
        missing.append('At least 2 GB free workspace disk space')
    return dict(status='READY' if not missing else 'MISSING_DEPENDENCIES', missing=missing,
        python=sys.executable, free_disk_bytes=disk, symbols=len(c['symbols']),
        base_requests=len(c['symbols'])*6, max_logical_requests=c['max_logical_requests'],
        documents_enabled=user['documents_enabled'], ocr_scope='SCAN_QUEUE_ONLY',
        network_executed=False, classification='SOURCE_HEADER_CHECK_THEN_CANDIDATE_ONLY', **CLOSED)


def load_resume(root, relatives, user_hash):
    """Exactly one most-recent parent preserves a single trial-wide counter lineage."""
    if len(relatives)>1:
        raise ValueError('use only the most recent parent; it preserves transitive checkpoints')
    if not relatives:
        return None
    parent = inside(root,relatives[0],'data')
    if digest((parent/'user-config.json').read_bytes()) != user_hash:
        raise ValueError('resume configuration changed; start an explicitly new trial instead')
    if (parent/'manifest.json').exists():
        verify(root,relatives[0])
    events = read_ledger(parent/'ledger',verified_outer=(parent/'manifest.json').exists())
    if not events:
        raise ValueError('resume requires a sealed ledger event; counters cannot reset')
    state = events[-1]['state']
    required = ['logical_requests','transport_attempts','pdf_download_attempts','downloaded_bytes',
                'reserved_bytes','text_pages','reserved_text_pages']
    if any(type(state.get(k)) is not int or state[k]<0 for k in required):
        raise ValueError('resume ledger lacks valid cumulative counters')
    if state['logical_requests']!=len(state['requests']) or state['transport_attempts']!=sum(r['attempts'] for r in state['requests'].values()):
        raise ValueError('resume ledger request/attempt counters mismatch')
    return state


@contextmanager
def epoch_lock(root, user):
    """OS lock releases on Ctrl+C/crash; epoch pointers prevent fresh counter resets."""
    folder = Path(root)/'data/financial/trial-epochs'/digest(user['cache_epoch'].encode('utf8'))
    folder.mkdir(parents=True,exist_ok=True)
    lock = (folder/'active.lock').open('a+b')
    lock.seek(0)
    if lock.read(1)==b'':
        lock.write(b'0')
        lock.flush()
    lock.seek(0)
    try:
        if sys.platform=='win32':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise ValueError('another process is running this trial epoch') from None
    try:
        yield folder
    finally:
        lock.seek(0)
        if sys.platform=='win32':
            msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        else:
            fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
        lock.close()


def summaries(cells, config):
    # Group before invoking the legacy summarizer to avoid all-universe scans per period.
    by_symbol = defaultdict(list)
    for r in cells:
        by_symbol[r['symbol']].append(r)
    result = dict(wire_cells=len(cells), in_target_cells=sum(r['in_target'] for r in cells),
        statuses=dict(Counter(r['status'] for r in cells)), coverage=[], conflicts=[], accounting_qa=[], accepted_facts=0)
    for symbol in config['symbols']:
        for period, years in [('year',config['annual_years']),('quarter',config['quarter_years'])]:
            rows = [r for r in by_symbol[symbol] if r['requested_period']==period]
            s = summarize(rows,dict(symbols=[symbol],years=years,periods=[period]))
            for key in ['coverage','conflicts','accounting_qa']:
                result[key].extend(s[key])
    return result


def task_readiness(cells, c, members, conflicts):
    lookup = defaultdict(list)
    for r in cells:
        if r['in_target'] and r['quarter']==0 and r['field'] and r['value'] is not None:
            lookup[(r['symbol'],r['year'],r['field'])].append(r)
    rows, detail = [], []
    types = {m['ticker']:m['proposed_company_type'] for m in members}
    conflicted = {(r['key'][0],r['key'][2],r['key'][4]) for r in conflicts}
    for symbol in c['symbols']:
        for year in c['score_years']:
            for task, requirements in ANNUAL_TASKS.items():
                inputs = []
                for field,offset in requirements:
                    found = lookup[(symbol,year+offset,field)]
                    bad = any((symbol,year+offset,r['report_norm_id']) in conflicted for r in found)
                    presence = bool(found) and not bad
                    inputs.append(dict(field=field,year=year+offset,
                        status='VALUE_CONFLICT' if bad else 'UNVERIFIED_CANDIDATE_PRESENT' if presence else 'MISSING_EXACT_INPUT',
                        evidence=[dict(path=r['source_path'],sha256=r['source_sha256'],header=r['header']) for r in found]))
                blockers = list(EXTERNAL.get(task,[]))+['SEMANTIC_UNIT_SCOPE_REVIEW','PUBLICATION_PIT','REVISIONS',
                    'HISTORICAL_IDENTITY_AND_SECTOR']
                sector_review = types[symbol]!='Regular' and task in ('F_SCORE','M_SCORE','Z_SCORE')
                if sector_review:
                    blockers.append('SECTOR_VARIANT_REVIEW_REQUIRED')
                row = dict(symbol=symbol,year=year,task=task,required_input_cells=len(inputs),
                    candidate_input_cells=sum(i['status']=='UNVERIFIED_CANDIDATE_PRESENT' for i in inputs),
                    missing_inputs=[f"{i['field']}@{i['year']}" for i in inputs if i['status']!='UNVERIFIED_CANDIDATE_PRESENT'],
                    blockers=blockers, task_ready=False, computed_value=None, financial_features_allowed=False,
                    variant_status='SECTOR_VARIANT_REVIEW_REQUIRED' if sector_review else 'STRICT_INPUT_PREPARATION_ONLY')
                rows.append(row)
                detail.append(dict(row,inputs=inputs))
    return rows, detail


def document_sample(symbols, types, explicit, gap_counts, limit):
    """Keep controls and sector diversity instead of letting unmapped banks take every slot."""
    rank = {s:i for i,s in enumerate(symbols)}
    ordered = sorted(symbols,key=lambda s:(-gap_counts[s],rank[s]))
    selected = [s for s in symbols if any(d['symbol']==s for d in explicit)]
    for kind,quota in [('Regular',8),('Bank',2),('Securities',1),('Insurance',1)]:
        needed = max(0,quota-sum(types[s]==kind for s in selected))
        selected.extend([s for s in ordered if types[s]==kind and s not in selected][:needed])
    selected.extend(s for s in ordered if s not in selected)
    return selected[:limit]


def extract_document(root, out, cp, doc, transport, parents, command=subprocess.run):
    """Run PDF parser in a bounded worker; never run unbounded pypdf in supervisor."""
    if doc['acquisition']['status']!='COMPLETE':
        return dict(status=doc['acquisition']['status'],payload={})
    import pypdf
    from ..ingestion import financial_crawl_pdf as pdf_module
    renderer = shutil.which('pdftoppm')
    request = dict(version='financial-batch-evidence-v1',operation='USER_PDF_TEXT_SELECTED_OCR',
        pdf_sha256=doc['acquisition']['payload']['sha256'],ocr_pages=[],cell_templates=[],
        pypdf=pypdf.__version__,max_pdf_pages=cp.c['max_pdf_pages'],
        extractor_sha256=digest(Path(pdf_module.__file__).read_bytes()),
        script_sha256=digest((root/'scripts/ocr_financial_pages.ps1').read_bytes()),
        renderer_sha256=digest(Path(renderer).read_bytes()) if renderer else 'UNAVAILABLE')
    cached = cp.cached_result(request)
    if cached:
        return cached
    remaining = transport.remaining_seconds()
    page_budget = cp.c['max_text_pages']-transport.state['text_pages']-transport.state['reserved_text_pages']
    if remaining<=0 or page_budget<=0:
        return dict(status='DEFERRED_GLOBAL_EXTRACTION_BUDGET',payload={})
    reserved = min(page_budget,cp.c['max_pdf_pages'])
    job = dict(config=dict(cp.c,max_text_pages=reserved,
                           max_seconds=max(1,int(remaining))), document=doc,
               resume_runs=[*parents,out.relative_to(root).as_posix()])
    path = out/'pdf-jobs'/(digest(encoded(job))+'.json')
    immutable_write(path,encoded(job))
    transport.state['reserved_text_pages'] += reserved
    transport.event('PDF_WORKER_START',job=path.relative_to(root).as_posix(),reserved_pages=reserved)
    try:
        p = command([sys.executable,str(root/'scripts/crawl_financial_trial.py'),'pdf-worker',
                     '--output',out.relative_to(root).as_posix(),'--job',path.relative_to(root).as_posix()],
                    capture_output=True,timeout=max(.1,remaining),check=True)
        response = json.loads(p.stdout)
        processed = response['metrics']['text_pages']
        if not response['receipt'].get('reused'):
            processed = max(processed,len(response['receipt']['payload'].get('pages',[])))
        if not 0<=processed<=reserved:
            raise ValueError('PDF worker exceeded reserved page budget')
        transport.state['reserved_text_pages'] -= reserved
        transport.state['text_pages'] += processed
        transport.event('PDF_WORKER_FINISHED',processed_pages=processed)
        cp.metrics['text_pages'] += response['metrics']['text_pages']
        cp.metrics['ocr_pages'] += response['metrics']['ocr_pages']
        cp.metrics['new_checkpoints'] += response['metrics']['new_checkpoints']
        cp.metrics['cache_hits'] += response['metrics']['cache_hits']
        return response['receipt']
    except (subprocess.SubprocessError,ValueError,OSError,KeyError,TypeError) as exc:
        stderr = getattr(exc,'stderr',b'') or b''
        return dict(status='FAILED_OR_TIMED_OUT_PDF_WORKER',payload={},error=str(exc),
                    diagnostic=stderr.decode('utf8',errors='replace')[-2000:])


def run(root, config_path, output, resume_runs=(), network=False, **kwargs):
    root = Path(root).resolve()
    user = json.loads(inside(root,config_path,'configs').read_bytes())
    prepare(root,user)
    with epoch_lock(root,user) as folder:
        entries = sorted(folder.glob('[0-9]*'))
        if entries:
            verify_inventory(entries[-1])
            pointer = json.loads((entries[-1]/'run.json').read_bytes())
            if list(resume_runs)!=[pointer['path']]:
                raise ValueError('epoch already started; use --resume-from '+pointer['path']+' to preserve global counters')
        return _run(root,config_path,output,resume_runs,network,epoch_folder=folder,**kwargs)


def _run(root, config_path, output, resume_runs=(), network=False, *, transport_factory=TrialTransport,
        epoch_folder=None,
        pdf_command=subprocess.run):
    root = Path(root).resolve()
    user_path = inside(root,config_path,'configs')
    user = json.loads(user_path.read_bytes())
    plan,c = prepare(root,user)
    environment = doctor(root,user)
    if environment['status']!='READY':
        raise ValueError('preflight failed: '+'; '.join(environment['missing']))
    out = inside(root,output,'data')
    state = load_resume(root,resume_runs,digest(user_path.read_bytes()))
    cp = Checkpoints(root,out,c,resume_runs)
    out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'config.json',encoded(c))
    immutable_write(out/'user-config.json',user_path.read_bytes())
    immutable_write(out/'plan.json',inside(root,user['plan_path'],'configs').read_bytes())
    immutable_write(out/'environment.json',encoded(environment))
    dependencies = []
    for r in resume_runs:
        parent = inside(root,r,'data')
        events = read_ledger(parent/'ledger',verified_outer=(parent/'manifest.json').exists())
        dependencies.append(dict(path=r,manifest_sha256=digest((parent/'manifest.json').read_bytes())
            if (parent/'manifest.json').exists() else None,ledger_event_count=len(events),
            ledger_last_sha256=digest((parent/'ledger'/f'{len(events):06d}'/'event.json').read_bytes())))
    immutable_write(out/'resume-dependencies.json',encoded(dependencies))
    for source in sorted((root/'src/delta_t1').rglob('*.py')):
        if source.parent.name in ('ingestion','experiments') or source.name=='base.py':
            immutable_write(out/'code'/source.relative_to(root),source.read_bytes())
    for name in ['scripts/crawl_financial_trial.py','scripts/crawl_financial_trial.ps1']:
        if (root/name).exists():
            immutable_write(out/'code'/name,(root/name).read_bytes())
    transport = transport_factory(root,out,c,state)
    if epoch_folder:
        entry = epoch_folder/f'{len(list(epoch_folder.glob("[0-9]*")))+1:06d}'
        immutable_write(entry/'run.json',encoded(dict(path=out.relative_to(root).as_posix(),
            config_sha256=digest(user_path.read_bytes()))))
        seal(entry)
    cp.boundary |= transport.state['boundary']
    cells,structured,listings,documents,errors,waves = [],[],[],[],[],[]
    receipts = []
    types = {m['ticker']:m['proposed_company_type'] for m in plan['members']}
    def log(stage,**data):
        record = dict(at=now(),stage=stage,**data)
        with (out/'work-log.jsonl').open('a',encoding='utf8') as f:
            f.write(json.dumps(record,ensure_ascii=False)+'\n')
        print(json.dumps(record,ensure_ascii=False),flush=True)
    def acquire(item):
        transport.context = item
        # Cached receipts remain readable after a stop, but no new network is possible.
        if (transport.state['budget_stop'] or transport.remaining_seconds()<=0) and network:
            request = dict(version='financial-batch-evidence-v1',operation='ACQUIRE',cache_epoch=c['cache_epoch'],**item)
            old = cp.cached_result(request)
            if old:
                receipts.append(old)
                return old
            if not transport.state['budget_stop']:
                transport.state.update(budget_stop=True,stop_reason='WALL_TIME_CAP')
                transport.event('BUDGET_STOP',reason='WALL_TIME_CAP')
            r = cp.commit(request,'DEFERRED_GLOBAL_BUDGET',{},error=transport.state['stop_reason'])
            receipts.append(r)
            return r
        r = cp.acquire(item,transport,network)
        if r['status']=='DEFERRED_BUDGET' and network:
            transport.state.update(budget_stop=True,stop_reason='CHECKPOINT_BUDGET_CAP')
            transport.event('BUDGET_STOP',reason='CHECKPOINT_BUDGET_CAP')
        receipts.append(r)
        return r
    def collect_structured(symbol,period,page,phase,wave):
        for report in REPORTS:
            request = structured_request(symbol,report,period,page)
            r = acquire(request)
            parsed = dict(request,acquisition=r,status=r['status'],phase=phase,wave=wave)
            if r['status']=='COMPLETE':
                try:
                    body = inside(root,r['payload']['path'],'data').read_bytes()
                    if digest(body)!=r['payload']['sha256']:
                        raise ValueError('raw checkpoint hash mismatch')
                    raw_path = 'raw/'+r['payload']['sha256']+'.json'
                    if not (out/raw_path).exists():
                        immutable_write(out/raw_path,body)
                    def reject(token):
                        raise ValueError('nonfinite JSON '+token)
                    def finite_float(token):
                        value = float(token)
                        if not math.isfinite(value):
                            reject(token)
                        return value
                    rows = candidates(json.loads(body,parse_constant=reject,parse_float=finite_float),dict(request,path=raw_path,
                        sha256=r['payload']['sha256']),c['annual_years'] if period=='year' else c['quarter_years'],types[symbol])
                    for row in rows:
                        business_type = row['header'].get('BusinessType')
                        evidence = type(business_type) is int and business_type==1 and types[symbol]=='Regular'
                        row['classification_status'] = 'CURRENT_PROVIDER_REGULAR_HEADER_ONLY' if evidence else 'SECTOR_SOURCE_REVIEW_REQUIRED'
                        if not evidence and row['status']!='INVALID_NUMERIC_VALUE':
                            row.update(field=None,value=None,unit='UNVERIFIED',status='SECTOR_SOURCE_REVIEW_REQUIRED')
                    cells.extend(rows)
                    parsed.update(status='PARSED_CANDIDATES' if rows else 'EMPTY_RESPONSE',wire_cells=len(rows))
                except (ValueError,TypeError,KeyError) as exc:
                    parsed.update(status='INVALID_PROVIDER_PAYLOAD',error=str(exc))
            structured.append(parsed)
            log('STRUCTURED',symbol=symbol,period=period,page=page,report=report,status=parsed['status'],
                progress=len(structured),base_expected=len(c['symbols'])*6)
            if parsed['status']!='PARSED_CANDIDATES':
                errors.append(dict(stage='STRUCTURED',symbol=symbol,report=report,period=period,page=page,reason=parsed['status']))
            if cp.boundary or transport.state['budget_stop']:
                break
    log('START',symbols=len(c['symbols']),network=network)
    quality_stop = False
    for phase,period in [('P1','year'),('P2','quarter')]:
        for wave in plan['waves']:
            start = len(structured)
            for symbol in wave['symbols']:
                collect_structured(symbol,period,1,phase,wave['id'])
                if cp.boundary or transport.state['budget_stop']:
                    break
            valid = sum(r['status']=='PARSED_CANDIDATES' for r in structured[start:])
            expected = len(wave['symbols'])*3
            passed = valid*10>=expected*9
            waves.append(dict(phase=phase,id=wave['id'],valid=valid,expected=expected,passed=passed))
            log('WAVE',**waves[-1])
            if not passed or cp.boundary or transport.state['budget_stop']:
                quality_stop = not passed
                break
        if quality_stop or cp.boundary or transport.state['budget_stop']:
            break
    summary = summaries(cells,c)
    # Deterministic priority: missing annual years, then quarter gaps; whole report triplets.
    history_jobs = []
    for m in plan['members']:
        for period in ['year','quarter']:
            coverage = [r for r in summary['coverage'] if r['symbol']==m['ticker'] and
                        (r['quarter']==0 if period=='year' else r['quarter']>0)]
            if any(not r['wire_cells'] for r in coverage):
                for page in [2,3]:
                    history_jobs.append((m['ticker'],period,page))
    if not (quality_stop or cp.boundary or transport.state['budget_stop']):
        for symbol,period,page in history_jobs[:c['history_requests']//3]:
            collect_structured(symbol,period,page,'P3_HISTORY',0)
            if cp.boundary or transport.state['budget_stop']:
                break
    summary = summaries(cells,c)
    if c['documents_enabled'] and not (quality_stop or cp.boundary or transport.state['budget_stop']):
        # Pilot controls first, then most annual field gaps; deterministic tie by plan order.
        gap_counts = Counter()
        for row in summary['coverage']:
            if row['quarter']==0:
                gap_counts[row['symbol']] += len(row['missing_core_fields'])
        selected = document_sample(c['symbols'],types,c['explicit_documents'],gap_counts,c['document_symbols'])
        document_calls, seen = 0,set()
        for symbol in selected:
            choices = [d for d in c['explicit_documents'] if d['symbol']==symbol]
            if document_calls>=c['document_requests']:
                break
            if not choices:
                year = max(c['annual_years'])
                r = acquire(dict(symbol=symbol,year=year,kind='list',url=f'https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={symbol.lower()}&Type=1&Year={year}'))
                listings.append(r)
                document_calls += 1
                if r['status']=='COMPLETE':
                    try:
                        rows = consolidated_rows(inside(root,r['payload']['path'],'data').read_bytes(),year)
                        choices = [dict(symbol=symbol,year=year,quarter=0,url=x['Link'],provider_report_id=x['id'],
                                        provider_name=x['Name'],listing_sha256=r['payload']['sha256']) for x in rows if x['Quarter']==5]
                    except (ValueError,KeyError,TypeError) as exc:
                        errors.append(dict(stage='PDF_DISCOVERY',symbol=symbol,reason='INVALID_LISTING',error=str(exc)))
                else:
                    errors.append(dict(stage='PDF_DISCOVERY',symbol=symbol,reason=r['status']))
            if not choices:
                errors.append(dict(stage='PDF_DISCOVERY',symbol=symbol,reason='NO_ANNUAL_CONSOLIDATED_CANDIDATE'))
            for d in choices:
                if d['url'] in seen:
                    continue
                if document_calls>=c['document_requests'] or len(documents)>=20:
                    errors.append(dict(stage='PDF',symbol=symbol,reason='DOCUMENT_SCOPE_CAP'))
                    break
                seen.add(d['url'])
                try:
                    validate_url(d['url'],c['approved_hosts'])
                    r = acquire(dict(d,kind='pdf'))
                    document_calls += 1
                    if r['status']=='COMPLETE' and d.get('pdf_sha256') and r['payload']['sha256']!=d['pdf_sha256']:
                        raise ValueError('explicit PDF checksum mismatch')
                    doc = dict(d,acquisition=r,publication_date=None,usable_from_date=None)
                    doc['extraction'] = extract_document(root,out,cp,doc,transport,resume_runs,pdf_command)
                    documents.append(doc)
                    log('PDF',symbol=symbol,acquisition=r['status'],extraction=doc['extraction']['status'])
                    if r['status']!='COMPLETE' or doc['extraction']['status']!='COMPLETE':
                        errors.append(dict(stage='PDF',symbol=symbol,reason=doc['extraction']['status']))
                except ValueError as exc:
                    errors.append(dict(stage='PDF',symbol=symbol,reason='DOCUMENT_REVIEW_REQUIRED',error=str(exc)))
                if cp.boundary or transport.state['budget_stop']:
                    break
            if cp.boundary or transport.state['budget_stop']:
                break
    readiness, detail = task_readiness(cells,c,plan['members'],summary['conflicts'])
    queue = [dict(stage='CORE_MAPPING',**r) for r in summary['coverage'] if r['missing_core_fields']]
    queue += [dict(stage='RECONCILIATION',**r) for r in summary['conflicts']]
    queue += [dict(stage='ACCOUNTING',**r) for r in summary['accounting_qa'] if r['status']!='CANDIDATE_ARITHMETIC_PASS']
    queue += errors
    for m in plan['members']:
        queue.append(dict(stage='CLASSIFICATION_AND_RELEASE',symbol=m['ticker'],required=['CURRENT_AND_HISTORICAL_SECTOR',
            'VALUE_UNIT_SCOPE_FRAMEWORK','EXACT_VINTAGE_PUBLICATION','REVISIONS','SECURITY_ID_HISTORY'],financial_features_allowed=False))
        matches = [d for d in documents if d['symbol']==m['ticker']]
        if not matches:
            queue.append(dict(stage='PDF_EVIDENCE',symbol=m['ticker'],reason='NO_DOCUMENT_EVIDENCE_IN_TRIAL'))
        for d in matches:
            queue.append(dict(stage='PDF_SEMANTICS_PUBLICATION_SCAN_REVIEW',symbol=m['ticker'],url=d['url'],
                acquisition_status=d['acquisition']['status'],extraction_status=d['extraction']['status'],
                low_text_pages=d['extraction']['payload'].get('low_text_pages',[]),
                reason='EXACT_DOCUMENT_IDENTITY_UNIT_NOTES_PUBLICATION_REVISIONS_REQUIRE_REVIEW'))
    ambiguous = {(r['symbol'],r['source_sha256'],r['column']):r for r in cells if r['header_status']=='AMBIGUOUS_DUPLICATED_PERIOD_COLUMNS'}
    queue += [dict(stage='PROVIDER_HEADER_REVIEW',symbol=r['symbol'],report=r['report'],header=r['header'],
                   source_sha256=r['source_sha256'],column=r['column']) for r in ambiguous.values()]
    period_rows = []
    indexed = defaultdict(list)
    for row in cells:
        if row['in_target']:
            indexed[(row['symbol'],row['report'],row['year'],row['quarter'])].append(row)
    for r in summary['coverage']:
        selected = indexed[(r['symbol'],r['report'],r['year'],r['quarter'])]
        period_rows.append(dict(symbol=r['symbol'],report=r['report'],year=r['year'],quarter=r['quarter'],
            unambiguous_wire_cells=len(selected),non_null_wire_cells=sum(x['raw_value'] is not None and x['status']!='INVALID_NUMERIC_VALUE' for x in selected),
            mapped_candidate_fields=len(r['fields_with_candidates']),classification_verified=False))
    base_success = {p:sum(r['status']=='PARSED_CANDIDATES' for r in structured if r['phase']==phase)
                    for p,phase in [('annual','P1'),('quarter','P2')]}
    def covered(year,quarter):
        return sum(all(any(r['symbol']==s and r['year']==year and r['quarter']==quarter and r['report']==report
                       and r['non_null_wire_cells']>0 for r in period_rows) for report in REPORTS) for s in c['symbols'])
    annual_covered,quarter_covered = covered(max(c['annual_years']),0),covered(max(c['quarter_years']),4)
    base_expected = len(c['symbols'])*3
    targets_pass = all(v*100>=base_expected*95 for v in base_success.values()) and min(annual_covered,quarter_covered)*10>=len(c['symbols'])*9
    status = 'HARD_STOP' if cp.boundary or transport.state['boundary'] else 'BUDGET_STOP' if transport.state['budget_stop'] else 'QUALITY_STOP' if quality_stop else 'PARTIAL' if errors else 'COMPLETE'
    actual_attempted = len({r['symbol'] for r in structured})
    transport.event('FINISH',engineering_status=status)
    immutable_write(out/'request-ledger.jsonl',''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in transport.journal).encode('utf8'))
    result = dict(version=VERSION,engineering_status=status,transport_mode=getattr(transport,'mode','PUBLIC_HTTPS' if network else 'OFFLINE_CACHE_ONLY'),symbols=c['symbols'],attempted_symbols=actual_attempted,
        planned_symbols=len(c['symbols']),metrics=cp.metrics,trial_totals=transport.state,
        base_success=base_success,base_expected_per_period=base_expected,waves=waves,
        annual_latest_wire_covered_symbols=annual_covered,quarter_q4_wire_covered_symbols=quarter_covered,
        engineering_targets_pass=targets_pass,accepted_facts=0,financial_cluster_eligible_rows=0,
        numeric_accuracy='NOT_MEASURED_NO_NEW_GROUND_TRUTH',review_minutes=None,
        summary=summary,structured=structured,listings=receipts,
        documents=documents,exceptions=errors,reference_runs=[],review_queue_items=len(queue),
        next_100_allowed=False,**CLOSED)
    immutable_write(out/'candidates.jsonl',''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n' for r in cells).encode('utf8'))
    immutable_write(out/'candidates.csv',csv_bytes(cells,['symbol','report','year','quarter','field','raw_value','value','unit','status','classification_status','header','source_path','source_sha256']))
    immutable_write(out/'coverage.csv',csv_bytes(summary['coverage'],['symbol','report','year','quarter','wire_cells','fields_with_candidates','missing_core_fields','status','verified']))
    immutable_write(out/'period-coverage.csv',csv_bytes(period_rows,['symbol','report','year','quarter','unambiguous_wire_cells','non_null_wire_cells','mapped_candidate_fields','classification_verified']))
    immutable_write(out/'feature-readiness.csv',csv_bytes(readiness,['symbol','year','task','required_input_cells','candidate_input_cells','missing_inputs','blockers','variant_status','task_ready','computed_value']))
    immutable_write(out/'feature-readiness.json',encoded(detail))
    immutable_write(out/'review-queue.json',encoded(queue))
    immutable_write(out/'results.json',encoded(result))
    actions = [dict(priority=1,action='FIX_ACCESS_BOUNDARY',reason=transport.state['stop_reason'])] if cp.boundary else []
    if quality_stop:
        actions.append(dict(priority=1,action='DIAGNOSE_SOURCE_BEFORE_NEXT_WAVE',reason='wave valid responses below 90%'))
    if transport.state['budget_stop']:
        actions.append(dict(priority=1,action='REVIEW_BUDGET_AND_PENDING_WORK',reason=transport.state['stop_reason']))
    actions += [dict(priority=2,action='REVIEW_PROVIDER_HEADERS_AND_PERIOD_GAPS',ambiguous_columns=len(ambiguous)),
        dict(priority=3,action='VALIDATE_SECTOR_TEMPLATE_AND_NUMERIC_GROUND_TRUTH'),
        dict(priority=4,action='REVIEW_NOTES_PUBLICATIONS_REVISIONS_AND_VALUATION_BASIS'),
        dict(priority=5,action='REVIEW_100_SYMBOL_TRIAL',automatic_permission=False,engineering_targets_pass=targets_pass)]
    immutable_write(out/'next-actions.json',encoded(actions))
    report = f'''# Financial trial — báo cáo sau chạy

Collection: **{status}**. Mã đã thử: **{actual_attempted}/{len(c['symbols'])}**.
Annual page1 hợp lệ: **{base_success['annual']}/{base_expected}**;
quarter page1 hợp lệ: **{base_success['quarter']}/{base_expected}**.
FY{max(c['annual_years'])} có ba báo cáo với wire headers rõ: {annual_covered} mã;
Q4/{max(c['quarter_years'])}: {quarter_covered} mã. Đây là wire coverage, không numeric acceptance.
Engineering targets: {'PASS' if targets_pass else 'NOT_MET'}.
Accepted facts: **0**; financial cluster eligible: **0**; tự mở 100 mã: **false**.

Toàn lineage: {transport.state['logical_requests']} logical requests,
{transport.state['transport_attempts']} attempts, {transport.state['downloaded_bytes']} bytes đã đọc;
{transport.state['reserved_bytes']} bytes dự phòng chưa xác nhận do interruption.
Run này: {cp.metrics['cache_hits']} cache hits, {cp.metrics['text_pages']} text pages mới.
PDF records: {len(documents)}; OCR v1: queue trang scan, không tự đọc/nhận số.
Numeric accuracy chưa đo; review_minutes chưa đo, không gán bằng zero.

Đọc `period-coverage.csv` cho wire periods, `coverage.csv` cho mapped field gaps,
`feature-readiness.csv` cho đầu vào F/M/Z/EPS/P-E/P-B theo mã/năm. Trạng thái candidate
không chứng minh đúng semantics, đơn vị, PIT hoặc revision. Score giữ null khi chưa
nghiệm thu. Ba năm trên header chưa chứng minh ba năm usable cho cluster.

## Công việc tiếp theo

Xem `next-actions.json` và `review-queue.json`. Xử lý stop/lỗi nguồn và ambiguous
headers trước; xác minh sector/templates và đối chiếu ground truth; bổ sung exact
PDF notes/publications/revisions/shares/events/price basis theo dependency còn thiếu.
Tăng 100 mã cần đánh giá engineering targets, numeric QA và review cost riêng.

Gửi lại `feedback.zip` do lệnh feedback tạo ngoài run sealed. Gói chứa report, metrics,
coverage, readiness và queue; không chứa raw response/PDF. Có thể gửi thêm candidates
hoặc exact raw riêng nếu cần debug. Run này và toàn bộ raw/checkpoints giữ local.
'''
    immutable_write(out/'report.md',report.encode('utf8'))
    immutable_write(out/'self-review.json',encoded(dict(status='PASS_ENGINEERING_INVARIANTS',
        real_data_acceptance='NOT_GRANTED',source_accuracy='NOT_MEASURED',**CLOSED)))
    log('FINISH',engineering_status=status,attempted_symbols=actual_attempted,cache_hits=cp.metrics['cache_hits'])
    seal(out)
    verify(root,out.relative_to(root).as_posix())
    return result


def verify(root, relative):
    root = Path(root).resolve()
    result = verify_flow(root,relative)
    out = inside(root,relative,'data')
    flow = json.loads((out/'results.json').read_bytes())
    if flow['version']!=VERSION or any(flow[k] is not False for k in CLOSED):
        raise ValueError('trial release gates changed')
    checked = set()
    for line in (out/'candidates.jsonl').read_text(encoding='utf8').splitlines():
        r = json.loads(line)
        key = (r['source_path'],r['source_sha256'])
        if key in checked:
            continue
        p = (out/r['source_path']).resolve()
        if not p.is_relative_to(out/'raw') or digest(p.read_bytes())!=r['source_sha256']:
            raise ValueError('trial portable candidate raw mismatch')
        checked.add(key)
    events = read_ledger(out/'ledger',verified_outer=True)
    if not events or events[-1]['state']!=flow['trial_totals']:
        raise ValueError('trial ledger totals mismatch')
    # Transitive manifests pin budget lineage as well as successful task receipts.
    visited = set()
    def dependencies(folder):
        for d in json.loads((folder/'resume-dependencies.json').read_bytes()):
            parent = inside(root,d['path'],'data')
            if parent in visited:
                continue
            visited.add(parent)
            if d['manifest_sha256']:
                if digest((parent/'manifest.json').read_bytes())!=d['manifest_sha256']:
                    raise ValueError('trial resume manifest changed')
                verify_inventory(parent)
            parent_events = read_ledger(parent/'ledger',verified_outer=bool(d['manifest_sha256']))
            if not parent_events:
                raise ValueError('trial parent ledger missing')
            if (len(parent_events)!=d['ledger_event_count'] or
                    digest((parent/'ledger'/f'{len(parent_events):06d}'/'event.json').read_bytes())!=d['ledger_last_sha256']):
                raise ValueError('trial parent ledger anchor changed')
            dependencies(parent)
    dependencies(out)
    return dict(result,verified_raw_files=len(checked),ledger_events=len(events),trial_totals_verified=True)


def feedback(root,relative,output):
    verify(root,relative)
    root = Path(root).resolve()
    out = inside(root,relative,'data')
    target = inside(root,output,'artifacts')
    if target.exists():
        raise ValueError('feedback output already exists; choose a new filename')
    target.parent.mkdir(parents=True,exist_ok=True)
    names = ['report.md','results.json','coverage.csv','period-coverage.csv','feature-readiness.csv',
             'review-queue.json','next-actions.json','self-review.json','work-log.jsonl','request-ledger.jsonl','user-config.json','plan.json']
    pins = {name:digest((out/name).read_bytes()) for name in names}
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(out/name,name)
        z.writestr('feedback-manifest.json',encoded(dict(source_run=relative,
            source_manifest_sha256=digest((out/'manifest.json').read_bytes()),files=pins)))
    return dict(status='FEEDBACK_READY',path=str(target),sha256=digest(target.read_bytes()),includes_raw=False)
