import copy
import unittest
from delta_t1.experiments.financial_quarterly_review import check_quarter_v2, period_eps, publication_status


class QuarterlyReviewTests(unittest.TestCase):
    def review(self):
        facts=[]
        for interval,start,values in [('QUARTER_STANDALONE','2015-07-01',{'net_revenue':100,'cost_of_goods_sold':60,'gross_profit':40,'eps_adjusted_earnings_numerator':30,'weighted_average_basic_shares':10}),
                                      ('YTD','2015-01-01',{'net_revenue':270,'cost_of_goods_sold':170,'gross_profit':100,'operating_cash_flow':50})]:
            for field,value in values.items():
                facts.append(dict(id=interval+':'+field,symbol='MWG',year=2015,quarter=3,interval=interval,
                                  period_start=start,period_end='2015-09-30',field=field,value=str(value),
                                  unit='SHARES' if field=='weighted_average_basic_shares' else 'VND',
                                  scope='CONSOLIDATED',framework='VAS',review_status='REVIEWED_REFERENCE_ONLY',
                                  provenance={'pdf_sha256':'exact-vintage'}))
        return dict(version='financial-quarter-reference-review-v2',fiscal_basis='CALENDAR_YEAR',facts=facts)

    def test_exact_period_eps_not_annualized_and_cfo_not_reassigned(self):
        review=self.review();rows=period_eps(review)
        quarter=next(r for r in rows if r['interval']=='QUARTER_STANDALONE')
        ytd=next(r for r in rows if r['interval']=='YTD')
        self.assertEqual(quarter['value'],'3')
        self.assertEqual(quarter['months'],3)
        self.assertIsNone(ytd['value'])
        self.assertEqual(review['facts'][-1]['interval'],'YTD')
        self.assertFalse(quarter['annualized'])
        self.assertFalse(quarter['pit_ready'])
        self.assertIsNone(quarter['diluted_eps'])

    def test_ytd_cannot_be_relabeled_quarter(self):
        review=self.review();review['facts'][-1]['interval']='QUARTER_STANDALONE'
        with self.assertRaisesRegex(ValueError,'period'):check_quarter_v2(review)

    def test_accounting_errors_are_not_tolerated(self):
        review=self.review();review['facts'][0]['value']='101'
        with self.assertRaisesRegex(ValueError,'accounting'):check_quarter_v2(review)

    def test_duplicate_and_cross_vintage_review_rejected(self):
        review=self.review();review['facts'].append(copy.deepcopy(review['facts'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):check_quarter_v2(review)
        review=self.review();review['facts'][0]['provenance']['pdf_sha256']='new-restatement'
        with self.assertRaisesRegex(ValueError,'vintages'):check_quarter_v2(review)

    def test_catalogue_before_exact_document_creation_is_not_pit(self):
        self.assertEqual(publication_status(dict(catalogue_date='2015-10-30',document_creation_date='2015-11-06')),
                         'DOCUMENT_POSTDATES_CATALOGUE_REQUIRES_VERSION_EVIDENCE')
        self.assertEqual(publication_status(dict(catalogue_date='2015-11-07',document_creation_date='2015-11-06')),
                         'EXACT_DOCUMENT_PUBLICATION_NOT_ACCEPTED')


if __name__=='__main__':unittest.main()
