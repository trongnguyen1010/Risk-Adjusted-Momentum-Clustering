import copy,unittest
from unittest.mock import patch
from delta_t1.experiments.financial_failed_request_quarantine import validate_failed_request
from delta_t1.experiments.financial_acquisition_overnight_v2 import check_parent
class FailedRequestTests(unittest.TestCase):
 def fixture(self):
  q=dict(url='https://apiweb.cafef.vn/api/exact',attempts=2,kind='structured',symbol='DTR',report='CDKT')
  r=dict(status='FAILED_OR_STOPPED',task=dict(url=q['url']),reason='bounded transport attempts exhausted')
  e=dict(action='HTTP_ERROR',detail=dict(http_status=500,request_key='key',request_snapshot=copy.deepcopy(q)))
  return r,q,e
 def test_only_exact_http500_two_attempt_receipt_can_be_deferred(self):
  r,q,e=self.fixture();self.assertTrue(validate_failed_request(r,q,e,'key'))
  for status in [401,403,404,429,502]:
   bad=copy.deepcopy(e);bad['detail']['http_status']=status;self.assertRaises(ValueError,validate_failed_request,r,q,bad,'key')
  for attempts in [0,1,3]:
   bad=copy.deepcopy(q);bad['attempts']=attempts;self.assertRaises(ValueError,validate_failed_request,r,bad,e,'key')
 def test_identity_record_or_unbounded_failure_cannot_be_deferred(self):
  r,q,e=self.fixture()
  for change in ['url','record','reason','key','snapshot']:
   rr,qq,ee=copy.deepcopy(r),copy.deepcopy(q),copy.deepcopy(e)
   if change=='url':rr['task']['url']='other'
   if change=='record':rr['record']={'path':'raw'}
   if change=='reason':rr['reason']='unknown'
   if change=='key':ee['detail']['request_key']='other'
   if change=='snapshot':ee['detail']['request_snapshot']['symbol']='OTHER'
   self.assertRaises(ValueError,validate_failed_request,rr,qq,ee,'key')
 def test_parent_failure_count_latches_and_original_deadline(self):
  s=dict(created_at=1792414507.836684,boundary=False,budget_stop=False,reserved_bytes=0,requests={},cache={})
  summary=dict(status='COMPLETE_CANDIDATE_TASK_ACCOUNTING',parser_errors=0,task_statuses=dict(FAILED_OR_STOPPED=4),counters={k:v for k,v in s.items() if k not in ['requests','cache']});ledger=dict(state=s,torn_tail_bytes=0)
  with patch('delta_t1.experiments.financial_acquisition_overnight_v2.time.time',return_value=s['created_at']+100):
   self.assertEqual(check_parent(summary,ledger,[{}]*4),s)
   self.assertRaises(ValueError,check_parent,summary,ledger,[{}]*3)
   for key in ['boundary','budget_stop']:
    bad=copy.deepcopy(ledger);bad['state'][key]=True;self.assertRaises(ValueError,check_parent,summary,bad,[{}]*4)
  with patch('delta_t1.experiments.financial_acquisition_overnight_v2.time.time',return_value=s['created_at']+259201):self.assertRaises(ValueError,check_parent,summary,ledger,[{}]*4)
if __name__=='__main__':unittest.main()
