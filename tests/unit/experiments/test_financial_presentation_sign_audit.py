import unittest
from delta_t1.experiments.financial_presentation_sign_audit import hypothesis

class SignAuditTests(unittest.TestCase):
 def test_only_negative_cost_presentation_triggers_hypothesis(self):
  v=dict(cost_of_goods_sold='20',deferred_tax_expense='5',net_profit='-7')
  proposed,changes=hypothesis(v);self.assertEqual(proposed,v);self.assertEqual(changes,[])
 def test_negative_balances_profit_and_cfo_are_not_absed(self):
  v=dict(cost_of_goods_sold='-20',total_equity='-50',net_profit='-7',operating_cash_flow='-9',deferred_tax_expense='5')
  p,changes=hypothesis(v);self.assertEqual(p['total_equity'],'-50');self.assertEqual(p['net_profit'],'-7');self.assertEqual(p['operating_cash_flow'],'-9');self.assertEqual(p['cost_of_goods_sold'],'20');self.assertEqual(p['deferred_tax_expense'],'-5');self.assertEqual(v['cost_of_goods_sold'],'-20')
 def test_missing_fields_remain_missing(self):
  p,changes=hypothesis(dict(cost_of_goods_sold='-20'))
  self.assertNotIn('associate_profit',p);self.assertNotIn('deferred_tax_expense',p)
 def test_explicit_deferred_tax_income_and_expense_flip_is_only_a_hypothesis(self):
  p,_=hypothesis(dict(cost_of_goods_sold='-20',deferred_tax_expense='-5',revenue_deductions='-3'))
  self.assertEqual(p['deferred_tax_expense'],'5');self.assertEqual(p['revenue_deductions'],'3')

if __name__=='__main__':unittest.main()
