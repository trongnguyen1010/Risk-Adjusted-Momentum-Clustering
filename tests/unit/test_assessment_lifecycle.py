import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from delta_t1.product.assessment_repository import AssessmentArtifactUnavailable


class FakeRepository:
    meta = {'version': 'test', 'model_configs': {}}
    manifest = {'database_sha256': 'test'}


class TestAssessmentLifecycle(unittest.TestCase):
    def test_injected_assessment_repository_is_stored_on_app_state(self):
        injected = object()
        app = create_app(repository=FakeRepository(), assessment_repository=injected)
        with TestClient(app):
            self.assertIs(app.state.assessment_repository, injected)

    def test_app_starts_without_assessment_artifact(self):
        app = create_app(repository=FakeRepository())
        with patch('app.main.AssessmentRepository.from_config', side_effect=AssessmentArtifactUnavailable('CONFIG_NOT_FOUND')):
            with TestClient(app):
                self.assertIsNone(app.state.assessment_repository)


if __name__ == '__main__':
    unittest.main()
