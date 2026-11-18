import json
from pathlib import Path
import unittest

from delta_t1.experiments.upgrade_reference import validate


class UpgradeProtocolTests(unittest.TestCase):
    def test_protocol_changes_and_unapproved_execution_are_rejected(self):
        root=Path(__file__).resolve().parents[3]
        original=json.loads((root/'configs/experiments/delta_upgrade_r1_v1.json').read_bytes())
        validate(original)
        for key,value in [('k',[2,3,10]),('n_init',1),('clipping',True),('holdout_claim',True)]:
            with self.subTest(key=key),self.assertRaises(ValueError):validate(dict(original,**{key:value}))
        with self.assertRaises(ValueError):validate(dict(original,owner_approval={'status':'PENDING'}))

    def test_preprocessing_replays_signed_zero_constant_and_tail_features(self):
        import numpy as np
        from delta_t1.clustering.reference_preprocessing import prepare,replay
        x=np.array([[-100,0,7,0],[-2,1,7,2],[0,2,7,3],[1,3,7,4],[1e5,5,7,8]],dtype=float)
        for recipe in ('P1','P2','P3'):
            with self.subTest(recipe=recipe):
                transformed,spec=prepare(x,recipe,2)
                np.testing.assert_allclose(transformed,replay(x,spec),rtol=1e-8,atol=1e-8)
                self.assertAlmostEqual(float(np.var(transformed[:,:2],axis=0).sum()),.5)
                self.assertAlmostEqual(float(np.var(transformed[:,2:],axis=0).sum()),.5)
                self.assertTrue(spec['constant'][2])
        for invalid in (np.array([[float('nan'),0],[1,2]]),np.ones((10,4))):
            with self.assertRaises(ValueError):prepare(invalid,'P3',2)

    def test_geometry_flags_preserve_singleton_and_unfavorable_silhouette(self):
        import numpy as np
        from sklearn.metrics import pairwise_distances
        from delta_t1.evaluation.reference_scorecard import score
        x=np.array([[i*.001,0] for i in range(100)]+[[1000,0]])
        labels=[0]*100+[1]
        d=pairwise_distances(x);np.fill_diagonal(d,0)
        metrics=score(x,labels,['tail','constant'],d,d)
        self.assertTrue(metrics['dominant_flag']);self.assertTrue(metrics['single_feature_flag'])
        self.assertEqual(metrics['singleton_count'],1);self.assertEqual(len(metrics['silhouette_distribution']),101)
        self.assertAlmostEqual(metrics['feature_contribution']['tail'],1)

if __name__=='__main__':unittest.main()
