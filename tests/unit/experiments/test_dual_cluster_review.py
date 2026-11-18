import unittest

from delta_t1.experiments.dual_cluster_review import reference_join, separation_drivers


class DualReviewTests(unittest.TestCase):
    def test_separate_namespaces_union_and_ex_post_scope(self):
        m = [dict(snapshot_date='2025-12-31', ticker='A', security_id='M:A', cluster_label='0'),
             dict(snapshot_date='2025-12-31', ticker='B', security_id='M:B', cluster_label='1')]
        f = [dict(year='2025', symbol='A', registry_id='F:A', cluster_id='2'),
             dict(year='2025', symbol='C', registry_id='F:C', cluster_id='0')]
        got = reference_join(m, f, ['2025-12-31'])
        self.assertEqual(['BOTH', 'MARKET_ONLY', 'FINANCIAL_ONLY'], [r['coverage'] for r in got])
        self.assertEqual(('0', '2'), (got[0]['market_cluster_id'], got[0]['financial_cluster_id']))
        self.assertTrue(all(not r['research_ready'] and 'NOT_PIT' in r['join_scope'] for r in got))

    def test_ambiguous_current_identity_is_rejected(self):
        m = [dict(snapshot_date='2025-12-31', ticker='A', security_id=s, cluster_label='0') for s in ['M:1', 'M:2']]
        with self.assertRaisesRegex(ValueError, 'duplicate key'):
            reference_join(m, [], ['2025-12-31'])

    def test_separation_driver_uses_actual_model_scale(self):
        p = [dict(size=1, means=dict(a=0, b=0)), dict(size=1, means=dict(a=10, b=1))]
        got = separation_drivers(p, dict(a={'scale': 10}, b={'scale': 1}), ['a', 'b'])
        self.assertAlmostEqual(.5, got['a'])
        self.assertAlmostEqual(.5, got['b'])
