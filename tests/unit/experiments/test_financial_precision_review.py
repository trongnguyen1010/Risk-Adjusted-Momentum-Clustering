import json
import unittest
from pathlib import Path
from delta_t1.experiments.financial_precision_review import residual_decision, evaluate, annual_filename_key, validate
from delta_t1.features.financial_exploratory import calculate_core


class PrecisionReviewTests(unittest.TestCase):
    def test_both_caps_required_no_percent_tolerance(self):
        self.assertEqual(residual_decision('1', ['1000000000']), 'SMALL_RAW_RESIDUAL_REFERENCE_ONLY')
        self.assertEqual(residual_decision('-1', ['-1000000000']), 'SMALL_RAW_RESIDUAL_REFERENCE_ONLY')
        for difference, terms in [('2', ['1000000000000']), ('1', ['100']), ('0.1', ['1'])]:
            self.assertTrue(residual_decision(difference, terms).startswith('HELD'))
        self.assertEqual(residual_decision('0', ['0']), 'EXACT_EQUALITY')

    def test_missing_invalid_boolean_nonfinite_never_rescued(self):
        for difference, terms in [(None, ['1000000000']), ('NaN', ['1000000000']),
                                   ('1', [True]), ('1', ['Infinity']), ('1', [])]:
            self.assertTrue(residual_decision(difference, terms).startswith('HELD'))
        self.assertFalse(evaluate({})['quality_gate'])

    def values(self):
        return dict(total_assets='10000000000', total_capital='10000000000',
            total_liabilities='4000000000', total_equity='6000000000',
            current_assets='7000000000', noncurrent_assets='3000000000',
            current_liabilities='3000000000', noncurrent_liabilities='1000000000',
            net_revenue='10000000000', cost_of_goods_sold='6000000000', gross_profit='4000000000',
            profit_before_tax='3000000000', reported_operating_profit='3000000000', other_profit='0',
            net_profit='2400000000', current_tax_expense='600000000', deferred_tax_expense='0',
            finance_income='0', finance_expense='0', associate_profit='0', selling_expense='500000000',
            administrative_expense='500000000', operating_cash_flow='-1000000000')

    def test_displacement_missing_significant_difference_still_block(self):
        v = self.values(); self.assertTrue(evaluate(v)['quality_gate'])
        self.assertFalse(evaluate(v, displaced=True)['quality_gate'])
        v['total_assets'] = '10000000001'
        self.assertTrue(evaluate(v)['quality_gate'])
        self.assertFalse(evaluate(v, absolute_cap='0', relative_cap='0')['quality_gate'])
        v['total_assets'] = '10000000002'; self.assertFalse(evaluate(v)['quality_gate'])
        del v['total_assets']; self.assertFalse(evaluate(v)['quality_gate'])

    def test_precision_does_not_override_core_feature_validity(self):
        v = self.values(); self.assertIsNotNone(calculate_core(v)['values'])
        v['current_liabilities'] = '0'; self.assertIsNone(calculate_core(v)['values'])
        del v['operating_cash_flow']; self.assertEqual(calculate_core(v)['status'], 'MISSING_INPUTS')

    def test_optional_missing_allowed_optional_observed_difference_held(self):
        v = self.values(); self.assertTrue(evaluate(v)['quality_gate'])
        v.update(other_income='100', other_expense='98')
        self.assertFalse(evaluate(v)['quality_gate'])

    def test_cached_filename_only_hint_not_quarterly_document(self):
        self.assertEqual(annual_filename_key('VNM-2025-q0-abcdef.pdf'), ('VNM', 2025))
        self.assertEqual(annual_filename_key('01-PVS-2019.pdf'), ('PVS', 2019))
        self.assertEqual(annual_filename_key('GMD-FY2015.pdf'), ('GMD', 2015))
        self.assertIsNone(annual_filename_key('VNM-2025-q2-abcdef.pdf'))
        self.assertIsNone(annual_filename_key('MWG-Q3-2015.pdf'))
        self.assertIsNone(annual_filename_key('anonymous.pdf'))

    def test_contract_cannot_enable_transport_or_promotion(self):
        root = Path(__file__).resolve().parents[3]
        c = json.loads((root/'configs/experiments/financial_precision_review_v1.json').read_bytes())
        validate(c)
        for key in ['network_allowed', 'pdf_download_allowed', 'ocr_allowed', 'research_promotion_allowed']:
            changed = dict(c); changed[key] = True
            with self.assertRaises(ValueError): validate(changed)
        changed = dict(c, absolute_raw_cap='2')
        with self.assertRaises(ValueError): validate(changed)
