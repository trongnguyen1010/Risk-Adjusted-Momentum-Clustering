import unittest

import numpy as np

from delta_t1.product.cluster_story import describe_clusters

DEFS = {'mom_126': dict(label='Động lượng · 6 tháng', unit='percent'),
        'vol_63': dict(label='Biến động · 63 phiên', unit='ratio'),
        'liquidity_21': dict(label='Thanh khoản · 21 phiên', unit='vnd')}
FEATURES = ('mom_126', 'vol_63', 'liquidity_21')


def cohort():
    rng = np.random.default_rng(0)
    quiet = np.column_stack([rng.normal(0, .05, 60), rng.normal(.2, .03, 60), rng.normal(2e8, 2e7, 60)])
    rally = np.column_stack([rng.normal(.6, .1, 30), rng.normal(.6, .05, 30), rng.normal(2e8, 2e7, 30)])
    raw = np.vstack([quiet, rally])
    z = (raw - raw.mean(axis=0)) / raw.std(axis=0)
    return raw, z, np.r_[np.zeros(60, int), np.ones(30, int)]


class ClusterStoryTests(unittest.TestCase):
    def test_names_follow_the_strongest_differences(self):
        raw, z, labels = cohort()
        stories = describe_clusters(raw, z, labels, FEATURES, DEFS)
        self.assertEqual(stories[1]['name'], 'Đà tăng giá mạnh, biến động mạnh')
        self.assertTrue(stories[0]['name'].startswith('Giá đang giảm') or stories[0]['name'].startswith('Ít biến động'))
        self.assertIn('Động lượng · 6 tháng trung vị +', stories[1]['description'])
        self.assertIn('(chung:', stories[1]['description'])
        self.assertNotIn('Thanh khoản', stories[1]['name'])  # liquidity does not differ between the groups

    def test_names_are_unique_and_mild_differences_are_marked(self):
        raw, z, labels = cohort()
        z[:, 0] *= 0.1  # shrink every difference below the threshold
        z[:, 1] *= 0.1
        stories = describe_clusters(raw, z, labels, FEATURES, DEFS)
        self.assertTrue(all('(nhẹ)' in s['name'] for s in stories.values()))
        self.assertEqual(len({s['name'] for s in stories.values()}), 2)


if __name__ == '__main__':
    unittest.main()
