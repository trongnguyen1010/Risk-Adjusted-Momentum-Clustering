import json
from pathlib import Path
import unittest

from delta_t1.experiments.financial_reviewed_batch import annual_values, legacy_rows, task_result, validate_fact


class ReviewedBatchTests(unittest.TestCase):
    def fact(self, field, value, year=2015, **extra):
        return dict(id=field+str(year), symbol='GMD', field=field, year=year,
                    value=str(value), unit='VND', scope='CONSOLIDATED', provenance={'pdf_sha256': 'vintage1'}, **extra)

    def test_bom_baseline_and_duplicate_keys(self):
        body='symbol,year,family,value\nGMD,2025,EPS,10\n'
        self.assertEqual(legacy_rows(body.encode('utf-8-sig'))[0]['symbol'], 'GMD')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            legacy_rows((body+'GMD,2025,EPS,20\n').encode())

    def test_reference_review_cannot_self_promote_pit_or_unknown_units(self):
        good=dict(self.fact('total_assets',100), review_status='REVIEWED_REFERENCE_ONLY',
                  scope='CONSOLIDATED',framework='VAS',pit_ready=False,available_at=None)
        validate_fact(good)
        for override in [dict(pit_ready=True),dict(available_at='2015-12-31'),
                         dict(scope='SEPARATE'),dict(unit='BILLION_VND'),dict(value=True),dict(value='NaN')]:
            with self.assertRaises(ValueError):validate_fact(dict(good,**override))

    def test_conflicts_are_excluded_in_both_orders(self):
        facts=[self.fact('parent_net_profit', 574), self.fact('parent_net_profit', 575)]
        for sequence in [facts, facts[::-1]]:
            values, ids, conflicts=annual_values(sequence, 'GMD', ['vintage1'])
            self.assertEqual(values, {})
            self.assertEqual(ids, {})
            self.assertEqual(len(conflicts), 1)

    def test_quarter_and_unapproved_vintage_never_fill_annual_inputs(self):
        rows=[self.fact('total_assets', 10, interval='INSTANT'),
              dict(self.fact('net_profit', 20), provenance={'pdf_sha256':'later-restatement'}),
              dict(self.fact('total_assets', 30), symbol='VNM')]
        self.assertEqual(annual_values(rows, 'GMD', ['vintage1'])[0], {})

    def test_missing_is_not_zero(self):
        result=task_result('GMD', 2015, 'F_SCORE', {}, {})
        self.assertIsNone(result['value'])
        self.assertIn({'field':'long_term_debt_including_current_portion','year':2014},result['missing_inputs'])

    def test_company_report_never_enters_consolidated_cohort(self):
        rows=[dict(self.fact('total_assets',100),scope='COMPANY_REPORTED')]
        self.assertEqual(annual_values(rows,'GMD',['vintage1'])[0],{})
        self.assertEqual(annual_values(rows,'GMD',['vintage1'],'COMPANY_REPORTED')[0],{('total_assets',2015):'100'})
        with self.assertRaisesRegex(ValueError,'basic EPS arithmetic'):
            task_result('GMD',2015,'Z_SCORE',{}, {},'COMPANY_REPORTED')

    def test_company_scope_requires_explicit_allowance(self):
        fact=dict(self.fact('total_assets',100),scope='COMPANY_REPORTED',framework='VAS',
                  review_status='REVIEWED_REFERENCE_ONLY',pit_ready=False,available_at=None)
        with self.assertRaises(ValueError):validate_fact(fact)
        validate_fact(fact,'COMPANY_REPORTED')

    def test_disclosed_eps_uses_exact_numerator_despite_parent_conflict(self):
        facts=[self.fact('parent_net_profit',574),self.fact('parent_net_profit',575),
               self.fact('eps_adjusted_earnings_numerator',382241762096),
               dict(self.fact('weighted_average_basic_shares',116843336),unit='SHARES')]
        values, ids, conflicts=annual_values(facts,'GMD',['vintage1'])
        result=task_result('GMD',2015,'EPS',values,ids)
        self.assertEqual(result['result']['rounded'],'3271')
        self.assertFalse(result['strict_pit_ready'])
        self.assertEqual(len(conflicts),1)

    def test_no_valuation_without_reviewed_price_basis(self):
        values={('eps_adjusted_earnings_numerator',2015):'100',('weighted_average_basic_shares',2015):'10',
                ('parent_common_equity',2015):'500',('common_shares',2015):'10'}
        for family in ['PE','PB']:
            self.assertIsNone(task_result('GMD',2015,family,values,{})['value'])

    def test_actual_note_bridge_does_not_import_original_eps(self):
        root=Path(__file__).resolve().parents[3]
        review=json.loads((root/'data/financial/history_document_supplement_v2/review/06-gmd2015-model-input-review.json').read_text(encoding='utf-8'))
        original=[f for f in review['facts'] if f['source_report_year']==2014]
        self.assertEqual({(f['field'],f['year']) for f in original},
                         {('total_assets',2013),('owned_tangible_ppe_depreciation',2014)})
        for f in review['facts']:
            if f['field']=='long_term_debt_including_current_portion':
                self.assertEqual(int(f['value']),sum(map(int,f['derivation']['components'])))
                self.assertTrue(f['derivation']['excluded_future_lease_interest'])


if __name__=='__main__':
    unittest.main()
