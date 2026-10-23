import copy,unittest
from delta_t1.experiments.financial_acquisition_rate1 import validate_policy,prior_request_allowed,verify_inheritance
class RateSuccessorTests(unittest.TestCase):
 def fixture(self):
  old=dict(budgets=dict(min_seconds_between_transport_attempts=2,max_wall_seconds=259200,max_attempts_per_request=2,max_logical_requests=23994),network_concurrency=1,years=list(range(2013,2026)),auxiliary_balance_year=2012,approved_hosts=['apiweb.cafef.vn'],max_campaign_days=90,cache_epoch='same-epoch',numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False)
  c=copy.deepcopy(old);c['budgets']['min_seconds_between_transport_attempts']=1;return c,old
 def test_only_rate_changes_no_budget_reset(self):
  c,o=self.fixture();validate_policy(c,o)
  for k in ['max_wall_seconds','max_logical_requests','max_attempts_per_request']:
   b=copy.deepcopy(c);b['budgets'][k]+=1;self.assertRaises(ValueError,validate_policy,b,o)
 def test_host_concurrency_or_epoch_change_rejected(self):
  c,o=self.fixture()
  for k,v in [('network_concurrency',2),('cache_epoch','reset'),('approved_hosts',['other'])]:
   b=copy.deepcopy(c);b[k]=v;self.assertRaises(ValueError,validate_policy,b,o)
 def test_cannot_decrease_below_approved_interval(self):
  c,o=self.fixture();c['budgets']['min_seconds_between_transport_attempts']=.1;self.assertRaises(ValueError,validate_policy,c,o)
 def test_prior_request_must_be_exact_proved_unattempted_reservation(self):
  c=dict(authorized_unattempted_url='https://apiweb.cafef.vn/exact');task=dict(url=c['authorized_unattempted_url']);q=dict(url=task['url'],kind='structured',attempts=0)
  self.assertTrue(prior_request_allowed(c,task,[q]));self.assertTrue(prior_request_allowed(c,task,[]))
  self.assertFalse(prior_request_allowed(c,task,[dict(q,attempts=1)]));self.assertFalse(prior_request_allowed(c,dict(url='other'),[q]));self.assertFalse(prior_request_allowed(c,task,[q,q]))
 def test_only_reserved_attempt_counter_can_change(self):
  seed=dict(created_at=123,requests=dict(done=dict(url='a',attempts=1),pending=dict(url='b',kind='structured',attempts=0)))
  state=copy.deepcopy(seed);state['requests']['pending']['attempts']=1;verify_inheritance(state,seed,'pending')
  state['requests']['done']['attempts']=2;self.assertRaises(ValueError,verify_inheritance,state,seed,'pending')
 def test_source_anchor_and_request_identity_must_survive(self):
  seed=dict(created_at=123,requests=dict(pending=dict(url='b',attempts=0)))
  state=copy.deepcopy(seed);state['created_at']=124;self.assertRaises(ValueError,verify_inheritance,state,seed,'pending')
  state=copy.deepcopy(seed);state['requests']['pending']['url']='c';self.assertRaises(ValueError,verify_inheritance,state,seed,'pending')
class ReservedTransportTests(unittest.TestCase):
 def test_unattempted_request_reuses_original_key_and_waits_one_second(self):
  import tempfile
  from pathlib import Path
  from delta_t1.experiments.financial_history_documents import DocumentTransport
  from delta_t1.ingestion.cafef_financial import digest,encoded
  url='https://apiweb.cafef.vn/api/test';epoch='same'
  key=digest(encoded(dict(url=url,kind='structured',cache_epoch=epoch)))
  seed=dict(created_at=1000,logical_requests=1,transport_attempts=0,pdf_download_attempts=0,downloaded_bytes=0,reserved_bytes=0,text_pages=0,reserved_text_pages=0,requests={key:dict(url=url,kind='structured',attempts=0)},boundary=False,budget_stop=False,stop_reason=None)
  c=dict(approved_hosts=['apiweb.cafef.vn'],cache_epoch=epoch,budgets=dict(max_logical_requests=10,max_transport_attempts=20,max_pdf_download_attempts=1,max_total_downloaded_bytes=10000,max_response_bytes=1000,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=1))
  clock=[1000.0];sleeps=[]
  class Response:
   status=200
   def __enter__(self):self.sent=False;return self
   def __exit__(self,*a):pass
   def read(self,n):
    if self.sent:return b''
    self.sent=True;return b'{}'
  class Opener:
   def open(self,*a,**k):return Response()
  def sleep(delay):sleeps.append(delay);clock[0]+=delay
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);transport=DocumentTransport(root,root/'network',c,seed,opener=Opener(),sleep=sleep,clock=lambda:clock[0],utc=lambda:clock[0]);transport.context=dict(kind='structured')
   self.assertEqual(transport.get(url),(b'{}',200));self.assertEqual(transport.state['logical_requests'],1);self.assertEqual(transport.state['transport_attempts'],1);self.assertEqual(transport.state['requests'][key]['attempts'],1);self.assertEqual(sleeps,[1.0])
if __name__=='__main__':unittest.main()
