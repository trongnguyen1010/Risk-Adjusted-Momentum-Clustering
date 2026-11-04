"""Regression checks for the owner-approved B-PIT runtime cutoff gate."""
import csv
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from delta_t1.m3 import inputs
from delta_t1.m3.strategies import Strategies


ROOT = Path(__file__).resolve().parents[2]
DATES = ('2024-03-29', '2024-04-30', '2024-05-31')


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FinancialCutoffTests(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(financial_rule='not_weakest', market_rule='leading', n_min=1, top_share=0.3,
                        stale_months=18, combined_weight_market=0.5,
                        market_criteria={'mom_126': True}, financial_criteria={'roe': True})
        self.market = {d: [dict(ticker='AAA', cluster=0, liquidity='LIQUID',
                               features=dict(mom_126=0.5, mdd_126=-0.1, liquidity_21=1.0))] for d in DATES}
        self.fin = {y: {'AAA': (0, {'roe': 0.1, 'debt_to_equity': 1.0})} for y in (2022, 2023)}
        self.avail = {('AAA', 2022): dict(usable_from_date='2023-07-03'),
                      ('AAA', 2023): dict(usable_from_date='2024-03-15')}
        self.ind = {('AAA', y): dict(roe=0.1) for y in (2022, 2023)}
        self.order = {y: [0, 1, 2] for y in (2022, 2023)}
        self.cutoffs = {2022: '2023-04-30', 2023: '2024-04-30'}

    def strategies(self, *, labels=None, cutoffs=None):
        return Strategies(self.cfg, self.market, self.fin if labels is None else labels,
                          self.avail, {}, self.ind, fin_order=self.order,
                          financial_cutoffs=self.cutoffs if cutoffs is None else cutoffs)

    def test_before_at_and_after_cutoff_through_target_entry_point(self):
        strategies = self.strategies()
        for name in ('combined', 'financial_only'):
            with self.subTest(strategy=name):
                before = strategies.target_for(name, DATES[0])
                self.assertEqual(before['candidates'], 0)
                self.assertEqual(before['audit'][0]['financial_year'], 2023)
                self.assertEqual(before['audit'][0]['reason'], 'FINANCIAL_MODEL_BEFORE_CUTOFF')
                self.assertFalse(before['audit'][0]['financial_eligible'])
                self.assertEqual(before['engine_target']({'AAA': 0.5, 'CASH': 0.5}), {})
                for d in DATES[1:]:
                    result = strategies.target_for(name, d)
                    self.assertEqual(result['engine_target'], {'AAA': 1.0})
                    self.assertEqual(result['audit'][0]['financial_year'], 2023)

    def test_latest_usable_year_with_no_model_does_not_fall_back(self):
        strategies = self.strategies(labels={2022: self.fin[2022]}, cutoffs={2022: self.cutoffs[2022]})
        for name in ('combined', 'financial_only'):
            with self.subTest(strategy=name):
                result = strategies.target_for(name, DATES[2])
                self.assertEqual(result['candidates'], 0)
                self.assertEqual(result['audit'][0]['financial_year'], 2023)
                self.assertEqual(result['audit'][0]['reason'], 'FINANCIAL_MODEL_NOT_READY')

    def test_empty_model_metadata_blocks_financial_strategies(self):
        result = self.strategies(cutoffs={}).financial_only(DATES[2])
        self.assertEqual(result['audit'][0]['reason'], 'FINANCIAL_MODEL_NOT_READY')

    def test_market_controls_and_legacy_reference_keep_their_behavior(self):
        gated = self.strategies()
        reference = Strategies(self.cfg, self.market, self.fin, self.avail, {}, self.ind, fin_order=self.order)
        self.assertEqual(reference.combined(DATES[0])['target'], {'AAA': 1.0})
        for name in ('market_only', 'equal_weight', 'momentum_only'):
            self.assertEqual(gated.target_for(name, DATES[0])['target'], {'AAA': 1.0})

    def test_older_year_is_selected_until_newer_report_becomes_usable(self):
        self.avail['AAA', 2023]['usable_from_date'] = '2024-04-01'
        result = self.strategies().combined(DATES[0])
        self.assertEqual(result['target'], {'AAA': 1.0})
        self.assertEqual(result['audit'][0]['financial_year'], 2022)

    def write_artifact(self, folder):
        artifact = folder / 'bpit'
        artifact.mkdir()
        (artifact / 'manifest.json').write_text('{}', encoding='utf-8')
        models = {str(y): dict(cutoff=d, cluster_order=self.order[y]) for y, d in self.cutoffs.items()}
        (artifact / 'models.json').write_text(json.dumps(models), encoding='utf-8')
        (artifact / 'labels.csv').write_text('ticker,fiscal_year,cluster\nAAA,2022,0\nAAA,2023,0\n', encoding='utf-8')
        return artifact

    def test_artifact_loader_keeps_existing_interface_and_rejects_incomplete_models(self):
        with TemporaryDirectory() as folder:
            artifact = self.write_artifact(Path(folder))
            self.assertEqual(len(inputs.bpit(artifact)), 3)
            self.assertEqual(inputs.bpit(artifact, include_cutoffs=True)[3], self.cutoffs)
            (artifact / 'models.json').write_text(json.dumps({
                '2022': dict(cutoff=self.cutoffs[2022], cluster_order=[0, 1]),
                '2023': dict(cluster_order=[0, 1, 2]),
            }), encoding='utf-8')
            self.assertEqual(inputs.bpit(artifact, include_cutoffs=True)[3], {})

    def test_runner_and_feasibility_read_cutoffs_from_pinned_artifact(self):
        runner = load_script('run_m3')
        feasibility = load_script('m3_feasibility_variants')
        with TemporaryDirectory() as folder:
            root = Path(folder)
            artifact = self.write_artifact(root)
            cfg = dict(self.cfg, financial_pit=dict(artifact=str(artifact),
                       labels_sha256=inputs.sha256(artifact / 'labels.csv')),
                       status='READY_TO_LOCK_AFTER_BPIT', strategies=['combined', 'financial_only'],
                       segments=dict(holdout=[DATES[0], DATES[-1]]), segment_end_dates=dict(holdout=DATES[-1]))
            config = root / 'config.json'
            config.write_text(json.dumps(cfg), encoding='utf-8')
            market = dict(self.market, **{'2023-07-31': self.market[DATES[0]]})
            with patch.object(inputs, 'market_snapshots', return_value=market), \
                    patch.object(inputs, 'availability', return_value=self.avail), \
                    patch.object(inputs, 'sectors', return_value={}), \
                    patch.object(inputs, 'indicators', return_value=self.ind), \
                    patch.object(inputs, 'calendar', return_value=[DATES[0], '2024-04-01', DATES[1],
                                                                 '2024-05-02', DATES[2], '2024-06-03']), \
                    patch('builtins.print'):
                with patch.object(runner, 'ROOT', root), patch.object(runner, 'git_state', return_value=('fixture', False)), \
                        patch.object(runner, 'input_hashes', return_value={}), \
                        patch.object(sys, 'argv', ['run_m3', '--config', str(config), '--segment', 'holdout', '--targets-only']):
                    runner.main()
                run = next((root / 'data/experiments/m3/holdout').iterdir())
                for name in cfg['strategies']:
                    with (run / f'universe_audit_{name}.csv').open(encoding='utf-8', newline='') as f:
                        audit = list(csv.DictReader(f))
                    self.assertEqual(audit[0]['reason'], 'FINANCIAL_MODEL_BEFORE_CUTOFF')
                    self.assertEqual(audit[1]['in_candidate_universe'], 'True')
                    with (run / f'targets_{name}.csv').open(encoding='utf-8', newline='') as f:
                        targets = list(csv.DictReader(f))
                    self.assertEqual([r['candidates'] for r in targets], ['0', '1', '1'])
                self.assertFalse((run / 'metrics.json').exists())
                with patch.object(feasibility, 'ROOT', root), patch.object(feasibility, 'CONFIG', config), \
                        patch.object(sys, 'argv', ['m3_feasibility_variants']):
                    feasibility.main()
                result = next((root / 'data/experiments/m3/feasibility-variants').glob('*/variants.json'))
                payload = json.loads(result.read_text(encoding='utf-8'))
                self.assertTrue(payload['financial_source'].startswith('B_PIT:'))
                for variant in payload['variants'].values():
                    self.assertEqual(variant['monthly'][1]['candidates'], 0)
                    self.assertEqual(variant['monthly'][2]['candidates'], 1)
                self.assertEqual(payload['official_config']['monthly'][1]['candidates'], 0)
                self.assertEqual(payload['official_config']['monthly'][2]['candidates'], 1)


if __name__ == '__main__':
    unittest.main()
