"""Complete remaining unattempted DStock scope, preserving old terminal cases."""
import time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_dstock_recovery_v4 import prepare,execute,consolidate,status
from delta_t1.experiments.financial_user_workflow import exclusive
from delta_t1.experiments.financial_history_documents import put
from delta_t1.experiments.financial_pdf_pipeline import file_hash
c,out,contract=prepare(ROOT,'configs/experiments/financial_dstock_recovery_v4.json')
stages=[50,100,200,300,360]
put(out/'campaign-driver.json',dict(path='scripts/financial_dstock_remaining_campaign.py',sha256=file_hash(Path(__file__)),stages=stages,authorization_deadline=c['authorization_deadline'],goal='ATTEMPT_ALL_1647_REMAINING_CASES_ON_360_CANDIDATES',stop_at_1000=False,original_absolute_caps_unchanged=True))
with exclusive(out):
 last=0
 try:
  for limit in stages:
   if time.time()>=c['authorization_deadline']:raise ValueError('renewed scope window expired')
   result=execute(ROOT,c,out,contract,limit,True);last=limit
  status(out,phase='ALL_REMAINING_API_CASES_REVIEWED',stage_limit=last,summary=result)
 except Exception as error:
  result=consolidate(ROOT,c,out,contract,last)
  status(out,phase='REMAINING_CAMPAIGN_STOPPED_REVIEW_REQUIRED',error=str(error),stage_limit=last,summary=result);raise
