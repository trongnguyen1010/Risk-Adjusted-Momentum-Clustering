import copy,unittest
from delta_t1.experiments.financial_acquisition_batches import tasks,validate_assignment,validate_budget
from delta_t1.experiments.financial_acquisition_qa import classify_templates
from delta_t1.experiments.financial_history_batch import tasks as legacy_tasks
class BoundedBatchesTests(unittest.TestCase):
 def fixture(self,n=50):
  rows=[dict(registry_id=f'R{i}',ticker=f'{i:03}',exchange='HOSE',legacy_security_id=f'L{i}') for i in range(n+1)]
  members=[dict(registry_id=r['registry_id'],symbol=r['ticker'],exchange=r['exchange'],legacy_security_id=r['legacy_security_id'],provider_partition_id='PROVISIONAL:CAFEF:'+r['registry_id'],historical_identity_ready=False) for r in rows]
  return rows,dict(members=members[1:],previous_members=members[:1])
 def test_generic_tasks_preserve_pagination_and_urls(self):
  _,a=self.fixture(15);self.assertEqual(tasks(a['members']),legacy_tasks(a['members']))
  _,a=self.fixture();jobs=tasks(a['members']);self.assertEqual(len(jobs),11000);self.assertEqual(len({t['id'] for t in jobs}),11000)
  self.assertEqual(sum(t['kind']=='REPORT' for t in jobs),7000)
 def test_previous_domain_assignment_cannot_be_reassigned(self):
  r,a=self.fixture();validate_assignment(r,a);a['members'].append(a['previous_members'][0]);self.assertRaises(ValueError,validate_assignment,r,a)
 def test_ambiguous_registry_or_identity_promotion_rejected(self):
  r,a=self.fixture();self.assertRaises(ValueError,validate_assignment,r+[r[1]],a)
  a['members'][0]['historical_identity_ready']=True;self.assertRaises(ValueError,validate_assignment,r,a)
 def test_new_batch_does_not_expand_pdf_or_time_policy(self):
  s=dict(logical_requests=5644,transport_attempts=5644,pdf_download_attempts=20,downloaded_bytes=267795832)
  c=dict(approved_hosts=['apiweb.cafef.vn'],network_concurrency=1,max_campaign_days=90,years=list(range(2013,2026)),auxiliary_balance_year=2012,numeric_acceptance_allowed=False,financial_features_allowed=False,research_ready=False,budgets=dict(max_logical_requests=12644,max_transport_attempts=19644,max_pdf_download_attempts=20,max_response_bytes=5000000,max_total_downloaded_bytes=2267795832,max_wall_seconds=259200,max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=2))
  validate_budget(c,s,50)
  for k in ['max_pdf_download_attempts','max_wall_seconds','max_attempts_per_request','max_logical_requests']:
   changed=copy.deepcopy(c);changed['budgets'][k]+=1;self.assertRaises(ValueError,validate_budget,changed,s,50)
class TemplateClassificationTests(unittest.TestCase):
 def test_exact_known_template_only_permits_diagnostics(self):
  p,e=classify_templates([dict(symbol='X',statement='KQKD',template_sha256='A')],[dict(symbol='REF',proposed_company_type='Regular')],[dict(task=dict(symbol='REF',statement='KQKD'),template_sha256=['A'])])
  self.assertEqual(p[0]['proposed_company_type'],'Regular');self.assertFalse(e[0]['industry_accepted']);self.assertFalse(e[0]['pit_ready'])
 def test_unknown_ambiguous_or_mixed_templates_stay_unknown(self):
  ref=[dict(symbol='R',proposed_company_type='Regular'),dict(symbol='B',proposed_company_type='Bank')]
  templates=[dict(task=dict(symbol='R',statement='KQKD'),template_sha256=['A']),dict(task=dict(symbol='B',statement='KQKD'),template_sha256=['B'])]
  for hashes in [['NEW'],['A','NEW'],['A','B']]:
   p,_=classify_templates([dict(symbol='X',statement='KQKD',template_sha256=h) for h in hashes],ref,templates)
   self.assertEqual(p[0]['proposed_company_type'],'UNKNOWN')
 def test_bank_template_not_regular(self):
  p,e=classify_templates([dict(symbol='X',statement='KQKD',template_sha256='B')],[dict(symbol='REF',proposed_company_type='Bank')],[dict(task=dict(symbol='REF',statement='KQKD'),template_sha256=['B'])])
  self.assertEqual(p[0]['proposed_company_type'],'Bank');self.assertFalse(e[0]['regular_semantic_diagnostics_allowed'])
if __name__=='__main__':unittest.main()
