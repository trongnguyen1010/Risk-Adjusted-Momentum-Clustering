"""CafeF-first bounded candidate trial. No KBS fallback or financial acceptance."""
import csv
import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

from ..ingestion.cafef_financial import digest,encoded,immutable_write,now
from ..ingestion.cafef_financial_detail import detail_url,parse_detail
from ..ingestion.financial_batch_evidence import GATES,inside,seal
from ..ingestion.financial_compact_trial import CompactTrialTransport,read_compact
from ..ingestion.financial_crawl_candidates import csv_bytes
from ..ingestion.financial_data_report import FIELDS
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_requirements import EXTRA,NOTES
from ..ingestion.financial_task_readiness import ANNUAL_TASKS,EXTERNAL
from ..ingestion.financial_trial_transport import TrialBudgetError
from ..ingestion.sources.base import AccessControlError,RateLimitError
from .financial_crawl_trial import epoch_lock
from .financial_source_benchmark import qa

VERSION='cafef-financial-trial-v1'
CLOSED=dict(**GATES,financial_cluster_allowed=False,unattended_numeric_acceptance_allowed=False)
REPORTS={'CDKT':'bsheet','KQKD':'incsta','LCTT':'cashflow'}
LIMITS=dict(max_logical_requests=720,max_transport_attempts=900,max_attempts_per_request=2,
    max_response_bytes=3_000_000,max_total_downloaded_bytes=300_000_000,
    timeout_seconds=20,max_wall_seconds=7200,max_pdf_download_attempts=0)
SOURCES=['src/delta_t1/experiments/cafef_financial_trial.py',
    'src/delta_t1/ingestion/financial_compact_trial.py','src/delta_t1/ingestion/financial_trial_transport.py',
    'src/delta_t1/ingestion/cafef_financial_detail.py','src/delta_t1/ingestion/financial_data_report.py',
    'src/delta_t1/ingestion/financial_requirements.py','src/delta_t1/ingestion/financial_task_readiness.py',
    'src/delta_t1/ingestion/financial_pilot_readiness.py','src/delta_t1/experiments/financial_source_benchmark.py',
    'src/delta_t1/ingestion/financial_batch_evidence.py','src/delta_t1/ingestion/financial_documents.py',
    'src/delta_t1/ingestion/cafef_financial.py','src/delta_t1/ingestion/sources/base.py',
    'src/delta_t1/experiments/financial_crawl_trial.py','src/delta_t1/ingestion/financial_source_compare.py',
    'src/delta_t1/ingestion/financial_crawl_candidates.py','src/delta_t1/ingestion/financial_provider_normalize.py']


def source_pins(root):return {name:digest((root/name).read_bytes()) for name in SOURCES}


def prepare(root,c,check_pilot=True):
    root=Path(root).resolve()
    if c.get('version')!=VERSION or any(c.get(k) is not False for k in CLOSED):raise ValueError('closed candidate trial required')
    if c.get('source')!='CAFEF_DETAIL' or c.get('approved_hosts')!=['cafef.vn']:raise ValueError('CafeF-only source required')
    if not isinstance(c.get('cache_epoch'),str) or not re.fullmatch('[a-zA-Z0-9_-]{1,100}',c['cache_epoch']):raise ValueError('explicit epoch required')
    plan_path=inside(root,c['plan_path'],'configs');body=plan_path.read_bytes()
    if digest(body)!=c['plan_sha256']:raise ValueError('plan pin changed')
    plan=json.loads(body)
    if plan['version']!='financial-crawl-50-plan-v1' or plan['executable'] is not False:raise ValueError('frozen plan required')
    if plan.get('branch') and (root/'.git').exists():
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True,timeout=5).strip()
        if branch!=plan['branch']:raise ValueError('wrong CafeF branch')
    symbols=c['symbols'];all_members={m['ticker']:m for m in plan['members']}
    if not isinstance(symbols,list) or not 1<=len(symbols)<=50 or len(set(symbols))!=len(symbols):raise ValueError('invalid bounded membership')
    if len(symbols)>4 and symbols!=[m['ticker'] for m in plan['members']]:raise ValueError('trial50 must use exact frozen ordered membership')
    market=inside(root,plan['universe_source']['path'],'artifacts')
    if digest(market.read_bytes())!=plan['universe_source']['sha256']:raise ValueError('market snapshot changed')
    rows=list(csv.DictReader(market.read_text(encoding='utf-8-sig').splitlines()))
    if len(symbols)<=4:
        # The reviewed pilot cohort predates the frozen market-ready trial50.
        # VNM/PVS are validation references, not newly eligible market members.
        benchmark=inside(root,c['reference_benchmark'],'data');verify_inventory(benchmark)
        reference_config=json.loads((benchmark/'config.json').read_bytes())
        if set(reference_config['history_symbols'])!={'FPT','VNM','PVS','ACV'} or not set(symbols)<=set(reference_config['history_symbols']):raise ValueError('invalid reviewed pilot membership')
        members=[dict(ticker=s,proposed_company_type=reference_config['symbols'][s],membership_basis='PINNED_REVIEWED_PILOT_ONLY') for s in symbols]
        market_members=[all_members[s] for s in symbols if s in all_members]
    else:
        if not set(symbols)<=set(all_members):raise ValueError('invalid bounded membership')
        members=[all_members[s] for s in symbols];market_members=members
    for m in market_members:
        found=[r for r in rows if r['ticker']==m['ticker'] and r['security_id']==m['security_id']]
        if len(found)!=1 or found[0]['market_feature_ready_v2']!='True' or m['proposed_company_type'] not in ('Regular','Bank','Securities','Insurance'):raise ValueError('invalid market member/type')
    if c['annual_years']!=list(range(2021,2026)) or c['quarter_years']!=[2024,2025] or c['score_years']!=[2023,2024,2025]:raise ValueError('frozen target years required')
    b=c['budgets']
    if set(b)!=set(LIMITS)|{'min_seconds_between_transport_attempts'}:raise ValueError('invalid budget keys')
    for key,cap in LIMITS.items():
        if type(b[key]) is not int or not (0 if cap==0 else 1)<=b[key]<=cap:raise ValueError('invalid budget '+key)
    if type(b['min_seconds_between_transport_attempts']) not in (int,float) or not 2<=b['min_seconds_between_transport_attempts']<=60:raise ValueError('invalid spacing')
    if type(c['gap_request_limit']) is not int or not 0<=c['gap_request_limit']<=120:raise ValueError('invalid gap budget')
    if len(symbols)>4 and c.get('seed_run'):raise ValueError('live50 may not import benchmark traffic as fresh acquisition')
    if len(symbols)>4 and check_pilot:
        gate=c.get('pilot_gate')
        if not gate:raise ValueError('verified pilot gate required before trial50')
        folder=inside(root,gate['run'],'data');verify(root,gate['run'])
        if digest((folder/'manifest.json').read_bytes())!=gate['manifest_sha256']:raise ValueError('pilot gate pin changed')
        result=json.loads((folder/'results.json').read_bytes())
        if not result['pilot_preflight_pass'] or result['source_pins']!=source_pins(root):raise ValueError('pilot gate/code mismatch')
    return plan,members


def jobs(c):
    return [dict(symbol=s,report=r,statement=statement,year=y,quarter=q,period='year' if q==0 else 'quarter',phase='BASE',kind='structured',url=detail_url(s,statement,y,q))
        for s in c['symbols'] for r,statement in REPORTS.items() for y,q in [(2025,0),(2021,0),(2025,4),(2024,4)]]


def parse(body,job,kind):
    data=parse_detail(body,job['symbol'],job['statement'],job['year'],job['quarter']);output=[]
    for cell in data['facts']:
        field=next((f for f,(st,code,token) in {**FIELDS,**EXTRA}.items()
            if st==job['statement'] and code==cell['provider_item_code'] and token in cell['item_name'].casefold()),None)
        regular=kind=='Regular'
        output.append(dict(provider='CAFEF',symbol=cell['symbol'],report=job['report'],statement=job['statement'],
            year=cell['year'],quarter=cell['quarter'],code=cell['provider_item_code'],label=cell['item_name'],
            row_ordinal=cell['row_ordinal'],raw_value_text=cell['raw_value_text'],raw_value=cell['display_number_candidate'],
            field=field if regular else None,comparison_value=str(cell['display_number_candidate']) if regular and field and cell['display_number_candidate'] is not None else None,
            unit_basis='RAW_DISPLAY_QA_HYPOTHESIS_UNVERIFIED',unit_scale=None,
            period_semantics=cell['period_semantics'],fiscal_period_status='UNVERIFIED_CALENDAR_OR_FISCAL_YEAR',
            classification_status='PROPOSED_REGULAR_TEMPLATE' if regular else 'SECTOR_TEMPLATE_REVIEW_REQUIRED',
            header=dict(display_unit_labels=data['display_unit_labels'],requested_anchor=[job['year'],job['quarter']]),
            source_path=job['path'],source_sha256=job['sha256'],unambiguous=True,
            numeric_status='CANDIDATE_ONLY',published_at=None,available_at=None,**CLOSED))
    return output


def exports(cells,c,members):
    period=defaultdict(list);field=defaultdict(list)
    for row in cells:
        if (row['quarter']==0 and row['year'] in c['annual_years']) or (row['quarter']>0 and row['year'] in c['quarter_years']):
            period[row['symbol'],row['report'],row['year'],row['quarter']].append(row)
            if row['field'] and row['raw_value'] is not None:field[row['symbol'],row['year'],row['quarter'],row['field']].append(row)
    coverage=[];requirements=[];conflicts=[]
    for s in c['symbols']:
        for y,q in [(y,0) for y in c['annual_years']]+[(y,q) for y in c['quarter_years'] for q in range(1,5)]:
            for r in REPORTS:
                rows=period[s,r,y,q]
                coverage.append(dict(symbol=s,report=r,year=y,quarter=q,wire_cells=len(rows),
                    non_null_wire_cells=sum(row['raw_value'] is not None for row in rows),
                    mapped_candidate_fields=sorted({row['field'] for row in rows if row['field'] and row['raw_value'] is not None}),
                    wire_present=any(row['raw_value'] is not None for row in rows),verified=False))
        for y in c['annual_years']:
            for f in list({**FIELDS,**EXTRA})+NOTES:
                rows=field[s,y,0,f];values=sorted({r['comparison_value'] for r in rows})
                status='MISSING_EXACT_INPUT' if not values else 'VALUE_CONFLICT' if len(values)>1 else 'UNVERIFIED_CANDIDATE_PRESENT'
                if f in NOTES:status='DOCUMENT_NOTE_REVIEW_REQUIRED'
                item=dict(symbol=s,year=y,field=f,status=status,candidate_values=values,
                    evidence=[dict(path=r['source_path'],sha256=r['source_sha256'],code=r['code'],header=r['header']) for r in rows],verified=False)
                requirements.append(item)
                if len(values)>1:conflicts.append(item)
    lookup={(r['symbol'],r['year'],r['field']):r for r in requirements}
    types={m['ticker']:m['proposed_company_type'] for m in members};tasks=[]
    for s in c['symbols']:
        for y in c['score_years']:
            for task,inputs in ANNUAL_TASKS.items():
                selected=[lookup.get((s,y+offset,f),dict(field=f,year=y+offset,status='MISSING_EXACT_INPUT',evidence=[])) for f,offset in inputs]
                blockers=list(EXTERNAL.get(task,[]))+['UNIT_SCOPE_DEFINITION','PUBLICATION_PIT','COMPATIBLE_REVISIONS','HISTORICAL_IDENTITY_SECTOR']
                if types[s]!='Regular' and task in ('F_SCORE','M_SCORE','Z_SCORE'):blockers.append('SECTOR_VARIANT_REVIEW_REQUIRED')
                tasks.append(dict(symbol=s,year=y,task=task,required_input_cells=len(selected),
                    candidate_input_cells=sum(i['status']=='UNVERIFIED_CANDIDATE_PRESENT' for i in selected),
                    missing_inputs=[f"{i['field']}@{i['year']}" for i in selected if i['status']!='UNVERIFIED_CANDIDATE_PRESENT'],
                    blockers=blockers,task_ready=False,computed_value=None,inputs=selected,**CLOSED))
    return coverage,requirements,tasks,conflicts


def load_references(root,c):
    benchmark=inside(root,c['reference_benchmark'],'data');verify_inventory(benchmark)
    data=json.loads((benchmark/'reference-inputs.json').read_bytes())
    for path,pin in data['source_pins'].items():
        if digest(inside(root,path,'data').read_bytes())!=pin:raise ValueError('reviewed reference pin changed')
    return dict(benchmark=c['reference_benchmark'],manifest_sha256=digest((benchmark/'manifest.json').read_bytes()),
        source_pins=data['source_pins'],references=[r for r in data['references'] if r['symbol'] in c['symbols']])


def verify(root,relative,visited=None):
    root=Path(root).resolve();folder=inside(root,relative,'data');visited=visited or set()
    if folder in visited:return {'status':'ALREADY_CHECKED'}
    visited.add(folder);verify_inventory(folder)
    result=json.loads((folder/'results.json').read_bytes())
    if result['version']!=VERSION or any(result[k] is not False for k in CLOSED):raise ValueError('release gates changed')
    ledger=read_compact(folder)
    if ledger['torn_tail_bytes'] or ledger['state']!=result['trial_totals']:raise ValueError('sealed trial ledger mismatch')
    checked=set()
    for record in ledger['state']['cache'].values():
        path=inside(root,record['path'],'data');key=(str(path),record['sha256'])
        if key not in checked:
            if digest(path.read_bytes())!=record['sha256']:raise ValueError('cached raw pin mismatch')
            checked.add(key)
    for dep in json.loads((folder/'dependencies.json').read_bytes()):
        path=inside(root,dep['run'],'data')
        if dep.get('manifest_sha256'):
            if digest((path/'manifest.json').read_bytes())!=dep['manifest_sha256']:raise ValueError('dependency manifest changed')
            if dep['kind']=='RESUME':verify(root,dep['run'],visited)
            else:verify_inventory(path)
        if dep['kind']=='RESUME':
            parent=read_compact(path)
            if parent['prefix_sha256']!=dep['journal_prefix_sha256'] or parent['prefix_bytes']!=dep['journal_prefix_bytes']:raise ValueError('resume journal anchor changed')
    return dict(status='PASS',raw_files=len(checked),journal_events=ledger['events'],gates_closed=True)


def run(root,config_path,output,resume_from=None,network=False,*,transport_factory=CompactTrialTransport):
    root=Path(root).resolve();cfgpath=inside(root,config_path,'configs');c=json.loads(cfgpath.read_bytes())
    plan,members=prepare(root,c);pins=source_pins(root);refs=load_references(root,c)
    with epoch_lock(root,c) as epoch:
        entries=sorted(epoch.glob('[0-9]*'))
        if entries:
            verify_inventory(entries[-1]);pointer=json.loads((entries[-1]/'run.json').read_bytes())
            if resume_from!=pointer['path']:raise ValueError('epoch already started; resume latest '+pointer['path'])
        state=None;dependencies=[dict(run=c['reference_benchmark'],manifest_sha256=refs['manifest_sha256'],kind='REFERENCE')]
        if c.get('pilot_gate'):dependencies.append(dict(run=c['pilot_gate']['run'],manifest_sha256=c['pilot_gate']['manifest_sha256'],kind='PILOT_GATE'))
        if resume_from:
            parent=inside(root,resume_from,'data')
            if digest((parent/'config.json').read_bytes())!=digest(cfgpath.read_bytes()):raise ValueError('resume config changed')
            if json.loads((parent/'source-pins.json').read_bytes())!=pins:raise ValueError('resume code changed')
            sealed=(parent/'manifest.json').is_file()
            if sealed:verify(root,resume_from)
            ledger=read_compact(parent);state=ledger['state']
            dependencies.append(dict(run=resume_from,kind='RESUME',manifest_sha256=digest((parent/'manifest.json').read_bytes()) if sealed else None,
                journal_prefix_bytes=ledger['prefix_bytes'],journal_prefix_sha256=ledger['prefix_sha256']))
        out=inside(root,output,'data');out.mkdir(parents=True,exist_ok=False)
        immutable_write(out/'config.json',cfgpath.read_bytes());immutable_write(out/'source-pins.json',encoded(pins))
        immutable_write(out/'plan.json',encoded(plan));immutable_write(out/'references.json',encoded(refs))
        for name in SOURCES:immutable_write(out/'code'/name,(root/name).read_bytes())
        transport=transport_factory(root,out,c,state)
        if not state and c.get('seed_run'):
            seed=inside(root,c['seed_run'],'data');verify_inventory(seed)
            source=json.loads((seed/'results.json').read_bytes())
            dependencies.append(dict(run=c['seed_run'],kind='SEED',manifest_sha256=digest((seed/'manifest.json').read_bytes())))
            for item in source['requests']:
                if item['provider']=='CAFEF' and item['cohort']=='MAIN' and item['symbol'] in c['symbols'] and item['status']=='PARSED_CANDIDATES':
                    record={k:item[k] for k in ['symbol','report','statement','year','quarter','url','sha256']}
                    record['path']=(seed/item['path']).relative_to(root).as_posix()
                    record['origin']='PINNED_BENCHMARK_CACHE';transport.commit_cache(item['url'],record)
        immutable_write(out/'dependencies.json',encoded(dependencies))
        entry=epoch/f'{len(entries)+1:06d}';immutable_write(entry/'run.json',encoded(dict(path=out.relative_to(root).as_posix(),config_sha256=digest(cfgpath.read_bytes()))));seal(entry)
        cells=[];records=[];stopped=False;cache_hits=0;started=time.perf_counter()
        kinds={m['ticker']:m['proposed_company_type'] for m in members}
        def acquire(job):
            nonlocal stopped,cache_hits
            row=dict(job,at=now(),status='NOT_EXECUTED',cache_hit=False)
            try:
                cached=transport.state['cache'].get(job['url'])
                if cached:
                    path=inside(root,cached['path'],'data');body=path.read_bytes()
                    if digest(body)!=cached['sha256']:raise ValueError('cache checksum changed')
                    row.update(path=cached['path'],sha256=cached['sha256'],cache_hit=True,origin=cached['origin']);cache_hits+=1
                elif network:
                    transport.context=job
                    body,status=transport.get(job['url']);path=out/'raw'/(digest(body)+'.html')
                    if not path.exists():immutable_write(path,body)
                    row.update(path=path.relative_to(root).as_posix(),sha256=digest(body),origin='FRESH_PUBLIC_HTTPS',bytes=len(body))
                    transport.commit_cache(job['url'],{k:row[k] for k in ['symbol','report','statement','year','quarter','url','path','sha256','origin']})
                else:
                    row['status']='MISSING_OFFLINE_CACHE';records.append(row);return
                parsed=parse(body,row,kinds[job['symbol']]);cells.extend(parsed);row.update(status='PARSED_CANDIDATES',wire_cells=len(parsed))
            except (AccessControlError,RateLimitError) as exc:stopped=True;row.update(status='HARD_STOP',error=str(exc))
            except TrialBudgetError as exc:stopped=True;row.update(status='BUDGET_STOP',error=str(exc))
            except (ValueError,KeyError,TypeError,OSError) as exc:row.update(status='ERROR',error=str(exc))
            records.append(row)
            with (out/'work-log.jsonl').open('a',encoding='utf8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        base=jobs(c)
        for offset in range(0,len(c['symbols']),10):
            symbols=c['symbols'][offset:offset+10]
            for job in base:
                if job['symbol'] in symbols and not stopped:acquire(job)
            print(json.dumps(dict(stage='BASE_WAVE',symbols=symbols,records=len(records),attempts=transport.state['transport_attempts'],stopped=stopped)),flush=True)
            if stopped:break
        coverage,_,_,_=exports(cells,c,members)
        gap_count=0
        for gap in coverage:
            if gap['wire_present'] or stopped or gap_count>=c['gap_request_limit']:continue
            statement=REPORTS[gap['report']];url=detail_url(gap['symbol'],statement,gap['year'],gap['quarter'])
            if any(r['url']==url for r in records):continue  # No repeated malformed/HTTP302 anchors.
            acquire(dict(symbol=gap['symbol'],report=gap['report'],statement=statement,year=gap['year'],quarter=gap['quarter'],
                period='year' if gap['quarter']==0 else 'quarter',phase='GAP',kind='structured',url=url));gap_count+=1
        coverage,requirements,tasks,conflicts=exports(cells,c,members)
        comparisons=[r for r in qa(cells,refs['references']) if r['provider']=='CAFEF']
        exceptions=[r for r in comparisons if r['status']!='MATCH_WITHIN_TOLERANCE']
        queue=[dict(stage='PERIOD_GAP',**r) for r in coverage if not r['wire_present']]
        queue += [dict(stage='NUMERIC_CONFLICT',**r) for r in conflicts]
        queue += [dict(stage='REFERENCE_QA',**r) for r in exceptions]
        queue += [dict(stage='EXACT_DOCUMENT_NOTES_PUBLICATION_REVISION',symbol=s,year=y,
            proposed_company_type=kinds[s],note_fields=NOTES,automatic_download=False,
            reason='EPS_NOTES_SCOPE_UNITS_PIT_REVISIONS_EVENTS_REQUIRE_DOCUMENT_EVIDENCE') for s in c['symbols'] for y in c['annual_years']]
        queue += [dict(stage='SECTOR_TEMPLATE',symbol=s,proposed_company_type=kinds[s],reason='NO_REGULAR_NUMERIC_MAPPING') for s in c['symbols'] if kinds[s]!='Regular']
        queue += [dict(stage='REQUEST_EXCEPTION',**r) for r in records if r['status'] in ('ERROR','HARD_STOP','BUDGET_STOP','MISSING_OFFLINE_CACHE')]
        success=sum(r['status']=='PARSED_CANDIDATES' and r['phase']=='BASE' for r in records)
        baseline=json.loads((inside(root,c['reference_benchmark'],'data')/'qa.json').read_bytes())
        expected={(r['symbol'],r['year'],r['field']):(r['status'],r['candidate_values']) for r in baseline if r['provider']=='CAFEF' and r['symbol'] in c['symbols']}
        observed={(r['symbol'],r['year'],r['field']):(r['status'],r['candidate_values']) for r in comparisons}
        qa_replay_matches=expected==observed
        pilot_pass=len(c['symbols'])==4 and set(c['symbols'])=={'FPT','VNM','PVS','ACV'} and success==48 and not stopped and len(comparisons)==78 and qa_replay_matches
        status='HARD_STOP' if transport.state['boundary'] else 'BUDGET_STOP' if transport.state['budget_stop'] else 'PARTIAL' if any(r['status']!='PARSED_CANDIDATES' for r in records) or any(not r['wire_present'] for r in coverage) else 'COMPLETE_CANDIDATE_COLLECTION'
        transport.event('FINISH',engineering_status=status)
        result=dict(version=VERSION,source='CAFEF_DETAIL',engineering_status=status,pilot_preflight_pass=pilot_pass,
            source_pins=pins,symbols=c['symbols'],attempted_symbols=len({r['symbol'] for r in records}),
            base_expected=len(base),base_success=success,gap_requests=gap_count,requests=records,cache_hits=cache_hits,
            wire_cells=len(cells),present_statement_periods=sum(r['wire_present'] for r in coverage),target_statement_periods=len(coverage),
            qa_counts=dict(Counter(r['status'] for r in comparisons)),qa_replay_matches_benchmark=qa_replay_matches,conflicts=len(conflicts),review_queue_items=len(queue),
            collection_seconds=time.perf_counter()-started,trial_totals=transport.state,accepted_facts=0,
            strict_tasks_ready=0,pdf_downloads=0,ocr_pages=0,next_100_allowed=False,**CLOSED)
        for name,obj in [('results.json',result),('coverage.json',coverage),('requirements.json',requirements),('feature-readiness.json',tasks),('qa.json',comparisons),('review-queue.json',queue)]:immutable_write(out/name,encoded(obj))
        immutable_write(out/'candidates.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in cells).encode('utf8'))
        for name,rows in [('coverage.csv',coverage),('requirements.csv',requirements),('feature-readiness.csv',tasks)]:
            fields=[k for k in rows[0] if k not in ('evidence','inputs')];immutable_write(out/name,csv_bytes(rows,fields))
        seal(out);verification=verify(root,out.relative_to(root).as_posix())
        print(json.dumps(dict(stage='FINISH',status=status,attempted_symbols=result['attempted_symbols'],base_success=success,
            wire_periods=result['present_statement_periods'],target_periods=len(coverage),cache_hits=cache_hits,
            physical_attempts=transport.state['transport_attempts'],pilot_preflight_pass=pilot_pass,verification=verification)),flush=True)
        return result


def prepare50(root,pilot_run,output):
    root=Path(root).resolve();verify(root,pilot_run);pilot=inside(root,pilot_run,'data')
    result=json.loads((pilot/'results.json').read_bytes());c=json.loads((pilot/'config.json').read_bytes())
    if not result['pilot_preflight_pass'] or result['source_pins']!=source_pins(root):raise ValueError('pilot engineering gate not passed/current')
    plan=json.loads(inside(root,c['plan_path'],'configs').read_bytes())
    c.update(symbols=[m['ticker'] for m in plan['members']],seed_run=None,cache_epoch='cafef-financial-50-20261008-v1',gap_request_limit=120,
        pilot_gate=dict(run=pilot_run,manifest_sha256=digest((pilot/'manifest.json').read_bytes())))
    path=inside(root,output,'configs');prepare(root,c);immutable_write(path,encoded(c))
    return dict(status='PREPARED_CANDIDATE_TRIAL50',path=output,symbols=len(c['symbols']),**CLOSED)


def feedback(root,relative,output):
    verify(root,relative);root=Path(root).resolve();folder=inside(root,relative,'data');destination=inside(root,output,'artifacts')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as pack:
        for name in ['results.json','coverage.csv','requirements.csv','feature-readiness.csv','qa.json','source-pins.json','config.json']:
            pack.write(folder/name,name)
    return dict(status='FEEDBACK_READY',path=output,includes_raw=False)
