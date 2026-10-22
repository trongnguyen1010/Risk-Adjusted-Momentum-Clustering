"""Bounded synthetic tests; the real V2 holdout feature payload is never loaded."""
import ast
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from delta_t1.experiments import final_holdout_v2 as h
from delta_t1.io import digest, write_json

ROOT = Path(__file__).resolve().parents[3]


def synthetic_rows(day):
    rows=[]
    for i in range(102):
        level=(i%6) + (12 if i>=51 else 0)
        rows.append(dict(security_id=f'FIXTURE:{i:03d}',as_of_date=day,
                         available_at=day+'T17:00:00+07:00',adjustment_basis='vendor_adjusted',
                         market_feature_ready_v2=True,
                         **{f:level*(j+1)+i*.001 for j,f in enumerate(h.M2_MARKET_FEATURES)}))
    return rows


class HoldoutV2Tests(unittest.TestCase):
    def test_real_preflight_verifies_development_without_opening_holdout(self):
        with patch.object(h,'load_verified_market_only_features',side_effect=AssertionError('Holdout opened')):
            gate=h.freeze_gate(ROOT)
        self.assertEqual(('kmeans','sklearn',2,[2]),
                         (gate['algorithm'],gate['clustering']['implementation'],gate['clustering']['k'],gate['clustering']['k_range']))
        self.assertEqual((60,24),(len(gate['dev_diagnostics']),len(gate['task_config']['holdout_snapshots'])))

    def test_wrong_flags_and_unpinned_input_fail_before_holdout(self):
        original=h.read_json
        cfg=original(ROOT/h.CONFIG_PATH)
        for key,value in [('min_eligible_count',120),('selected_method','PCA_KMeans'),
                          ('implementation','stdlib'),('k_scan_enabled',True)]:
            bad=copy.deepcopy(cfg);bad[key]=value
            def read(p):return bad if p==ROOT/h.CONFIG_PATH else original(p)
            with self.subTest(key=key),patch.object(h,'read_json',side_effect=read),self.assertRaises(ValueError):
                h.freeze_gate(ROOT)
        bad=copy.deepcopy(cfg);bad['frozen_inputs_sha256'][cfg['decision_path']]='0'*64
        with patch.object(h,'read_json',side_effect=lambda p:bad if p==ROOT/h.CONFIG_PATH else original(p)):
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                h.freeze_gate(ROOT)

    def test_future_availability_rejected(self):
        gate=h.freeze_gate(ROOT)
        day=gate['task_config']['holdout_snapshots'][0]
        rows=synthetic_rows(day)
        rows[0].update(feature_version='1.6.0',available_at='2026-01-01T17:00:00+07:00')
        with patch.object(h,'load_verified_market_only_features',return_value=({},rows)):
            with self.assertRaisesRegex(ValueError,'future availability'):
                h.prepare_holdout(ROOT,gate)

    def test_full_synthetic_run_rerun_and_tamper(self):
        gate=h.freeze_gate(ROOT)
        tmp_parent=ROOT/'tmp';tmp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='holdout-v2-fixture-',dir=tmp_parent) as td:
            root=Path(td).resolve()
            self.assertTrue(root.is_relative_to(tmp_parent.resolve()))
            gate=copy.deepcopy(gate)
            cfg=gate['task_config'];cfg['feature_store']='fixture_store';cfg['synthetic']=True
            eval_dir=root/'development';eval_dir.mkdir()
            for name in ['cluster_profiles.csv','temporal_stability.csv']:
                shutil.copy2(gate['evaluation_dir']/name,eval_dir/name)
            gate['evaluation_dir']=eval_dir
            source_path=root/'fixture_store';(source_path/'canonical').mkdir(parents=True)
            feature=source_path/'canonical/feature_snapshots.jsonl';feature.write_text('{}\n',encoding='utf-8')
            source=dict(data_version='SYNTHETIC_FIXTURE',outputs={'canonical/feature_snapshots.jsonl':digest(feature.read_bytes())})
            write_json(source_path/'manifest.json',source)
            code=root/'fixture.py';code.write_text('# synthetic source only\n',encoding='utf-8')
            gate['input_sha256']={'fixture.py':digest(code.read_bytes())}
            gate['code_sha256']=dict(gate['input_sha256'])
            prepared=[]
            ready={0,1,3}
            for i,day in enumerate(cfg['holdout_snapshots']):
                prepared.append(dict(snapshot_date=day,status='ready' if i in ready else 'skipped',
                    eligible_count=102 if i in ready else 0,reason=None if i in ready else 'synthetic skip',
                    rows=synthetic_rows(day) if i in ready else []))
            with patch.object(h,'freeze_gate',return_value=gate),patch.object(h,'prepare_holdout',return_value=(source,prepared)),patch.object(h,'_code_paths',return_value=[code]):
                target,manifest=h.run_final_holdout(root)
                self.assertTrue(manifest['synthetic'])
                self.assertEqual((3,21,306,1),(manifest['n_snapshots'],manifest['n_skipped'],manifest['n_assignments'],manifest['n_temporal_pairs']))
                pairs=h._csv_rows(target/'temporal_stability.csv')
                self.assertEqual([(cfg['holdout_snapshots'][0],cfg['holdout_snapshots'][1])],
                                 [(r['from_date'],r['to_date']) for r in pairs])
                self.assertEqual(4,len(h._csv_rows(target/'transition_matrices.csv')))
                self.assertEqual(16,len(h._csv_rows(target/'centroid_drift.csv')))
                with patch.object(h,'fit_holdout',side_effect=AssertionError('Rerun refit')):
                    self.assertEqual((target,manifest),h.run_final_holdout(root))
                    (target/'assignments.csv').write_text('tampered',encoding='utf-8')
                    with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                        h.run_final_holdout(root)

    def test_incomplete_evidence_never_refits(self):
        gate=h.freeze_gate(ROOT)
        tmp_parent=ROOT/'tmp';tmp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='holdout-v2-incomplete-',dir=tmp_parent) as td:
            root=Path(td).resolve();self.assertTrue(root.is_relative_to(tmp_parent.resolve()))
            target=root/gate['task_config']['output_dir'];target.mkdir(parents=True)
            write_json(target/'manifest.json',{'status':'failed'})
            with patch.object(h,'freeze_gate',return_value=gate),patch.object(h,'fit_holdout',side_effect=AssertionError('Refit')):
                with self.assertRaisesRegex(ValueError,'Incomplete run'):
                    h.run_final_holdout(root)

    def test_notebook_all_code_cells_compile(self):
        nb=json.loads((ROOT/'M2/notebooks/11_final_holdout_execution_v2.ipynb').read_text(encoding='utf-8'))
        for i,c in enumerate(nb['cells']):
            if c['cell_type']=='code':ast.parse(''.join(c['source']),filename=f'cell{i}')


if __name__=='__main__':
    unittest.main()
