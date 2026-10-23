"""Offline conservative successor after additional complete CF totals/stock QA."""
import argparse,json
from pathlib import Path
from decimal import Decimal
from collections import Counter,defaultdict
from .financial_dstock_cash_gate import cash_checks
from .financial_history_documents import put,read
from .financial_pdf_pipeline import file_hash
from .financial_api_input_review import csv_bytes
from .financial_recovery_readiness import csv_rows,coverage
from .financial_direct_cashflow_review import longest_run
from ..ingestion.cafef_financial import encoded,digest
from ..ingestion.financial_batch_evidence import inside

def run(root,config):
 c=read(inside(root,config));pins={}
 if c['version']!='financial-dstock-cash-review-v1' or c['network_allowed'] or c['pdf_allowed'] or c['research_promotion_allowed']:raise ValueError('offline reference review required')
 def pin(p,h=None):
  path=inside(root,p);actual=file_hash(path)
  if h and actual!=h:raise ValueError('source changed:'+p)
  pins[p]=actual;return path
 for p in [config,'src/delta_t1/experiments/financial_dstock_cash_review.py','src/delta_t1/experiments/financial_dstock_cash_gate.py','src/delta_t1/experiments/financial_precision_review.py','scripts/financial_dstock_cash_review.py']:pin(p)
 source=c['input_result'];folder=inside(root,source['path']);manifest=read(pin(source['path']+'/manifest.json',source['manifest_sha256']))
 for name,h in manifest.items():pin(source['path']+'/'+name,h)
 for name,h in read(folder/'input-pins.json').items():pin(name,h)
 baseline=inside(root,c['baseline']['path']);base_manifest=read(pin(c['baseline']['path']+'/manifest.json',c['baseline']['manifest_sha256']))
 for name,h in base_manifest.items():pin(c['baseline']['path']+'/'+name,h)
 old=csv_rows(baseline/'features.csv');source_new=csv_rows(folder/'recovered-rows.csv');cases=read(folder/'cases.json');rawcache={};heldkeys=set();cashqa=[]
 for case in cases:
  if not case['eligible_reference']:continue
  target=case['target'];values={}
  for src in case['raw_sources']:
   if src['path'] not in rawcache:rawcache[src['path']]=json.loads(pin(src['path'],src['sha256']).read_bytes(),parse_float=Decimal)['data']
   for row in rawcache[src['path']]:
    if row['code']==target['symbol'] and row['fiscalDate']==str(target['year'])+'-12-31' and row['numericValue'] is not None:values[int(row['itemCode'])]=row['numericValue']
  qa=cash_checks(values);case['cash_qa']=qa
  cashqa.extend(dict(symbol=target['symbol'],registry_id=target['registry_id'],year=target['year'],**r) for r in qa['checks'])
  if not qa['quality_gate']:
   heldkeys.add((target['registry_id'],str(target['year'])));case['eligible_reference']=False
   case['reasons']=sorted(set(case['reasons']+['CASHFLOW_TOTAL_OR_STOCK_QA_HELD']))
 new=[dict(r,qa_policy='financial-precision-review-v1+financial-dstock-cashflow-totals-gate-v1',recovery_policy=c['version']) for r in source_new if (r['registry_id'],r['year']) not in heldkeys]
 data=sorted(old+new,key=lambda r:(r['registry_id'],int(r['year'])));registry=csv_rows(pin(c['registry']['path'],c['registry']['sha256']));cov=coverage(data,{r['registry_id']:r for r in registry});counts=defaultdict(set)
 for r in data:counts[r['registry_id']].add(int(r['year']))
 addedkeys={(r['registry_id'],int(r['year'])) for r in new};remaining=[r for r in csv_rows(baseline/'remaining-document-review-candidates.csv') if (r['registry_id'],int(r['year'])) not in addedkeys]
 summary=dict(status='REFERENCE_COVERAGE_OVER_1000_AFTER_ADDITIONAL_CASH_QA' if sum(r['full10'] for r in cov)>1000 else 'PARTIAL_AFTER_ADDITIONAL_CASH_QA',stage_limit=read(folder/'summary.json')['stage_limit'],processed_cases=len(cases),reference_candidate_passes=len(new),held_cases=len(cases)-len(new),cash_additional_held_cases=len(heldkeys),rows_before=len(old),rows_after=len(data),full10_before=469,full10_after=sum(r['full10'] for r in cov),distinct_candidates=sum(r['observed_periods']>0 for r in cov),remaining_one_year_gap_candidates=sum(r['observed_periods']==9 for r in cov),remaining_regular_annual_gap_cases=len(remaining),consecutive_history_counts={str(n):sum(r['longest_consecutive']>=n for r in cov) for n in [3,5,8,10]},rows_by_year=dict(sorted(Counter(int(r['year']) for r in data).items())),cash_check_statuses=dict(Counter(r['status'] for r in cashqa)),hold_reasons=dict(Counter(v for case in cases for v in case['reasons'])),pdf_downloads=0,ocr_pages=0,strict_pit_ready=False,research_ready=False,verified_original_six_families_full_history_candidates=0)
 products={'features.csv':csv_bytes(data),'recovered-rows.csv':csv_bytes(new),'cases.json':encoded(cases),'summary.json':encoded(summary),'coverage-by-symbol.csv':csv_bytes(cov),'remaining-document-review-candidates.csv':csv_bytes(remaining),'cashflow-qa.json':encoded(cashqa),'source-result-ref.json':encoded(source),'input-pins.json':encoded(pins),'config.json':encoded(c)}
 manifest={name:digest(raw) for name,raw in products.items()};out=inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
 for name,raw in products.items():put(out/name,raw)
 put(out/'manifest.json',encoded(manifest));ref=dict(path=out.relative_to(root).as_posix(),manifest_sha256=file_hash(out/'manifest.json'));put(inside(root,c['report_root'])/'cash-result-ref.json',ref)
 print(json.dumps(dict(result=ref,summary=summary)));return ref

def main(root):
 p=argparse.ArgumentParser();p.add_argument('--config',default='configs/experiments/financial_dstock_cash_review_v1.json');a=p.parse_args();run(Path(root),a.config)
