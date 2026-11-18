import unittest

from pydantic import ValidationError

from app.schemas import AssessmentQuery, AssessmentResponse, FEATURE_IDS


def payload():
    features = [
        {
            'feature_id': feature_id,
            'category': 'FINANCIAL' if feature_id in {'roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio', 'asset_turnover', 'revenue_growth', 'cfo_to_ni'} else 'MARKET',
            'value': None if feature_id == 'cfo_to_ni' else 0.1,
            'status': 'OK', 'unit': 'ratio', 'period': '2024', 'usable_from_date': '2025-03-11',
            'peer': None, 'evidence_ref': None,
        }
        for feature_id in FEATURE_IDS
    ]
    return {
        'ticker': 'A32', 'request_time': '2026-11-18T00:00:00+00:00', 'as_of': '2026-01-02',
        'required_price_session': '2025-12-31', 'evidence_cutoff_at': None,
        'assessment_context': 'SIMULATED_AS_OF', 'availability_status': 'READY',
        'assessment_status': 'RESEARCH_FAVORABLE', 'rationale': 'Fixture only.',
        'market_cluster': {'id': 0, 'model_version': 'A-v4', 'date_or_fy': '2025-12-31', 'profile': 'Market', 'quality_flags': [], 'source_revision': 'a-v4'},
        'financial_cluster': {'id': 0, 'model_version': 'B-PIT-v1', 'date_or_fy': '2024', 'profile': 'Financial', 'quality_flags': [], 'source_revision': 'b-pit-v1'},
        'features': features, 'drivers': [], 'risks': [], 'counter_evidence': [], 'history': [],
        'references': {'release_revision': 'assessment-v1-run01-r1', 'policy_revision': 'D-ASS-01', 'manifest_sha256': 'a' * 64, 'deterministic_content_sha256': 'b' * 64, 'source_hashes': {'availability_csv_sha256': 'c' * 64}},
        'scope': 'AS_OF_ASSESSMENT_ONLY',
    }


class TestAssessmentResponseModels(unittest.TestCase):
    def test_valid_fixture_preserves_nullable_feature_value(self):
        response = AssessmentResponse.model_validate(payload())
        feature = next(item for item in response.features if item.feature_id == 'cfo_to_ni')
        self.assertIsNone(feature.value)
        self.assertEqual(len(response.features), 18)

    def test_invalid_assessment_status_is_rejected(self):
        invalid = payload()
        invalid['assessment_status'] = 'BUY_NOW'
        with self.assertRaises(ValidationError):
            AssessmentResponse.model_validate(invalid)

    def test_missing_required_response_field_is_rejected(self):
        invalid = payload()
        del invalid['references']
        with self.assertRaises(ValidationError):
            AssessmentResponse.model_validate(invalid)

    def test_public_query_forbids_arbitrary_as_of(self):
        with self.assertRaises(ValidationError):
            AssessmentQuery.model_validate({'lookback_years': 10, 'as_of': '2020-01-01'})


if __name__ == '__main__':
    unittest.main()
