import unittest
from delta_t1.experiments.financial_dstock_cash_gate import cash_checks
class CashGateTests(unittest.TestCase):
 def values(self):return {32000:1000000000,33000:-200000000,34000:-300000000,35000:500000000,36000:1000000000,36100:0,37000:1500000000,11100:1500000000}
 def test_exact_totals_pass(self):self.assertTrue(cash_checks(self.values())['quality_gate'])
 def test_cash_stock_mismatch_held(self):
  v=self.values();v[11100]-=1000;self.assertFalse(cash_checks(v)['quality_gate'])
 def test_one_vnd_requires_both_caps(self):
  v=self.values();v[11100]-=1;self.assertTrue(cash_checks(v)['quality_gate'])
  v={k:x/1000 for k,x in self.values().items()};v[11100]-=1;self.assertFalse(cash_checks(v)['quality_gate'])
 def test_missing_never_zero_filled(self):
  v=self.values();del v[36100];r=cash_checks(v);self.assertFalse(r['quality_gate']);self.assertNotIn(36100,v)
 def test_booleans_not_numeric(self):
  v=self.values();v[36100]=False;self.assertFalse(cash_checks(v)['quality_gate'])
 def test_nonfinite_held(self):
  v=self.values();v[36100]='NaN';self.assertFalse(cash_checks(v)['quality_gate'])
 def test_negative_investment_and_financing_are_not_absed(self):
  v=self.values();cash_checks(v);self.assertEqual(v[33000],-200000000)
if __name__=='__main__':unittest.main()
