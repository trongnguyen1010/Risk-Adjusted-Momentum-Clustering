import unittest
from delta_t1.experiments.financial_scale_review import evaluate


class ScaleReviewTests(unittest.TestCase):
    def document(self):
        vals=dict(current_assets=50,total_assets=100,total_liabilities=60,current_liabilities=30,
                  total_equity=40,retained_earnings=10,profit_before_tax=10,interest_expense=2,
                  eps_numerator=120,weighted_basic_shares=10,vendor_basic_eps=12)
        return dict(symbol='NEW',year=2025,scope='CONSOLIDATED',framework='VAS',unit='VND',months=12,
            period_start='2025-01-01',period_end='2025-12-31',company_type='Regular',exchange='HNX',
            pdf_sha256='exact',ebit_basis='EBT_PLUS_DISCLOSED_EXPENSED_INTEREST_EXCLUDING_ISSUANCE_FEES',
            facts=[dict(field=k,value=str(v),locator='reviewed page/row',review_status='VISUALLY_VERIFIED_REFERENCE_ONLY') for k,v in vals.items()])

    def pub(self):return dict(publication_date='2026-03-05',pdf_sha256='exact',precision='DATE_ONLY',validation_status='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED')

    def calendar(self):return [dict(exchange='HNX',trade_date=d,is_open=True) for d in ['2026-03-05','2026-03-06']]

    def test_math_without_publication_is_reference_only(self):
        r=evaluate(self.document(),None,self.calendar(),'2026-03-06',24)
        self.assertEqual(r['disclosed_basic_eps_reference']['value'],'12')
        self.assertEqual(r['pe_annual_arithmetic'],'2');self.assertIsNone(r['production_value'])
        self.assertFalse(r['date_eligible_at_snapshot']);self.assertFalse(r['financial_cluster_allowed'])
        self.assertIsNone(r['pe_ttm']);self.assertIsNone(r['m_full'])

    def test_date_only_does_not_release_on_publication_day(self):
        for day,eligible in [('2026-03-05',False),('2026-03-06',True)]:
            r=evaluate(self.document(),self.pub(),self.calendar(),day)
            self.assertEqual(r['date_eligible_at_snapshot'],eligible);self.assertIsNone(r['available_at'])
            self.assertFalse(r['financial_features_allowed'])

    def test_wrong_pdf_and_inferred_precision_rejected(self):
        for k,v in [('pdf_sha256','other'),('precision','TIMESTAMP_INFERRED')]:
            p=self.pub();p[k]=v
            with self.assertRaises(ValueError):evaluate(self.document(),p,self.calendar(),'2026-03-06')

    def test_balance_and_eps_rounding_fail_separately(self):
        d=self.document();d['facts'][1]['value']='102';d['facts'][-1]['value']='13'
        r=evaluate(d,None,self.calendar(),'2026-03-06',24)
        self.assertIsNone(r['z_reference']);self.assertIsNone(r['disclosed_basic_eps_reference'])
        self.assertIsNone(r['pe_annual_arithmetic'])

    def test_sector_noncalendar_and_unreviewed_fact_rejected(self):
        for k,v in [('company_type','Securities'),('period_end','2025-06-30'),('unit','UNKNOWN')]:
            d=self.document();d[k]=v
            with self.assertRaises(ValueError):evaluate(d,None,self.calendar(),'2026-03-06')
        d=self.document();d['facts'][0]['review_status']='OCR_CANDIDATE_ONLY'
        with self.assertRaises(ValueError):evaluate(d,None,self.calendar(),'2026-03-06')

    def test_combined_fee_is_not_validated_ebit(self):
        d=self.document();d['ebit_basis']='INCOME_CODE23_UNREVIEWED_COMBINED_FEES'
        self.assertIsNone(evaluate(d,None,self.calendar(),'2026-03-06')['z_reference'])


if __name__=='__main__':unittest.main()
