import copy,unittest
from delta_t1.experiments.financial_acquisition_waves import validate_assignment,validate_budget,report_tasks
from delta_t1.experiments.financial_acquisition_batches import tasks
class WaveTests(unittest.TestCase):
 def test_api_tasks_exactly_preserved_without_latched_catalogue_placeholders(self):
  _,a=self.fixture();members=a['members'][:1]
  expected=[t for t in tasks(members) if t['kind']=='REPORT'];actual=report_tasks(members)
  self.assertEqual(actual,expected);self.assertEqual(len(actual),140)
  self.assertTrue(all(t['url'].startswith('https://apiweb.cafef.vn/') for t in actual))
 def fixture(self):
  rows=[];members=[]
  for i in range(800):
   ticker=f'{i:03d}';rid='R'+ticker;legacy='KBS:HOSE:'+ticker
   rows.append(dict(registry_id=rid,ticker=ticker,exchange='HOSE',legacy_security_id=legacy))
   members.append(dict(registry_id=rid,symbol=ticker,exchange='HOSE',legacy_security_id=legacy,provider_partition_id='PROVISIONAL:CAFEF:'+rid,historical_identity_ready=False))
  return rows,dict(members=members[500:],previous_members=members[:500])
 def test_exact_disjoint_wave300_after_previous500(self):
  rows,a=self.fixture();self.assertEqual(len(validate_assignment(rows,a)),300)
  for change in ['duplicate','prior','promotion','oversize']:
   bad=copy.deepcopy(a)
   if change=='duplicate':bad['members'][-1]=bad['members'][0]
   if change=='prior':bad['members'][0]=bad['previous_members'][0]
   if change=='promotion':bad['members'][0]['historical_identity_ready']=True
   if change=='oversize':bad['members'].append(bad['members'][0])
   self.assertRaises(ValueError,validate_assignment,rows,bad)
 def test_budget_preserves_deadline_rate_attempts_and_pdf(self):
  s=dict(logical_requests=46724,transport_attempts=46728,downloaded_bytes=636937280,pdf_download_attempts=20)
  c=dict(approved_hosts=['apiweb.cafef.vn'],network_concurrency=1,max_campaign_days=90,years=list(range(2013,2026)),auxiliary_balance_year=2012,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,budgets=dict(max_logical_requests=88724,max_transport_attempts=130728,max_pdf_download_attempts=20,max_response_bytes=5000000,max_total_downloaded_bytes=2636937280,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=.4))
  validate_budget(c,s,300)
  for key,value in [('max_wall_seconds',300000),('min_seconds_between_transport_attempts',.2),('max_attempts_per_request',3),('max_pdf_download_attempts',21)]:
   bad=copy.deepcopy(c);bad['budgets'][key]=value;self.assertRaises(ValueError,validate_budget,bad,s,300)
  c['network_concurrency']=2;self.assertRaises(ValueError,validate_budget,c,s,300)
if __name__=='__main__':unittest.main()
