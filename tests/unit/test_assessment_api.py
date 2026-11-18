import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from delta_t1.product.assessment_repository import AssessmentRepository


class FakeRepository:
    meta={'version':'test','model_configs':{}}
    manifest={'database_sha256':'test'}


class TestAssessmentApi(unittest.TestCase):
    def test_endpoint_reads_pinned_assessment(self):
        app=create_app(repository=FakeRepository(),assessment_repository=AssessmentRepository.from_config())
        with TestClient(app) as client:
            response=client.get('/api/v2/stocks/A32/assessment')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['ticker'],'A32')
        self.assertEqual(response.json()['assessment_context'],'SIMULATED_AS_OF')

    def test_unknown_ticker_is_404(self):
        app=create_app(repository=FakeRepository(),assessment_repository=AssessmentRepository.from_config())
        with TestClient(app) as client:
            response=client.get('/api/v2/stocks/ZZZ999/assessment')
        self.assertEqual(response.status_code,404)


if __name__=='__main__':unittest.main()
