import unittest
from delta_t1.experiments.financial_source_completion import select_original


class SourceSelectionTests(unittest.TestCase):
    def inputs(self):
        f=dict(symbol='FPT',year=2025,item='total_assets',value=100,unit='VND',pdf_sha256='original',
            statement_scope='CONSOLIDATED',accounting_framework='VAS',period_end='2025-12-31',
            period_start=None,period_semantics='INSTANT',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')
        p=dict(symbol='FPT',year=2025,pdf_sha256='original',publication_date='2026-03-19',exchange='HOSE',
            validation_status='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED',precision='DATE_ONLY')
        c=[dict(exchange='HOSE',trade_date=d,is_open=True) for d in ['2026-03-18','2026-03-19','2026-03-20']]
        return f,p,c
    def test_no_same_day_or_future_acceptance(self):
        f,p,c=self.inputs()
        self.assertIsNone(select_original([f],[p],c,2025,'total_assets','2026-03-19'))
        self.assertEqual(select_original([f],[p],c,2025,'total_assets','2026-03-20')['fact']['value'],100)
    def test_original_pdf_not_latest_or_wrong_units(self):
        f,p,c=self.inputs();revised=dict(f,pdf_sha256='later',value=999)
        self.assertEqual(select_original([f,revised],[p],c,2025,'total_assets','2026-03-20')['fact']['value'],100)
        self.assertIsNone(select_original([dict(f,unit='SHARES')],[p],c,2025,'total_assets','2026-03-20'))
    def test_quarter_period_does_not_enter_annual(self):
        f,p,c=self.inputs();f['period_end']='2025-06-30'
        self.assertIsNone(select_original([f],[p],c,2025,'total_assets','2026-03-20'))
    def test_conflicts_and_unreviewed_dates_fail_closed(self):
        f,p,c=self.inputs()
        with self.assertRaises(ValueError):select_original([f,dict(f,value=101)],[p],c,2025,'total_assets','2026-03-20')
        p['validation_status']='PENDING'
        with self.assertRaises(ValueError):select_original([f],[p],c,2025,'total_assets','2026-03-20')
