import unittest
from delta_t1.experiments.financial_cached_fact_reconciliation import supplement_interest


class InterestEvidenceTests(unittest.TestCase):
    def test_only_exact_cashflow_match_supplements_reference(self):
        ref=dict(field='interest_expense',symbol='AAA',year=2025,pdf_sha256='doc',pdf_page=12,reviewed_value='10')
        fields=[dict(year=2025,field=f,provider_type='HK',value=v,observations=[]) for f,v in
                [('cashflow_interest_adjustment','10'),('finance_expense','10'),('interest_expense','90')]]
        evidence,matches=supplement_interest(ref,fields)
        self.assertEqual(len(evidence),2);self.assertEqual(len(matches),1)
        self.assertEqual(matches[0]['api_value'],'10')
        self.assertTrue(all('NOT_GLOBAL_ALIAS' in r['interpretation'] for r in evidence))

    def test_other_year_and_numeric_difference_never_fill_interest(self):
        ref=dict(field='interest_expense',symbol='AAA',year=2025,pdf_sha256='doc',pdf_page=12,reviewed_value='10')
        fields=[dict(year=y,field='cashflow_interest_adjustment',provider_type='HK',value=v,observations=[]) for y,v in [(2024,'10'),(2025,'11')]]
        self.assertEqual(supplement_interest(ref,fields)[1],[])
