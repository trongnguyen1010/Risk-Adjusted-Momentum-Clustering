import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from delta_t1.product.assessment_repository import _load_assessments, load_assessment_payload


class TestAssessmentPayloadReader(unittest.TestCase):
    def test_real_release_loads_without_recomputing_nullable_values(self):
        result = load_assessment_payload()
        self.assertTrue(result.ready, result.reason)
        self.assertEqual(len(result.payload.assessments), 1428)
        self.assertEqual(set(result.payload.coverage), {
            'roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover', 'revenue_growth', 'cfo_to_ni',
            'mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21', 'downside_vol_63',
        })
        self.assertIsNone(result.payload.assessments['AAM']['financial_features']['cfo_to_ni'])

    def test_invalid_verdict_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / 'assessments.jsonl'
            path.write_text(json.dumps({'ticker': 'AAA', 'as_of': '2026-01-02', 'verdict': 'BUY_NOW', 'financial_features': {}, 'market_features': {}, 'peer_comparisons': {}}), encoding='utf-8')
            with self.assertRaises(ValueError):
                _load_assessments(path, SimpleNamespace(as_of='2026-01-02'))

    def test_missing_feature_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / 'assessments.jsonl'
            path.write_text(json.dumps({'ticker': 'AAA', 'as_of': '2026-01-02', 'verdict': 'MONITOR', 'financial_features': {}, 'market_features': {}, 'peer_comparisons': {}}), encoding='utf-8')
            with self.assertRaises(ValueError):
                _load_assessments(path, SimpleNamespace(as_of='2026-01-02'))


if __name__ == '__main__':
    unittest.main()
