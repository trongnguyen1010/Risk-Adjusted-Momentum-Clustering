"""Owner-authorized one-hour continuation, sequential stages and fixed deadline."""
import sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_dstock_recovery_v3 import prepare,execute,status,consolidate
from delta_t1.experiments.financial_user_workflow import exclusive
from delta_t1.experiments.financial_history_documents import put
from delta_t1.experiments.financial_pdf_pipeline import file_hash
CONFIG='configs/experiments/financial_dstock_recovery_v3.json'
c,out,contract=prepare(ROOT,CONFIG)
stages=[20,50,100,200,300,400,500,600,700,800,900,960]
put(out/'campaign-driver.json',dict(path='scripts/financial_dstock_campaign.py',sha256=file_hash(Path(__file__)),stages=stages,
 authorization_deadline=c['authorization_deadline'],stop_at_full10_more_than=1000,max_new_candidates_per_stage=100,source_contract=file_hash(out/'contract.json')))
with exclusive(out):
 last=10
 try:
  for limit in stages:
   if time.time()>=c['authorization_deadline']:break
   result=execute(ROOT,c,out,contract,limit,True);last=limit
   if limit==20 and result['reference_candidate_passes']<3:raise ValueError('PILOT_REFERENCE_YIELD_GATE_NOT_MET')
   if result['full10_after']>1000:
    status(out,phase='COVERAGE_TARGET_REACHED',stage_limit=limit,summary=result);break
  else:status(out,phase='ALL_FROZEN_GAP_TARGETS_REVIEWED',stage_limit=last,summary=result)
 except Exception as error:
  # Safely materialize completed receipts offline; no network retry on boundary.
  recovered=consolidate(ROOT,c,out,contract,last)
  status(out,phase='CAMPAIGN_STOPPED_REVIEW_REQUIRED',error=str(error),summary=recovered,stage_limit=last);raise
