import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from delta_t1.product.assessment_repository import AssessmentRepository


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
            insufficient = client.get('/api/v2/stocks/AAM/assessment')
            revision = client.get('/api/v2/stocks/A32/assessment?revision=wrong')
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json()['ticker'], 'A32')
        self.assertEqual(insufficient.status_code, 200)
        self.assertEqual(insufficient.json()['assessment_status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(revision.status_code, 409)


if __name__ == '__main__':
    unittest.main()
