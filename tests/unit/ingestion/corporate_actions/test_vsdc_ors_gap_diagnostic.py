from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.ingestion.corporate_actions import vsdc_ors_gap_diagnostic as diagnostic
from tests.unit.ingestion.corporate_actions import test_vsdc_five_query4s_pilot as fixture


class DiagnosticTests(unittest.TestCase):
    def invoke(self, root, *, empty_fifth=False, dry_run=False):
        project = Path(root)
        review = project / diagnostic.REVIEW
        review.mkdir(parents=True)
        collector = diagnostic.collector
        collector.write(review / 'manifest.json', {'files': {}})
        baseline = {'reported': 85, 'verified_article_ids': [str(i) for i in range(100001, 100081)]}
        clock = fixture.fixture.old.Clock()

        class Driver(fixture.Driver):
            def respond(self, number):
                response = super().respond(number)
                if empty_fifth and number == 5:
                    self.fragment = '<div id="divGlSearchArticles"></div>'
                    response.body.return_value = b' ' * 33
                return response

        state = project / 'run' / 'state'
        with (patch.object(diagnostic, 'load_inputs', return_value=({'ors': baseline}, set(), set(), {})),
                patch.object(collector, 'runtime', return_value={}),
                patch.object(collector.mbs.old, 'readiness', return_value={'ready': True}),
                patch.object(fixture.p, 'TICKERS', ('ORS',)),
                patch.object(fixture.p, 'EXPECTED_ROWS', {'ORS': 85})):
            result = diagnostic.run(project, state, dry_run=dry_run, clock=clock.now,
                driver_factory=lambda config, guard: Driver(config, guard, clock))
        return result, state

    def test_complete_query_compares_ids_and_seals_without_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, state = self.invoke(tmp)
            self.assertEqual(diagnostic.REVIEW_COMPLETE, result['status'])
            self.assertEqual(5, result['business_requests'])
            self.assertEqual(80, result['baseline_ids_seen'])
            self.assertEqual(5, len(result['ids_not_in_baseline']))
            self.assertTrue(result['same_count_gap_closed'])
            self.assertTrue(result['manual_offline_review_pending'])
            self.assertTrue(diagnostic.package(state).is_file())

    def test_empty_fifth_page_preserves_verified_prefix_and_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, state = self.invoke(tmp, empty_fifth=True)
            self.assertEqual(diagnostic.REVIEW_PARTIAL, result['status'])
            self.assertEqual(5, result['business_requests'])
            self.assertEqual(80, result['observed_distinct_now'])
            self.assertFalse(result['same_count_gap_closed'])
            evidence = diagnostic.collector.read(state / 'query/ORS/diagnostics/page5/body_evidence.json')
            self.assertEqual(33, evidence['bytes'])
            self.assertTrue(diagnostic.package(state).is_file())

    def test_preflight_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, state = self.invoke(tmp, dry_run=True)
            self.assertEqual('OFFLINE_CHECK_PASS', result['status'])
            self.assertEqual(0, result['source_requests'])
            self.assertFalse(state.exists())
