import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from delta_t1.product.assessment_repository import AssessmentRepository

EXPECTED_FEATURES = {
    'roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity',
    'current_ratio', 'asset_turnover', 'revenue_growth', 'cfo_to_ni',
    'mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126',
    'beta_126', 'liquidity_21', 'downside_vol_63',
}


class FakeRepository:
    meta = {'version': 'test', 'model_configs': {}}
    manifest = {'database_sha256': 'test'}


class TestAssessmentEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repository = AssessmentRepository.from_config()
        cls.app = create_app(repository=FakeRepository(), assessment_repository=cls.repository)

    def test_verified_artifact_endpoint_and_error_matrix(self):
        with TestClient(self.app) as client:
            ready = client.get('/api/v2/stocks/A32/assessment')
            matching_revision = client.get(
                '/api/v2/stocks/A32/assessment?revision='
                + self.repository.release.release_revision
            )
            insufficient = client.get('/api/v2/stocks/AAM/assessment')
            revision = client.get('/api/v2/stocks/A32/assessment?revision=wrong')
            missing = client.get('/api/v2/stocks/VCB/assessment')
            invalid_lookback = client.get('/api/v2/stocks/A32/assessment?lookback_years=7')
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json()['ticker'], 'A32')
        self.assertEqual(matching_revision.status_code, 200)
        self.assertEqual(
            matching_revision.json()['references']['release_revision'],
            self.repository.release.release_revision,
        )
        self.assertEqual(insufficient.status_code, 200)
        self.assertEqual(insufficient.json()['assessment_status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(revision.status_code, 409)
        # VCB is not present in this pinned release; keep the result explicit instead of
        # silently substituting another ticker's data.
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(invalid_lookback.status_code, 422)

    def test_lookback_changes_history_only_and_preserves_release_pins(self):
        with TestClient(self.app) as client:
            short = client.get('/api/v2/stocks/A32/assessment?lookback_years=5')
            long = client.get('/api/v2/stocks/A32/assessment?lookback_years=10')

        self.assertEqual(short.status_code, 200)
        self.assertEqual(long.status_code, 200)
        short_response, long_response = short.json(), long.json()
        for field in (
            'ticker', 'as_of', 'required_price_session', 'evidence_cutoff_at',
            'assessment_context', 'assessment_status', 'availability_status',
            'rationale', 'features', 'drivers', 'risks', 'counter_evidence',
            'references', 'scope',
        ):
            self.assertEqual(short_response[field], long_response[field], field)
        self.assertEqual(len(short_response['features']), 18)
        self.assertEqual(
            {feature['feature_id'] for feature in short_response['features']},
            EXPECTED_FEATURES,
        )
        self.assertEqual(
            short_response['references']['release_revision'],
            self.repository.release.release_revision,
        )
        self.assertTrue(all(int(point['period']) >= int(short_response['as_of'][:4]) - 4
                            for point in short_response['history']))
        self.assertTrue(all(int(point['period']) >= int(long_response['as_of'][:4]) - 9
                            for point in long_response['history']))


if __name__ == '__main__':
    unittest.main()
