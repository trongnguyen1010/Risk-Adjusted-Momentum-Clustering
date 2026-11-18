import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from delta_t1.product.assessment_repository import AssessmentArtifactUnavailable, AssessmentRepository


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

    def test_revision_mismatch_and_invalid_ticker_are_rejected(self):
        app=create_app(repository=FakeRepository(),assessment_repository=AssessmentRepository.from_config())
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/v2/stocks/A32/assessment?revision=wrong').status_code,409)
            self.assertEqual(client.get('/api/v2/stocks/%40%40%40/assessment').status_code,422)

    def test_unavailable_release_returns_503(self):
        app=create_app(repository=FakeRepository())
        with patch('app.main.AssessmentRepository.from_config',side_effect=AssessmentArtifactUnavailable('CONFIG_NOT_FOUND')):
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/v2/stocks/A32/assessment').status_code,503)


if __name__=='__main__':unittest.main()
