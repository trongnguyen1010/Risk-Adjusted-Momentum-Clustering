import unittest

from app.assessment import VERDICT_STATUS, map_assessment_response
from delta_t1.product.assessment_repository import AssessmentRepository


class TestAssessmentResponseMapper(unittest.TestCase):
    def test_mapper_preserves_release_content_and_refreshes_request_time(self):
        lookup = AssessmentRepository.from_config().lookup('A32')
        first = map_assessment_response(lookup, request_time='2026-11-18T00:00:00+00:00')
        second = map_assessment_response(lookup, request_time='2026-11-18T00:01:00+00:00')
        self.assertEqual(first.ticker, 'A32')
        self.assertEqual(first.as_of, '2026-01-02')
        self.assertEqual(first.assessment_context, 'SIMULATED_AS_OF')
        self.assertEqual(first.assessment_status, VERDICT_STATUS[lookup.assessment['verdict']])
        self.assertEqual(first.rationale, lookup.assessment['rationale'])
        self.assertNotEqual(first.request_time, second.request_time)
        self.assertEqual(first.features[0].value, second.features[0].value)


if __name__ == '__main__':
    unittest.main()
