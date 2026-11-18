import tempfile
import unittest
from pathlib import Path

from delta_t1.product.assessment_repository import AssessmentArtifactUnavailable, AssessmentRepository


class TestAssessmentRepository(unittest.TestCase):
    def test_verified_repository_reads_pinned_artifact_only(self):
        repository = AssessmentRepository.from_config()
        result = repository.lookup('A32')
        self.assertEqual(result.status, 'READY')
        self.assertEqual(result.assessment['ticker'], 'A32')

    def test_unpublished_artifact_is_distinct_from_unknown_ticker(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(AssessmentArtifactUnavailable, 'CONFIG_NOT_FOUND'):
                AssessmentRepository.from_config(repository_root=Path(temporary_directory))
        repository = AssessmentRepository.from_config()
        result = repository.lookup('ZZZ999')
        self.assertEqual(result.status, 'NOT_FOUND')
        self.assertEqual(result.reason, 'TICKER_NOT_FOUND')


if __name__ == '__main__':
    unittest.main()
