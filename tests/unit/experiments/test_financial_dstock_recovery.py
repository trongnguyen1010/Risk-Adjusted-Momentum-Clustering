import unittest,json
from pathlib import Path
from delta_t1.ingestion.dstock_financial import model_index
from delta_t1.experiments.financial_dstock_recovery_v3 import check_case

class RecoveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  root=Path(__file__).resolve().parents[3];p=root/'data/financial/history_dstock_api_probe_v1/raw'
  cls.models=model_index(json.loads((p/'c832ae998da167669b6e6ac9d51d8a0a74df8640d2c203ed8c35c3d127a40876.html').read_bytes()))
  cls.rows=json.loads((p/'1ee7f2b0fa293cf14db18d23cc941edc7aa0788f6d2a34e67be5f1fabb553eee.html').read_bytes())['data']
 def case(self,symbol='VHC',rows=None):return check_case([r for r in (rows if rows is not None else self.rows) if r['code']==symbol],symbol,2024,self.models)
 def test_positive_control_passes_without_duplicate_reasons_error(self):self.assertTrue(self.case()['eligible_reference'])
 def test_incomplete_cashflow_decomposition_is_explicit_diagnostic(self):
  c=self.case();self.assertNotEqual(float(c['cfo_component_residual']),0);self.assertIn('DIAGNOSTIC',c['cfo_component_completeness'])
 def test_missing_cfo_never_filled(self):
  c=self.case(rows=[r for r in self.rows if int(r['itemCode'])!=32000]);self.assertFalse(c['eligible_reference']);self.assertIn('MISSING_INPUTS',c['reasons'])
 def test_accounting_mismatch_held(self):
  rows=[dict(r) for r in self.rows]
  for r in rows:
   if r['code']=='VHC' and int(r['itemCode'])==12700:r['numericValue']+=100
  self.assertFalse(self.case(rows=rows)['eligible_reference'])
 def test_duplicate_even_equal_held(self):
  row=next(r for r in self.rows if r['code']=='VHC');self.assertFalse(self.case(rows=self.rows+[row])['eligible_reference'])
 def test_gates_remain_closed(self):
  c=self.case();self.assertFalse(c['strict_pit_ready']);self.assertFalse(c['financial_features_allowed']);self.assertIsNone(c['published_at'])
if __name__=='__main__':unittest.main()
