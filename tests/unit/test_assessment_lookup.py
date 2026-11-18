import unittest

from delta_t1.product.assessment_repository import lookup_assessment


class TestAssessmentLookup(unittest.TestCase):
    def test_known_ticker_uses_pinned_simulated_release_context(self):
        result = lookup_assessment(' a32 ', assessment_context='SIMULATED_AS_OF', as_of='2026-01-02', required_price_session='2025-12-31', release_revision='assessment-v1-run01-20261116')
        self.assertEqual(result.status, 'READY')
        self.assertEqual(result.assessment['ticker'], 'A32')
        self.assertEqual(result.release.assessment_context, 'SIMULATED_AS_OF')

    def test_existing_ticker_with_missing_evidence_is_not_not_found(self):
        result = lookup_assessment('AAM')
        self.assertEqual(result.status, 'INSUFFICIENT_EVIDENCE')
        self.assertIsNotNone(result.assessment)

    def test_unknown_ticker_is_not_found(self):
        result = lookup_assessment('ZZZ999')
        self.assertEqual(result.status, 'NOT_FOUND')
        self.assertIsNone(result.assessment)

    def test_release_context_cannot_be_overridden(self):
        result = lookup_assessment('A32', assessment_context='CURRENT_AS_OF')
        self.assertEqual(result.status, 'NOT_READY')
        self.assertEqual(result.reason, 'RELEASE_CONTEXT_MISMATCH')

    def test_invalid_ticker_does_not_be_treated_as_artifact_failure(self):
        result = lookup_assessment('../A32')
        self.assertEqual(result.status, 'NOT_FOUND')
        self.assertEqual(result.reason, 'TICKER_INVALID')


if __name__ == '__main__':
    unittest.main()
