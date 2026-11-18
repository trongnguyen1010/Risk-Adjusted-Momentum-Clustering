import copy
import unittest
from delta_t1.experiments.financial_period_date_view import build_date_view,monthly_decisions


class PeriodDateViewTests(unittest.TestCase):
    def setUp(self):
        self.policy=dict(precision='DATE_ONLY',timestamp_inference_allowed=False,financial_features_allowed=False,
                         availability_rule='FIRST_OBSERVED_EXCHANGE_SESSION_STRICTLY_AFTER_PUBLICATION_DATE',
                         owner_approval='existing owner approval',max_documents=40)
        self.calendar=[dict(exchange='HOSE',trade_date=d,is_open=True) for d in ['2024-07-18','2024-07-19','2024-07-22']]

    def slice(self,pdf='original',publication='2024-07-18',usable='2024-07-19',numerator='30'):
        facts=[]
        for field,value,unit in [('eps_adjusted_earnings_numerator',numerator,'VND'),('weighted_average_basic_shares','10','SHARES')]:
            facts.append(dict(id=pdf+':'+field,symbol='FPT',year=2023,quarter=2,interval='YTD',period_start='2023-01-01',
                              period_end='2023-06-30',field=field,value=value,unit=unit,scope='CONSOLIDATED',framework='VAS',
                              review_status='REVIEWED_REFERENCE_ONLY',provenance={'pdf_sha256':pdf}))
        return dict(review=dict(version='financial-quarter-reference-review-v2',fiscal_basis='CALENDAR_YEAR',facts=facts),
                    exchange='HOSE',publication=dict(symbol='FPT',pdf_sha256=pdf,publication_date=publication,usable_from_date=usable,
                         validation_status='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED',precision='DATE_ONLY',
                         date_pit_status='DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR'))

    def view(self,slices,decisions):return build_date_view(slices,self.calendar,self.policy,decisions)

    def test_comparative_restatement_not_visible_before_later_release(self):
        rows=self.view([self.slice()],['2023-07-31','2024-07-18','2024-07-19'])
        self.assertEqual([r['value'] for r in rows],[None,None,'3'])
        self.assertEqual([r['period_age_days'] for r in rows],[None,None,385])
        self.assertFalse(rows[2]['ttm']);self.assertFalse(rows[2]['strict_pit_ready'])
        self.assertEqual(rows[2]['months'],6)

    def test_latest_eligible_complete_vintage_selected(self):
        old=self.slice();new=self.slice('revision','2024-07-19','2024-07-22','40')
        rows=self.view([old,new],['2024-07-19','2024-07-22'])
        self.assertEqual([r['value'] for r in rows],['3','4'])
        self.assertEqual(rows[-1]['source_pdf_sha256'],['revision'])

    def test_same_date_conflicting_revisions_remain_null(self):
        rows=self.view([self.slice(),self.slice('different',numerator='40')],['2024-07-19'])
        self.assertIsNone(rows[0]['value'])
        self.assertEqual(rows[0]['result']['status'],'SAME_DATE_VINTAGE_VALUE_CONFLICT')

    def test_partial_new_vintage_does_not_mix_with_old_shares(self):
        old=self.slice();new=self.slice('revision','2024-07-19','2024-07-22','40')
        new['review']['facts']=new['review']['facts'][:1]
        rows=self.view([old,new],['2024-07-22'])
        self.assertIsNone(rows[0]['value'])
        self.assertEqual(rows[0]['result']['status'],'MIXED_OR_AMBIGUOUS_DOCUMENT_VINTAGE_INPUTS')

    def test_publication_must_match_exact_document(self):
        item=self.slice();item['publication']['pdf_sha256']='other'
        with self.assertRaisesRegex(ValueError,'different document'):self.view([item],['2024-07-19'])

    def test_unobserved_calendar_cannot_supply_next_session(self):
        with self.assertRaises(ValueError):build_date_view([self.slice()],[],self.policy,['2024-07-19'])

    def test_month_end_range_deterministic(self):
        dates=monthly_decisions(list(range(2016,2026)))
        self.assertEqual((len(dates),dates[0],dates[-1]),(120,'2016-01-31','2025-12-31'))
        self.assertIn('2016-02-29',dates)


if __name__=='__main__':unittest.main()
