import copy
import unittest

from delta_t1.experiments.financial_critical_review import compare


class CriticalReviewTests(unittest.TestCase):
    def setUp(self):
        self.payload = {'value': {'templace': [{'code': 'HDKD', 'data': [
            {'code': 'HDKD_7', 'name': 'Interest expense'}]}], 'data': [
            {'code': 'HDKD', 'data': [{'symbol': 'SHS', 'year': 2025, 'quater': 0,
             'type': 'K', 'data': [{'code': 'HDKD_1', 'value': 680},
                                  {'code': 'HDKD_7', 'value': 0}]}]}]}}
        self.case = dict(id='interest', symbol='SHS', year=2025, quarter=0, mode='NAM',
                         provider_type='K', group='HDKD', raw_code='HDKD_7',
                         expected_api_label='Interest expense', source_report_year=2025,
                         field='interest_expense', pdf_value='280', pdf_page=17,
                         row_label='06 Interest expense')

    def test_named_zero_conflict_does_not_promote_zero_or_override(self):
        r = compare(self.payload, self.case)
        self.assertEqual(r['status'], 'PDF_NONZERO_API_ZERO')
        self.assertFalse(r['accepted'])
        self.assertFalse(r['automatic_override'])

    def test_nonzero_orphan_cannot_become_cfo(self):
        c = dict(self.case, raw_code='HDKD_1', expected_api_label=None, field=None, pdf_value=None)
        self.assertEqual(compare(self.payload, c)['status'], 'UNRESOLVED_NONZERO_UNLABELLED')
        with self.assertRaises(ValueError):
            compare(self.payload, dict(c, field='operating_cash_flow', pdf_value='680'))

    def test_other_report_year_is_rejected(self):
        with self.assertRaises(ValueError):
            compare(self.payload, dict(self.case, source_report_year=2024))

    def test_quarter_is_not_substituted_for_annual(self):
        with self.assertRaises(ValueError):
            compare(self.payload, dict(self.case, quarter=4, mode='QUY'))

    def test_duplicate_cell_is_ambiguous(self):
        p = copy.deepcopy(self.payload)
        p['value']['data'][0]['data'][0]['data'].append({'code': 'HDKD_7', 'value': 0})
        with self.assertRaises(ValueError):
            compare(p, self.case)

    def test_matching_value_still_is_reference_diagnostic(self):
        r = compare(self.payload, dict(self.case, pdf_value='0'))
        self.assertEqual(r['status'], 'RAW_NUMERIC_MATCH_REFERENCE_ONLY')
        self.assertFalse(r['unit_acceptance'])
        self.assertFalse(r['accepted'])


if __name__ == '__main__':
    unittest.main()
