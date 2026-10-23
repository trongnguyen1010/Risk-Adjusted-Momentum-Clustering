import copy,unittest
from delta_t1.experiments.financial_acquisition_first import select_members,validate_budget
from delta_t1.experiments.financial_history_batch import tasks
class AcquisitionFirstTests(unittest.TestCase):
 def fixture(self):
  rows=[dict(registry_id=f'R{i:02}',ticker=f'S{i}',exchange='HOSE',legacy_security_id=f'L{i}',company_name='Company') for i in range(32)]
  legacy=[dict(ticker=r['ticker'],exchange=r['exchange'],security_id=r['legacy_security_id']) for r in rows]
  return rows,legacy
 def test_assignment_is_deterministic_and_provisional(self):
  r,l=self.fixture();a,d=select_members(r,l,set());self.assertEqual(len(a),30);self.assertEqual(len(d),2)
  self.assertEqual((a,d),select_members(r[::-1],l[::-1],set()))
  self.assertTrue(all(not x['historical_identity_ready'] for x in a))
  jobs=tasks(a[:15])+tasks(a[15:]);self.assertEqual(len(jobs),6600);self.assertEqual(len({j['id'] for j in jobs}),6600)
 def test_ambiguous_identity_rejected(self):
  r,l=self.fixture();r.append(r[0]);self.assertRaisesRegex(ValueError,'ambiguous',select_members,r,l,set())
 def test_existing_symbols_excluded_not_recrawled(self):
  r,l=self.fixture();a,_=select_members(r,l,{'S0','S1'});self.assertNotIn('S0',{x['symbol'] for x in a})
 def config(self):
  s=dict(logical_requests=10,transport_attempts=10,pdf_download_attempts=2,downloaded_bytes=100)
  c=dict(approved_hosts=['apiweb.cafef.vn'],network_concurrency=1,max_campaign_days=90,years=list(range(2013,2026)),auxiliary_balance_year=2012,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,next50_allowed=False,budgets=dict(max_logical_requests=4210,max_transport_attempts=8410,max_pdf_download_attempts=2,max_response_bytes=5000000,max_total_downloaded_bytes=2000000100,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=2))
  return c,s
 def test_no_budget_reset_or_pdf_expansion(self):
  c,s=self.config();validate_budget(c,s)
  for key in ['max_logical_requests','max_pdf_download_attempts','max_wall_seconds','max_attempts_per_request']:
   changed=copy.deepcopy(c);changed['budgets'][key]+=1;self.assertRaises(ValueError,validate_budget,changed,s)
 def test_downstream_gates_stay_closed(self):
  c,s=self.config();c['numeric_acceptance_allowed']=True;self.assertRaises(ValueError,validate_budget,c,s)
if __name__=='__main__':unittest.main()
