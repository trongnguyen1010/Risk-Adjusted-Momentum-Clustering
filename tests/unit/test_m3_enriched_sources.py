"""R2-02: one pinned financial source for scoring, sectors, availability and receipts."""
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from delta_t1.m3 import inputs

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('m3_sources_runner', ROOT / 'scripts/run_m3.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EnrichedSourceTests(unittest.TestCase):
    def fixture(self, root):
        databases, availability = {}, {}
        for name, roe, sector, usable in (
                ('baseline', 0.1, 'BANK', '2024-06-03'),
                ('enriched', 0.4, 'INDUSTRIAL', '2024-03-01')):
            database = root / f'{name} # financial.sqlite'
            with closing(sqlite3.connect(database)) as db:
                db.execute('create table indicator_values (ticker, fiscal_year, metric, value)')
                db.execute('create table company (ticker, sector_group)')
                db.execute('insert into indicator_values values (?, ?, ?, ?)', ('AAA', 2023, 'roe', roe))
                db.execute('insert into company values (?, ?)', ('AAA', sector))
                db.commit()
            databases[name] = database
            table = root / f'{name}_availability.csv'
            table.write_text('ticker,fiscal_year,date_source,usable_from_date\n'
                             f'AAA,2023,CAFEF_DISCLOSURE,{usable}\n', encoding='utf-8')
            availability[name] = table
        artifact = root / 'bpit'
        artifact.mkdir()
        (artifact / 'models.json').write_text(json.dumps({'2023': dict(
            k=3, cutoff='2024-03-01', cluster_order=[0, 1, 2])}), encoding='utf-8')
        (artifact / 'labels.csv').write_text(
            'ticker,fiscal_year,cluster\nAAA,2023,0\nBBB,2023,1\nCCC,2023,2\n', encoding='utf-8')
        cfg = dict(status='READY_TO_LOCK_AFTER_BPIT', financial_rule='not_weakest', market_rule='leading',
                   n_min=1, top_share=0.3, stale_months=18, combined_weight_market=0.5,
                   market_criteria={'mom_126': True}, financial_criteria={'roe': True},
                   strategies=['combined'], segments={'holdout': ['2024-03-29', '2024-04-30']},
                   segment_end_dates={'holdout': '2024-04-30'},
                   financial_pit=dict(artifact=str(artifact),
                                      labels_sha256=inputs.sha256(artifact / 'labels.csv'),
                                      models_sha256=inputs.sha256(artifact / 'models.json')))
        cfg['limits_cache'] = 'data/experiments/m3/inputs/enriched_v1/limits.json'
        cfg['financial_data'] = dict(
            indicators_path=databases['enriched'].name,
            indicators_sha256=inputs.sha256(databases['enriched']),
            availability_path=availability['enriched'].name,
            availability_sha256=inputs.sha256(availability['enriched']))
        self.write_provenance(artifact, cfg)
        return cfg, artifact, databases, availability

    def write_provenance(self, artifact, cfg):
        (artifact / 'manifest.json').write_text(json.dumps({'inputs': dict(
            indicators_enriched_sha256=cfg['financial_data']['indicators_sha256'],
            availability_sha256=cfg['financial_data']['availability_sha256'])}), encoding='utf-8')

    def test_legacy_and_explicit_paths_resolve_without_default_argument_leak(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg, _, databases, availability = self.fixture(root)
            with patch.object(inputs, 'INDICATORS', databases['baseline']), \
                    patch.object(inputs, 'AVAILABILITY', availability['baseline']):
                self.assertEqual(inputs.financial_sources({}, root=root), dict(
                    indicators_path=databases['baseline'], availability_path=availability['baseline']))
                self.assertEqual(inputs.financial_sources(cfg, root=root), dict(
                    indicators_path=databases['enriched'], availability_path=availability['enriched']))
                cfg['financial_data']['indicators_path'] = str(databases['enriched'])
                self.assertEqual(inputs.financial_sources(cfg, root=root)['indicators_path'], databases['enriched'])

    def test_runner_uses_same_database_for_values_sectors_and_manifest(self):
        for name in ('baseline', 'enriched'):
            with self.subTest(source=name), TemporaryDirectory() as folder:
                root = Path(folder)
                cfg, artifact, databases, availability = self.fixture(root)
                if name == 'baseline':
                    del cfg['financial_data']
                config = root / 'config.json'
                config.write_text(json.dumps(cfg), encoding='utf-8')
                other = root / 'market_input'
                other.write_text('fixture', encoding='utf-8')
                market = {'2024-03-29': [dict(ticker='AAA', cluster=0, liquidity='LIQUID',
                          features=dict(mom_126=0.5, mdd_126=-0.1, liquidity_21=1.0))]}
                with patch.object(runner, 'ROOT', root), \
                        patch.object(inputs, 'INDICATORS', databases['baseline']), \
                        patch.object(inputs, 'AVAILABILITY', availability['baseline']), \
                        patch.object(inputs, 'BUNDLE', other), patch.object(inputs, 'BENCHMARK', other), \
                        patch.object(inputs, 'CALENDAR', other), \
                        patch.object(inputs, 'market_snapshots', return_value=market), \
                        patch.object(inputs, 'calendar', return_value=['2024-03-29', '2024-04-01', '2024-04-30']), \
                        patch.object(runner, 'git_state', return_value=('fixture', False)), \
                        patch.object(runner, 'Strategies', wraps=runner.Strategies) as strategies, \
                        patch.object(sys, 'argv', ['run_m3', '--config', str(config), '--segment', 'holdout',
                                                  '--targets-only']), patch('builtins.print'):
                    runner.main()
                arguments = strategies.call_args.args
                self.assertEqual(arguments[4], {'AAA': 'BANK' if name == 'baseline' else 'INDUSTRIAL'})
                self.assertEqual(arguments[5], {('AAA', 2023): {'roe': 0.1 if name == 'baseline' else 0.4}})
                self.assertEqual(arguments[3][('AAA', 2023)]['usable_from_date'],
                                 '2024-06-03' if name == 'baseline' else '2024-03-01')
                output = next((root / 'data/experiments/m3/holdout').iterdir())
                manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
                hashes = manifest['inputs_sha256']
                self.assertEqual(hashes['indicators_sha256'], inputs.sha256(databases[name]))
                self.assertEqual(hashes['availability_sha256'], inputs.sha256(availability[name]))
                self.assertEqual(hashes['b_pit_labels_sha256'], inputs.sha256(artifact / 'labels.csv'))
                self.assertEqual(hashes['b_pit_models_sha256'], inputs.sha256(artifact / 'models.json'))
                self.assertIsNone(hashes['c8_prices_sha256'])
                self.assertEqual(manifest['financial_source'], 'B_PIT')
                self.assertFalse((output / 'metrics.json').exists())

    def test_missing_or_wrong_source_pins_fail_before_outputs(self):
        for key in ('indicators_path', 'indicators_sha256', 'availability_path', 'availability_sha256'):
            for missing in (False, True):
                with self.subTest(key=key, missing=missing), TemporaryDirectory() as folder:
                    root = Path(folder)
                    cfg, _, _, _ = self.fixture(root)
                    if missing:
                        del cfg['financial_data'][key]
                    else:
                        cfg['financial_data'][key] = 'does-not-exist' if key.endswith('_path') else '0' * 64
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        inputs.financial_sources(cfg, root=root)
                    self.assertFalse((root / 'data/experiments').exists())

    def test_missing_or_wrong_model_and_label_pins_are_rejected(self):
        for key in ('labels_sha256', 'models_sha256'):
            for missing in (False, True):
                with self.subTest(key=key, missing=missing), TemporaryDirectory() as folder:
                    root = Path(folder)
                    cfg, _, _, _ = self.fixture(root)
                    if missing:
                        del cfg['financial_pit'][key]
                    else:
                        cfg['financial_pit'][key] = '0' * 64
                    with self.assertRaisesRegex(ValueError, 'financial_pit|B-PIT'):
                        runner.load_financial(cfg, True)

    def test_mismatched_bpit_provenance_is_rejected(self):
        for key in ('indicators_enriched_sha256', 'availability_sha256'):
            for missing in (False, True):
                with self.subTest(key=key, missing=missing), TemporaryDirectory() as folder:
                    root = Path(folder)
                    cfg, artifact, _, _ = self.fixture(root)
                    manifest = json.loads((artifact / 'manifest.json').read_text(encoding='utf-8'))
                    if missing:
                        del manifest['inputs'][key]
                    else:
                        manifest['inputs'][key] = '0' * 64
                    (artifact / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'source does not match'):
                        runner.load_financial(cfg, True)

    def test_baseline_manifest_shape_is_accepted_with_explicit_sources(self):
        with TemporaryDirectory() as folder:
            cfg, artifact, _, _ = self.fixture(Path(folder))
            manifest = {'inputs': {name: {'sha256': cfg['financial_data'][f'{name}_sha256']}
                                   for name in ('indicators', 'availability')}}
            (artifact / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            self.assertEqual(runner.load_financial(cfg, True)[2], 'B_PIT')

    def test_explicit_sources_never_fall_back_to_b_v4(self):
        with TemporaryDirectory() as folder:
            cfg, _, _, _ = self.fixture(Path(folder))
            del cfg['financial_pit']
            with patch.object(inputs, 'financial_labels') as fallback:
                with self.assertRaisesRegex(ValueError, 'no B v4 fallback'):
                    runner.load_financial(cfg, True)
                fallback.assert_not_called()

    def test_enriched_artifact_without_financial_data_never_uses_baseline(self):
        with TemporaryDirectory() as folder:
            cfg, artifact, _, _ = self.fixture(Path(folder))
            del cfg['financial_data']
            manifest = {'version': 'bpit_enriched_v1'}
            (artifact / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'no baseline SQLite fallback'):
                runner.load_financial(cfg, True)

    def test_enriched_config_preserves_all_baseline_strategy_rules(self):
        baseline = json.loads((ROOT / 'configs/experiments/m3_strategy_v1.json').read_text(encoding='utf-8'))
        enriched = json.loads((ROOT / 'configs/experiments/m3_strategy_enriched_v1.json').read_text(encoding='utf-8'))
        allowed = {'version', 'status', 'status_note', 'financial_model', 'financial_pit',
                   'financial_data', 'limits_cache'}
        self.assertEqual({k: v for k, v in baseline.items() if k not in allowed},
                         {k: v for k, v in enriched.items() if k not in allowed})
        self.assertEqual(enriched['status'], 'READY_TO_LOCK_AFTER_BPIT')
        self.assertEqual(enriched['financial_data']['indicators_path'],
                         'data/financial/indicators_enriched_v1/indicators_enriched_v1_run01/indicators.sqlite')
        self.assertEqual(enriched['financial_pit']['artifact'],
                         'data/financial/b_pit_enriched_v1/bpit_enriched_v1_run01')
        for section, keys in (('financial_data', ['indicators_sha256', 'availability_sha256']),
                              ('financial_pit', ['labels_sha256', 'models_sha256'])):
            for key in keys:
                self.assertRegex(enriched[section][key], r'^[0-9a-f]{64}$')
        self.assertNotEqual(runner.limits_cache_path(baseline), runner.limits_cache_path(enriched))

    def test_enriched_cache_is_separate_and_alias_of_baseline_is_rejected(self):
        with TemporaryDirectory() as folder, patch.object(runner, 'ROOT', Path(folder)):
            baseline = Path(folder) / 'data/experiments/m3/inputs/limits.json'
            self.assertEqual(runner.limits_cache_path({}), baseline)
            cfg = {'financial_data': {}, 'limits_cache': 'data/experiments/m3/inputs/enriched_v1/limits.json'}
            self.assertNotEqual(runner.limits_cache_path(cfg), baseline)
            for value in (None, '', str(baseline),
                          'data/experiments/m3/inputs/enriched_v1/../limits.json'):
                cfg['limits_cache'] = value
                with self.subTest(cache=value), self.assertRaisesRegex(ValueError, 'cache'):
                    runner.limits_cache_path(cfg)

    def test_ready_config_rejects_full_run_before_loading_data(self):
        config = ROOT / 'configs/experiments/m3_strategy_enriched_v1.json'
        with patch.object(sys, 'argv', ['run_m3', '--config', str(config), '--segment', 'development']), \
                patch.object(runner, 'load_financial') as loader:
            with self.assertRaisesRegex(SystemExit, 'only --targets-only'):
                runner.main()
            loader.assert_not_called()

    def test_full_runner_passes_enriched_cache_to_limits_loader(self):
        # A synthetic LOCKED fixture verifies wiring; the real config remains READY.
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg, _, _, _ = self.fixture(root)
            cfg.update(status='LOCKED', strategies=[], sharpe_allowed_segments=['final'])
            config = root / 'config.json'
            config.write_text(json.dumps(cfg), encoding='utf-8')
            other = root / 'market_input'
            other.write_text('fixture', encoding='utf-8')
            with patch.object(runner, 'ROOT', root), \
                    patch.object(inputs, 'BUNDLE', other), patch.object(inputs, 'BENCHMARK', other), \
                    patch.object(inputs, 'CALENDAR', other), \
                    patch.object(inputs, 'market_snapshots', return_value={}), \
                    patch.object(inputs, 'calendar', return_value=['2024-03-29', '2024-04-30']), \
                    patch.object(inputs, 'benchmark', return_value={'2024-04-30': 100}), \
                    patch.object(runner, 'git_state', return_value=('fixture', False)), \
                    patch.object(runner, 'PriceBook') as book, \
                    patch.object(runner, 'load_limits', return_value={}) as limits, \
                    patch.object(sys, 'argv', ['run_m3', '--config', str(config), '--segment', 'holdout',
                                              '--skip-c8-prices-hash']), patch('builtins.print'):
                book.return_value.flags = []
                runner.main()
                limits.assert_called_once_with(['2024-04-30'], cache=root / cfg['limits_cache'])
            output = next((root / 'data/experiments/m3/holdout').iterdir())
            manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['limits_cache'], cfg['limits_cache'])

    def test_sqlite_special_character_path_is_read_only_and_missing_is_not_created(self):
        with TemporaryDirectory() as folder:
            _, _, databases, _ = self.fixture(Path(folder))
            database = databases['enriched']
            original = inputs.sha256(database)
            connection = inputs._ro(database)
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute('delete from indicator_values')
            finally:
                connection.close()
            self.assertEqual(inputs.sha256(database), original)
            missing = Path(folder) / 'missing.sqlite'
            with self.assertRaises(sqlite3.OperationalError):
                inputs._ro(missing)
            self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
