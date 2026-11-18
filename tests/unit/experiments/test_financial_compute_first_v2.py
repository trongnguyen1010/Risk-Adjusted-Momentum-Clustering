import unittest
from delta_t1.experiments.financial_compute_first_v2 import apply_cohort_metadata, metric_row, summarize_symbols
from delta_t1.experiments.financial_cafef_pilot import FAMILIES


class CohortMetadataTests(unittest.TestCase):
    def setUp(self):
        self.cohorts = [dict(id='ACV-2025', symbol='ACV', year=2025,
            input_scope='CONSOLIDATED', variant_clearance='EXISTING_NONFINANCIAL_REFERENCE_VARIANTS')]
        self.rows = [dict(symbol='ACV', year=2025, cohort_id='ACV-2025', family=f,
            value=str(i + 1)) for i, f in enumerate(FAMILIES)]
        for row in self.rows[3:]:
            row['input_scope'] = 'CONSOLIDATED'

    def test_explicit_cohort_scope_groups_six_families_without_changing_values_or_gates(self):
        enriched = apply_cohort_metadata(self.rows, self.cohorts)
        self.assertEqual([r['value'] for r in enriched], [r['value'] for r in self.rows])
        normalized = [metric_row(r, 'ACV', 'evidence') for r in enriched]
        self.assertTrue(summarize_symbols(['ACV'], normalized)[0]['has_six_family_reference_cohort'])
        self.assertTrue(all(not r['strict_pit_ready'] and not r['financial_features_allowed'] for r in normalized))
        self.assertNotIn('input_scope', self.rows[0])

    def test_reject_scope_period_and_clearance_conflicts(self):
        for change in [dict(input_scope='SEPARATE'), dict(year=2024), dict(symbol='GAS')]:
            rows = [dict(self.rows[0], **change)]
            with self.assertRaises(ValueError):
                apply_cohort_metadata(rows, self.cohorts)
        with self.assertRaises(ValueError):
            apply_cohort_metadata(self.rows, [dict(self.cohorts[0], variant_clearance='UNKNOWN')])

    def test_declared_variant_is_preserved(self):
        rows = [dict(self.rows[0], variant='EXACT_REVIEWED_VARIANT')]
        self.assertEqual(apply_cohort_metadata(rows, self.cohorts)[0]['variant'], 'EXACT_REVIEWED_VARIANT')
