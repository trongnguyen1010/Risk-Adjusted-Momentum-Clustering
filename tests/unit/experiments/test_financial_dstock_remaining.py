import json,unittest
from pathlib import Path
from delta_t1.experiments.financial_dstock_recovery_v4 import check_case,periods,completed_keys,fresh_targets
from delta_t1.ingestion.dstock_financial import model_index

class RemainingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(__file__).resolve().parents[3];p=cls.root/'data/financial/history_dstock_api_probe_v1/raw'
  cls.models=model_index(json.loads((p/'c832ae998da167669b6e6ac9d51d8a0a74df8640d2c203ed8c35c3d127a40876.html').read_bytes()))
  cls.rows=[r for r in json.loads((p/'1ee7f2b0fa293cf14db18d23cc941edc7aa0788f6d2a34e67be5f1fabb553eee.html').read_bytes())['data'] if r['code']=='VHC']
 def test_control_passes_all_15_checks(self):
  c=check_case(self.rows,'VHC',2024,self.models);self.assertTrue(c['eligible_reference']);self.assertTrue(c['cash_qa']['quality_gate'])
 def test_cash_mismatch_blocks_even_if_old12_checks_pass(self):
  rows=[dict(r) for r in self.rows]
  for r in rows:
   if int(r['itemCode'])==11100:r['numericValue']+=1000
  c=check_case(rows,'VHC',2024,self.models);self.assertTrue(c['qa']['quality_gate']);self.assertFalse(c['eligible_reference']);self.assertIn('CASHFLOW_TOTAL_OR_STOCK_QA_HELD',c['reasons'])
 def test_period_count_supports_both_frozen_coverage_schemas(self):
  self.assertEqual(periods({'observed_periods':'10'}),10);self.assertEqual(periods({'after_periods':'9'}),9)
 def test_previously_held_keys_do_not_get_re_requested(self):
  prior=completed_keys([dict(target=dict(registry_id='A',year=2024),eligible_reference=False)])
  self.assertEqual(fresh_targets([dict(registry_id='A',year='2024'),dict(registry_id='A',year='2025')],prior),[dict(registry_id='A',year='2025')])
 def test_real_scope_is_1647_fresh_cases_on_360_candidates(self):
  import csv
  p=self.root/'data/financial/history_dstock_cash_review_v1/results/7632cb40dafdcf943d41'
  with (p/'remaining-document-review-candidates.csv').open(encoding='utf-8-sig') as stream:gaps=list(csv.DictReader(stream))
  todo=fresh_targets(gaps,completed_keys(json.loads((p/'cases.json').read_bytes())))
  self.assertEqual(len(todo),1647);self.assertEqual(len({r['registry_id'] for r in todo}),360)
if __name__=='__main__':unittest.main()
