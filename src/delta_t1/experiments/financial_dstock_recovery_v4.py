"""Bounded DStock gap acquisition and complete-vector exploratory successor."""
import argparse,csv,io,json,os,sys,time
from decimal import Decimal
from pathlib import Path
from collections import Counter,defaultdict
from urllib.parse import urlsplit
from .financial_history_documents import put,read
from .financial_pdf_pipeline import PipelineTransport,load_journal,file_hash
from .financial_user_workflow import exclusive
from .financial_precision_review import evaluate
from .financial_dstock_cash_gate import cash_checks
from .financial_api_input_review import csv_bytes
from .financial_direct_cashflow_review import longest_run
from ..ingestion.dstock_financial import model_index,vector,url,parse_page,HOST
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from ..features.financial_exploratory import calculate_core,REQUIRED

VERSION='financial-dstock-recovery-v4'
CODE=['src/delta_t1/ingestion/dstock_financial.py','src/delta_t1/experiments/financial_dstock_recovery_v4.py',
 'src/delta_t1/experiments/financial_dstock_cash_gate.py','src/delta_t1/experiments/financial_precision_review.py','src/delta_t1/features/financial_exploratory.py',
 'src/delta_t1/experiments/financial_api_input_review.py','src/delta_t1/experiments/financial_template_contract.py',
 'src/delta_t1/ingestion/financial_trial_transport.py','src/delta_t1/ingestion/financial_compact_trial.py',
 'src/delta_t1/experiments/financial_pdf_pipeline.py','scripts/financial_dstock_recovery_v4.py']
def table(p):return list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig'))))
def periods(row):return int(row.get('after_periods',row.get('observed_periods',0)))
def completed_keys(cases):return {(r['target']['registry_id'],int(r['target']['year'])) for r in cases}
def fresh_targets(gaps,prior):return [r for r in gaps if (r['registry_id'],int(r['year'])) not in prior]
def status(out,**data):
 data.update(updated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),version=VERSION)
 p=out/'pipeline-status.json';tmp=p.with_suffix('.tmp');tmp.write_bytes(encoded(data));os.replace(tmp,p)
 with (out/'worker.log').open('ab') as stream:stream.write(encoded(data)+b'\n')
 print(json.dumps(data),flush=True)

def prepare(root,config):
 c=read(inside(root,config));out=inside(root,c['output_root']);out.mkdir(parents=True,exist_ok=True)
 if c['version']!=VERSION or c['scope']!='EXPLORATORY_REFERENCE_ONLY' or any(c[x] is not False for x in ['pdf_allowed','ocr_allowed','pit_allowed','research_promotion_allowed']):raise ValueError('reference contract required')
 if c['concurrency']!=1 or c['budgets']['min_seconds_between_transport_attempts']<2 or c['budgets']['max_attempts_per_request']!=2:raise ValueError('transport safety changed')
 if c['approved_hosts']!=[HOST] or c['authorization_deadline']>c['authorization_started_at']+3600:raise ValueError('authorized window exceeded')
 if c['batch_deadline']>c['authorization_deadline'] or c['batch_deadline']>c['campaign_deadline']:raise ValueError('deadline reset')
 pins={}
 def pin(p,h=None):
  actual=file_hash(inside(root,p))
  if h and h!=actual:raise ValueError('pinned input changed:'+p)
  pins[p]=actual
 for p in CODE+[config]:pin(p)
 for x in ['parent_journal','models','control','reference_control','source_pilot_manifest','source_contract','registry','completed_cases']:pin(c[x]['path'],c[x]['sha256'])
 for x in c['source_frontend_assets']:pin(x['path'],x['sha256'])
 for x in c.get('seed_jobs',[]):
  pin(x['path'],x['sha256'])
  job=read(inside(root,x['path']))
  for case in job['cases']:
   for raw in case['raw_sources']:pin(raw['path'],raw['sha256'])
  put(out/'jobs'/Path(x['path']).name,job)
 base=c['baseline'];pin(base['path']+'/manifest.json',base['manifest_sha256'])
 for name,h in read(inside(root,base['path']+'/manifest.json')).items():pin(base['path']+'/'+name,h)
 oldcontract=read(inside(root,c['source_contract']['path']));blocked=set(oldcontract['blocked_hosts'])
 boundary_pins=dict(oldcontract['boundary_pins'])
 boundary_pins[c['parent_journal']['path']]=c['parent_journal']['sha256']
 cp=out/'contract.json'
 if cp.exists():
  contract=read(cp)
  if contract['pins']!=pins:raise ValueError('frozen acquisition inputs changed')
  for p,h in contract['boundary_pins'].items():
   if file_hash(inside(root,p))!=h:raise ValueError('imported boundary changed')
  return c,out,contract
 for basepath in c['boundary_roots']:
  for p in inside(root,basepath).rglob('transport.jsonl'):
   if p.is_relative_to(out):continue
   rel=p.relative_to(root).as_posix()
   if rel in boundary_pins:
    if file_hash(p)!=boundary_pins[rel]:raise ValueError('boundary pin changed:'+rel)
   else:
    ledger=load_journal(p);boundary_pins[rel]=ledger['sha256'];st=ledger['state']
    if st['boundary']:
     hosts={urlsplit(r['url']).hostname for r in list(st['requests'].values())[-1:]}
     if not hosts or None in hosts:raise ValueError('unknown boundary host')
     blocked.update(hosts)
 seed=load_journal(inside(root,c['parent_journal']['path']))['state']
 if seed['boundary'] or seed['budget_stop'] or seed['reserved_bytes'] or HOST in blocked:raise ValueError('unsafe parent/source')
 for cap,counter,extra in [('max_logical_requests','logical_requests',900),('max_transport_attempts','transport_attempts',1800),('max_total_downloaded_bytes','downloaded_bytes',250_000_000)]:
  if not seed[counter]<=c['budgets'][cap]<=seed[counter]+extra:raise ValueError('authorized budget amendment exceeded')
 contract=dict(version=VERSION,pins=pins,boundary_pins=boundary_pins,blocked_hosts=sorted(blocked),
  seed=seed,authorization=c['authorization'],acceptance_scope='EXPLORATORY_COMPLETE_PROVIDER_VECTOR_NOT_VERIFIED_FACT',budget_amendment=c['budget_amendment'])
 put(cp,contract);return c,out,contract

def fetch(root,out,c,t,uri):
 key=digest(uri.encode());p=out/'requests'/(key+'.json')
 if p.exists():
  r=read(p)
  if r.get('path') and file_hash(inside(root,r['path']))!=r['sha256']:raise ValueError('raw cache changed')
  return r
 if any(v['url']==uri for v in t.state['requests'].values()):raise ValueError('incomplete prior receipt requires review; no fresh retry')
 t.context=dict(kind='json',symbol='DSTOCK_GAP_GROUP')
 try:
  body,http=t.get(uri);path=out/'raw'/(digest(body)+'.json');put(path,body)
  r=dict(url=uri,status='ACQUIRED',http_status=http,path=path.relative_to(root).as_posix(),sha256=digest(body),bytes=len(body))
 except Exception as e:
  r=dict(url=uri,status='FAILED_OR_STOPPED',reason=str(e));put(p,r);raise
 put(p,r);return r

def check_case(rows,symbol,year,models):
 v=vector(rows,symbol,year,models);qa=evaluate(v['values']);calc=calculate_core(v['values'])
 cash=cash_checks({int(r['itemCode']):r['numericValue'] for r in rows if r['code']==symbol and r.get('numericValue') is not None})
 reasons=list(v['reasons'])
 if not qa['quality_gate']:reasons.append('ACCOUNTING_OR_FINANCE_QA_HELD')
 if not cash['quality_gate']:reasons.append('CASHFLOW_TOTAL_OR_STOCK_QA_HELD')
 if calc['values'] is None:reasons.append(calc['status'])
 if symbol in ['HSG','CTD']:reasons.append('KNOWN_FISCAL_CALENDAR_REVIEW_REQUIRED')
 return dict(v,qa=qa,cash_qa=cash,calculation=calc,reasons=sorted(set(reasons)),eligible_reference=not reasons,
  strict_pit_ready=False,research_ready=False,financial_features_allowed=False,published_at=None)

def execute(root,c,out,contract,stage_limit,network):
 baseline=inside(root,c['baseline']['path']);gaps=table(baseline/'remaining-document-review-candidates.csv');coverage=table(baseline/'coverage-by-symbol.csv')
 prior_completed=completed_keys(read(inside(root,c['completed_cases']['path'])))
 gaps=fresh_targets(gaps,prior_completed)
 byid={r['registry_id']:r for r in coverage};ids=sorted({r['registry_id'] for r in gaps},key=lambda rid:(-periods(byid[rid]),0 if byid[rid]['symbol'] in ['TCM','SIP','VPI'] else 1,rid))
 selected=set(ids[:stage_limit]);members=[r for r in gaps if r['registry_id'] in selected]
 models=model_index(read(inside(root,c['models']['path'])))
 # Pilot gate includes known complete source controls; acquisition alone is insufficient.
 control=read(inside(root,c['control']['path']));v=check_case([r for r in control['data'] if r['code']=='VHC'],'VHC',2024,models)
 if not v['eligible_reference']:raise ValueError('source positive control failed')
 ref=next(r for r in read(inside(root,c['reference_control']['path']))['reviews'] if r['symbol']=='VHC' and r['year']==2024)
 expected={f['field']:Decimal(f['value']) for f in ref['fields']}
 if any(Decimal(v['values'][f])!=expected[f] for f in REQUIRED):raise ValueError('PDF positive control mismatch')
 completed=prior_completed|{(r['target']['registry_id'],int(r['target']['year'])) for p in (out/'jobs').glob('*.json') for r in read(p)['cases']}
 grouping=defaultdict(list)
 for r in members:
  if (r['registry_id'],int(r['year'])) not in completed:grouping[int(r['year'])].append(r)
 jobs=[]
 for year,rr in sorted(grouping.items()):
  rr=sorted(rr,key=lambda r:r['registry_id'])
  for i in range(0,len(rr),5):jobs.append(dict(year=year,targets=rr[i:i+5]))
 t=None
 if network:
  if time.time()>=c['authorization_deadline']:raise ValueError('authorized one-hour window expired')
  t=PipelineTransport(root,out/'network',c,contract['seed'],batch_deadline=c['batch_deadline'],campaign_deadline=c['campaign_deadline'])
 n=sum((r['registry_id'],int(r['year'])) in completed for r in members)
 for job in jobs:
  key=digest(encoded(job));dest=out/'jobs'/(key+'.json')
  if dest.exists():n+=len(job['targets']);continue
  if not network:continue
  symbols=[r['symbol'] for r in job['targets']];year=job['year'];rows=[];refs=[];seen=set();page=1;total=None
  while True:
   rr=fetch(root,out,c,t,url(symbols,year,page));refs.append(rr)
   payload=parse_page(inside(root,rr['path']).read_bytes(),symbols,year,page)
   if total is None:total=(payload['totalElements'],payload['totalPages'])
   elif total!=(payload['totalElements'],payload['totalPages']):raise ValueError('pagination changed during request')
   rows.extend(payload['data'])
   if page>=max(1,payload['totalPages']):break
   page+=1
  if len(rows)!=total[0]:raise ValueError('pagination incomplete')
  cases=[]
  for target in job['targets']:
   records=[r for r in rows if r['code']==target['symbol']]
   cases.append(dict(target=target,**check_case(records,target['symbol'],year,models),raw_sources=refs,source_observations=len(records)))
  put(dest,dict(job=job,cases=cases));n+=len(job['targets'])
  status(out,phase='ACQUISITION_QA',stage_limit=stage_limit,stage_targets=len(members),stage_completed=n,stage_percent=round(100*n/len(members),2),latest_symbols=symbols,latest_year=year,local_transport_attempts=t.state['transport_attempts']-contract['seed']['transport_attempts'])
 return consolidate(root,c,out,contract,stage_limit)

def consolidate(root,c,out,contract,stage_limit):
 base=inside(root,c['baseline']['path']);old=table(base/'features.csv');coverage=table(base/'coverage-by-symbol.csv');gaps=table(base/'remaining-document-review-candidates.csv');keys={(r['registry_id'],int(r['year'])) for r in old};gapkeys={(r['registry_id'],int(r['year'])) for r in gaps}
 pins=dict(contract['pins']);cases=[];added=[];warnings=[]
 for p in sorted((out/'jobs').glob('*.json')):
  pins[p.relative_to(root).as_posix()]=file_hash(p)
  for case in read(p)['cases']:
   for raw in case['raw_sources']:
    rawpath=inside(root,raw['path'])
    if file_hash(rawpath)!=raw['sha256']:raise ValueError('case source changed')
    pins[raw['path']]=raw['sha256']
   target=case['target'];key=(target['registry_id'],int(target['year']));cases.append(case)
   if key not in gapkeys or key in keys:raise ValueError('target collision or non-gap')
   if case['eligible_reference']:
    added.append(dict(symbol=target['symbol'],registry_id=target['registry_id'],year=int(target['year']),**case['calculation']['values'],provider_type='DSTOCK_ANNUAL_SINGLE_PROVIDER_VECTOR',source_kind='DSTOCK_API_EXPLORATORY_COMPLETE_VECTOR',source_evidence=p.relative_to(root).as_posix(),qa_policy='financial-precision-review-v1+financial-dstock-cashflow-totals-gate-v1',recovery_policy=VERSION,scope='EXPLORATORY_PROVIDER_UNIT_SCOPE_VINTAGE_HYPOTHESIS_NOT_VERIFIED_FACT',unit='VND_PROVIDER_DISPLAY_SCALE_CONTROLLED_NOT_ALL_FACTS_VERIFIED',published_at=None,strict_pit_ready=False,research_ready=False,financial_features_allowed=False))
 for case in cases:
  if case['cfo_component_residual'] not in (None,'0','0.0'):warnings.append(dict(symbol=case['target']['symbol'],year=case['target']['year'],warning='INCOMPLETE_PROVIDER_CFO_DECOMPOSITION',residual=case['cfo_component_residual'],accepted_core_reference=case['eligible_reference']))
 # No cross-provider field repair. Every new row has one complete provider vector.
 data=sorted(old+added,key=lambda r:(r['registry_id'],int(r['year'])));counts=defaultdict(set)
 if len({(r['registry_id'],int(r['year'])) for r in data})!=len(data):raise ValueError('duplicate result key')
 for r in data:counts[r['registry_id']].add(int(r['year']))
 after=[dict(symbol=r['symbol'],registry_id=r['registry_id'],before_periods=periods(r),after_periods=len(counts[r['registry_id']]),valid_years=sorted(counts[r['registry_id']]),missing_years=sorted(set(range(2016,2026))-counts[r['registry_id']]),longest_consecutive_annual_periods=longest_run(counts[r['registry_id']]),full10=len(counts[r['registry_id']])==10,coverage_only_not_model_or_pit_acceptance=True) for r in coverage]
 addedkeys={(r['registry_id'],r['year']) for r in added};remaining=[r for r in gaps if (r['registry_id'],int(r['year'])) not in addedkeys]
 summary=dict(status='COMPLETE_STAGE_REFERENCE_GOAL_PARTIAL',stage_limit=stage_limit,processed_cases=len(cases),reference_candidate_passes=len(added),held_cases=len(cases)-len(added),rows_before=len(old),rows_after=len(data),full10_before=sum(periods(r)==10 for r in coverage),full10_after=sum(r['full10'] for r in after),distinct_candidates=sum(bool(v) for v in counts.values()),remaining_one_year_gap_candidates=sum(r['after_periods']==9 for r in after),remaining_regular_annual_gap_cases=len(remaining),consecutive_history_counts={str(n):sum(longest_run(v)>=n for v in counts.values()) for n in [3,5,8,10]},rows_by_year=dict(sorted(Counter(int(r['year']) for r in data).items())),hold_reasons=dict(Counter(s for r in cases for s in r['reasons'])),pdf_downloads=0,ocr_pages=0,strict_pit_ready=False,research_ready=False,verified_original_six_families_full_history_candidates=0)
 if summary['full10_after']>1000:summary['status']='REFERENCE_COVERAGE_OVER_1000_NOT_PIT_OR_SIX_FAMILY_COMPLETION'
 products={'features.csv':csv_bytes(data),'recovered-rows.csv':csv_bytes(added),'coverage-by-symbol.csv':csv_bytes(after),'remaining-document-review-candidates.csv':csv_bytes(remaining),'cases.json':encoded(cases),'warnings.json':encoded(warnings),'summary.json':encoded(summary),'input-pins.json':encoded(pins),'config.json':encoded(c)}
 manifest={n:digest(v) for n,v in products.items()};result=out/'results'/digest(encoded(manifest))[:20]
 for n,v in products.items():put(result/n,v)
 put(result/'manifest.json',encoded(manifest));ref=dict(path=result.relative_to(root).as_posix(),manifest_sha256=digest(encoded(manifest)))
 status(out,phase='STAGE_COMPLETE',stage_limit=stage_limit,result=ref,summary=summary)
 (out/'latest-result.json').write_bytes(encoded(ref));return summary

def main(root):
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--limit',type=int,default=10);p.add_argument('--network',action='store_true');a=p.parse_args()
 root=Path(root);c,out,contract=prepare(root,a.config)
 if not 1<=a.limit<=960:raise ValueError('invalid stage limit')
 with exclusive(out):
  try:execute(root,c,out,contract,a.limit,a.network)
  except Exception as error:
   status(out,phase='STOPPED_REVIEW_REQUIRED',error=str(error),stage_limit=a.limit);raise
