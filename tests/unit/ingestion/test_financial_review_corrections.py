import unittest
from delta_t1.ingestion.financial_review_corrections import apply_review_corrections

class ReviewCorrectionTests(unittest.TestCase):
    def fact(self,value,pdf='original'):
        return dict(symbol='FPT',year=2024,item='operating_cash_flow',value=value,unit='VND',
            pdf_sha256=pdf,period_start='2024-01-01',period_end='2024-12-31',period_semantics='ANNUAL',
            statement_scope='CONSOLIDATED',accounting_framework='VAS',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')
    def review(self):
        return dict(financial_features_allowed=False,corrections=[dict(rule='EXACT_PDF_VISUAL_TRANSCRIPTION_CORRECTION',
            incorrect_value=11703377718868,replacement=self.fact(11703777188868))])
    def test_only_known_same_pdf_typo_excluded_and_raw_unchanged(self):
        facts=[self.fact(11703377718868),self.fact(11703377718868,'different-vintage'),self.fact(999)]
        corrected,excluded=apply_review_corrections(facts,self.review())
        self.assertEqual(len(excluded),1)
        self.assertEqual(facts[0]['value'],11703377718868)
        self.assertTrue(any(f['value']==999 for f in corrected))  # unknown conflict must survive
        self.assertTrue(any(f['pdf_sha256']=='different-vintage' for f in corrected))
    def test_idempotent_and_invalid_scope_rejected(self):
        facts,_=apply_review_corrections([self.fact(11703377718868)],self.review())
        again,excluded=apply_review_corrections(facts,self.review())
        self.assertEqual(facts,again);self.assertEqual(excluded,[])
        r=self.review();r['corrections'][0]['replacement']['unit']='SHARES'
        with self.assertRaises(ValueError):apply_review_corrections([],r)
