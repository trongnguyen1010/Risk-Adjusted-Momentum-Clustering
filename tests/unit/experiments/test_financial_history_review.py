import unittest
from delta_t1.experiments.financial_history_review import compute_review, check_quarter

class HistoryReviewTests(unittest.TestCase):
    def fact(self,field,value):return dict(id=field,symbol='GMD',year=2015,field=field,value=str(value),unit='VND',scope='CONSOLIDATED',framework='VAS',review_status='REVIEWED_REFERENCE_ONLY',pit_ready=False,available_at=None)
    def test_missing_inputs_not_imputed(self):
        result=compute_review([self.fact('total_assets',100)])
        self.assertEqual(result['new_reference_metrics'],0)
        self.assertTrue(result['missing_inputs'])
    def test_accounting_mismatch_blocks_compute(self):
        with self.assertRaisesRegex(ValueError,'accounting difference'):
            compute_review([self.fact('total_assets',100),self.fact('total_liabilities',30),self.fact('total_equity',80)])
    def test_wrong_scope_or_unit_blocked(self):
        for extra in [dict(unit='BILLION_VND'),dict(scope='SEPARATE'),dict(pit_ready=True)]:
            with self.assertRaises(ValueError):compute_review([dict(self.fact('total_assets',100),**extra)])
    def test_duplicate_facts_not_selected_by_order(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):compute_review([self.fact('total_assets',100)]*2)
    def test_h1_cfo_does_not_become_standalone_quarter(self):
        facts=[]
        rows={'INSTANT':{'total_assets':100,'total_liabilities':30,'total_equity':70,'current_assets':40,'noncurrent_assets':60},
              'Q2_STANDALONE':{'net_revenue':100,'cost_of_goods_sold':70,'gross_profit':30},
              'H1_YTD':{'net_revenue':180,'cost_of_goods_sold':120,'gross_profit':60,'operating_cash_flow':50}}
        for interval,values in rows.items():
            facts.extend(dict(self.fact(f,v),interval=interval) for f,v in values.items())
        self.assertEqual(len(check_quarter(dict(facts=facts,quarter_cfo=None))),4)
        with self.assertRaisesRegex(ValueError,'H1-to-quarter'):
            check_quarter(dict(facts=facts,quarter_cfo=50))
