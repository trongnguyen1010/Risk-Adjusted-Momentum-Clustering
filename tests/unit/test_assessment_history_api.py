import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from delta_t1.product.assessment_repository import AssessmentRepository


class FakeRepository:
    meta = {'version': 'test', 'model_configs': {}}
    manifest = {'database_sha256': 'test'}


class TestAssessmentHistoryApi(unittest.TestCase):
    def setUp(self):
        self.app = create_app(repository=FakeRepository(), assessment_repository=AssessmentRepository.from_config())

    def test_lookback_only_changes_history_window(self):
        with TestClient(self.app) as client:
            five = client.get('/api/v2/stocks/A32/assessment?lookback_years=5').json()
            ten = client.get('/api/v2/stocks/A32/assessment?lookback_years=10').json()
        self.assertEqual(five['assessment_status'], ten['assessment_status'])
        self.assertEqual(five['rationale'], ten['rationale'])
        self.assertLessEqual(len(five['history']), len(ten['history']))
        self.assertTrue(all(int(row['period']) >= 2022 for row in five['history']))

    def test_invalid_lookback_is_rejected(self):
        with TestClient(self.app) as client:
            response = client.get('/api/v2/stocks/A32/assessment?lookback_years=7')
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
