"""R2-06: synthetic full runs, mutations, immutable receipts and Dev/Holdout gates."""
from contextlib import closing, ExitStack
import csv
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from delta_t1.m3 import inputs
from delta_t1.m3.prices import PriceBook, load_limits

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('m3_verifier_tests', ROOT / 'scripts/verify_m3_enriched_run.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
runner = verifier.runner


class EnrichedVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / 'terminal.sqlite'
        self.database = self.root / 'financial.sqlite'
        self.calendar = ['2023-11-30', '2023-12-01', '2023-12-28', '2023-12-29',
                         '2024-01-31', '2024-02-01', '2024-02-28', '2024-02-29', '2024-03-01']
        self.decisions = ['2023-11-30', '2023-12-29', '2024-01-31', '2024-02-29']
        with closing(sqlite3.connect(self.bundle)) as db, db:
            db.execute('create table observations (kind, date, ticker, cluster, features, liquidity)')
            db.execute('create table prices (ticker, date, adj_close, raw_close, volume)')
            for date in self.decisions:
                for index, ticker in enumerate(('AAA', 'BBB', 'CCC')):
                    features = json.dumps(dict(mom_126=index + 1, mdd_126=-0.1, liquidity_21=10))
                    db.execute('insert into observations values (?, ?, ?, ?, ?, ?)',
                               ('market', date, ticker, 0, features, 'LIQUID'))
            for index, date in enumerate(self.calendar):
                price = 100 + (index // 2) * 10
                db.executemany('insert into prices values (?, ?, ?, ?, ?)',
                               [(t, date, price, price, 100) for t in ('AAA', 'BBB', 'CCC')])
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('create table company (ticker, sector_group)')
            db.execute('create table indicator_values (ticker, fiscal_year, metric, value)')
            db.executemany('insert into company values (?, ?)', [(t, 'NON_FINANCIAL') for t in ('AAA', 'BBB', 'CCC')])
            db.executemany('insert into indicator_values values (?, ?, ?, ?)',
                           [(t, 2022, 'roe', index + 1) for index, t in enumerate(('AAA', 'BBB', 'CCC'))])
        self.availability = self.root / 'availability.csv'
        self.availability.write_text('ticker,fiscal_year,date_source,usable_from_date\n' + ''.join(
            f'{t},2022,CAFEF_DISCLOSURE,2023-03-01\n' for t in ('AAA', 'BBB', 'CCC')), encoding='utf-8')
        artifact = self.root / 'bpit'
        artifact.mkdir()
        (artifact / 'labels.csv').write_text('ticker,fiscal_year,cluster\nAAA,2022,0\nBBB,2022,1\nCCC,2022,2\n', encoding='utf-8')
        self.write_json(artifact / 'models.json', {'2022': dict(k=3, cutoff='2023-04-30', cluster_order=[0, 1, 2])})
        pins = dict(indicators_path=str(self.database), indicators_sha256=inputs.sha256(self.database),
                    availability_path=str(self.availability), availability_sha256=inputs.sha256(self.availability))
        self.write_json(artifact / 'manifest.json', dict(version='bpit_enriched_v1', inputs=dict(
            indicators_enriched_sha256=pins['indicators_sha256'], availability_sha256=pins['availability_sha256'])))
        self.cfg = dict(status='LOCKED', strategies=list(verifier.STRATEGIES), n_min=1, top_share=0.3,
                        market_rule='leading', financial_rule='not_weakest', stale_months=18,
                        market_criteria={'mom_126': True}, financial_criteria={'roe': True}, combined_weight_market=0.5,
                        segments=dict(development=['2023-11-30', '2023-12-29'], holdout=['2024-01-31', '2024-02-29']),
                        segment_end_dates=dict(development='2023-12-29', holdout='2024-02-29'),
                        sharpe_allowed_segments=['final'], financial_data=pins,
                        financial_pit=dict(artifact=str(artifact), labels_sha256=inputs.sha256(artifact / 'labels.csv'),
                                           models_sha256=inputs.sha256(artifact / 'models.json')),
                        limits_cache='data/experiments/m3/inputs/enriched_v1/limits.json')
        self.config = self.root / 'config.json'
        self.write_json(self.config, self.cfg)
        self.calendar_path, self.benchmark_path, self.c8 = (self.root / name for name in ('calendar.jsonl', 'benchmark.jsonl', 'prices.jsonl'))
        self.calendar_path.write_text(''.join(json.dumps(dict(trade_date=d, exchange='HOSE', is_open=True)) + '\n'
                                              for d in self.calendar), encoding='utf-8')
        self.benchmark_path.write_text(''.join(json.dumps(dict(trade_date=d, index_id='VNINDEX', close=1000 + i * 10)) + '\n'
                                               for i, d in enumerate(self.calendar)), encoding='utf-8')
        self.c8.write_text(''.join(json.dumps(dict(trade_date=d, ticker=t, raw_close=100 + (i // 2) * 10,
                                                 ceiling_price=9999, floor_price=1)) + '\n'
                                  for i, d in enumerate(self.calendar) for t in ('AAA', 'BBB', 'CCC')), encoding='utf-8')
        market_reader, calendar_reader, benchmark_reader = inputs.market_snapshots, inputs.calendar, inputs.benchmark
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for obj, name, value in ((verifier, 'ROOT', self.root), (runner, 'ROOT', self.root),
                                 (inputs, 'BUNDLE', self.bundle), (inputs, 'CALENDAR', self.calendar_path),
                                 (inputs, 'BENCHMARK', self.benchmark_path), (inputs, 'PRICES_C8', self.c8)):
            self.stack.enter_context(patch.object(obj, name, value))
        self.stack.enter_context(patch.object(inputs, 'market_snapshots', side_effect=lambda *a, **k: market_reader(bundle=self.bundle)))
        self.stack.enter_context(patch.object(inputs, 'calendar', side_effect=lambda *a, **k: calendar_reader(path=self.calendar_path)))
        self.stack.enter_context(patch.object(inputs, 'benchmark', side_effect=lambda *a, **k: benchmark_reader(path=self.benchmark_path)))
        def book(*args, **kwargs):
            return PriceBook(*args, **dict(kwargs, bundle=self.bundle))
        self.stack.enter_context(patch.object(runner, 'PriceBook', side_effect=book))
        self.stack.enter_context(patch.object(runner, 'load_limits', side_effect=lambda dates, cache: load_limits(dates, path=self.c8)))
        self.stack.enter_context(patch.object(runner, 'git_state', return_value=('a' * 40, False)))
        self.full, self.targets, self.baseline = {}, {}, {}
        for index, segment in enumerate(('development', 'holdout')):
            for targets_only in (True, False):
                args = ['runner', '--config', str(self.config), '--segment', segment] + (['--targets-only'] if targets_only else [])
                with patch.object(runner, 'datetime') as clock, patch.object(sys, 'argv', args), patch('builtins.print'):
                    clock.now.return_value = datetime(2026, 1, 1, 0, index, int(not targets_only), tzinfo=timezone.utc)
                    runner.main()
                path = sorted((self.root / 'data/experiments/m3' / segment).iterdir())[-1]
                (self.targets if targets_only else self.full)[segment] = path
            # A distinct synthetic baseline reference has identical market controls.
            self.baseline[segment] = self.root / f'baseline-{segment}'
            shutil.copytree(self.full[segment], self.baseline[segment])

    def write_json(self, path, value):
        path.write_text(json.dumps(value, indent=1), encoding='utf-8')

    def verify(self, segment='development', *, seal=False, development_seal=None):
        return verifier.verify_and_seal(self.full[segment], targets_run=self.targets[segment],
                                        baseline_run=self.baseline[segment], seal=seal, development_seal=development_seal)

    def mutate_csv(self, directory, filename, key, value, index=0):
        path = directory / filename
        fields, rows = verifier.read_csv(path)
        rows[index][key] = value
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_valid_development_seal_keeps_all_run_bytes_and_is_exclusive(self):
        before = verifier.snapshot(self.full['development'])
        result = self.verify(seal=True)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(before, verifier.snapshot(self.full['development']))
        seal = self.full['development'] / 'seal.json'
        original = seal.read_bytes()
        with self.assertRaises(FileExistsError):
            self.verify(seal=True)
        self.assertEqual(seal.read_bytes(), original)

    def test_holdout_requires_dev_seal_and_resets_nav_to_one(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'Development seal'):
            self.verify('holdout', seal=True)
        self.assertFalse((self.full['holdout'] / 'seal.json').exists())
        self.verify(seal=True)
        result = self.verify('holdout', seal=True, development_seal=self.full['development'] / 'seal.json')
        self.assertEqual(result['status'], 'PASS')
        for segment in ('development', 'holdout'):
            _, nav = verifier.read_csv(self.full[segment] / 'nav_combined.csv')
            self.assertEqual(float(nav[0]['nav']), 1)
            self.assertGreater(float(nav[-1]['nav']), 1)
            self.assertEqual(nav[-1]['date'], self.cfg['segment_end_dates'][segment])

    def test_mutated_cash_ledger_holdings_nav_target_audit_and_turnover_are_rejected(self):
        mutations = [('holdings_combined.csv', 'weight', '0.75'),
                     ('trade_ledger_combined.csv', 'executed', '0.25'),
                     ('nav_combined.csv', 'nav', '2.0'),
                     ('targets_combined.csv', 'target_weight', '0.25'),
                     ('universe_audit_combined.csv', 'reason', 'FORGED'),
                     ('turnover_combined.csv', 'turnover', '0.99')]
        for filename, key, value in mutations:
            with self.subTest(file=filename):
                path = self.full['development'] / filename
                original = path.read_bytes()
                self.mutate_csv(self.full['development'], filename, key, value)
                with self.assertRaises(verifier.VerificationError):
                    self.verify(seal=True)
                self.assertFalse((self.full['development'] / 'seal.json').exists())
                path.write_bytes(original)

    def test_date_bounds_and_manifest_pins_are_rejected(self):
        path = self.full['development'] / 'manifest.json'
        original = path.read_bytes()
        mutations = [('end_date', '2024-01-02'), ('segment_start', '2023-01-01'),
                     ('config_sha256', '0' * 64), ('git_commit', 'b' * 40), ('git_dirty', True), ('targets_only', True)]
        for key, value in mutations:
            with self.subTest(key=key):
                manifest = json.loads(original)
                manifest[key] = value
                self.write_json(path, manifest)
                with self.assertRaises(verifier.VerificationError):
                    self.verify(seal=True)
                self.assertFalse((self.full['development'] / 'seal.json').exists())
                path.write_bytes(original)
        self.mutate_csv(self.full['development'], 'nav_combined.csv', 'date', '2024-01-02', index=-1)
        with self.assertRaises(verifier.VerificationError):
            self.verify(seal=True)

    def test_missing_or_wrong_input_hash_and_changed_source_are_rejected(self):
        path = self.full['development'] / 'manifest.json'
        original = path.read_bytes()
        for value in (None, '0' * 64):
            manifest = json.loads(original)
            manifest['inputs_sha256']['c8_prices_sha256'] = value
            self.write_json(path, manifest)
            with self.assertRaises(verifier.VerificationError):
                self.verify(seal=True)
            path.write_bytes(original)
        with self.c8.open('a', encoding='utf-8') as f:
            f.write('\n')
        with self.assertRaises(verifier.VerificationError):
            self.verify(seal=True)

    def test_metrics_sharpe_and_non_finite_values_are_rejected(self):
        path = self.full['development'] / 'metrics.json'
        original = path.read_bytes()
        for key, value in (('total_return', 99), ('sharpe_rf0', 1), ('cagr', float('nan'))):
            metrics = json.loads(original)
            metrics['combined'][key] = value
            self.write_json(path, metrics)
            with self.assertRaises(verifier.VerificationError):
                self.verify(seal=True)
            path.write_bytes(original)

    def test_targets_reference_controls_and_missing_output_are_rejected(self):
        refs = [(self.targets['development'], 'targets_combined.csv', 'candidates', '999'),
                (self.baseline['development'], 'nav_market_only.csv', 'nav', '999')]
        for directory, filename, key, value in refs:
            path = directory / filename
            original = path.read_bytes()
            self.mutate_csv(directory, filename, key, value)
            with self.assertRaises(verifier.VerificationError):
                self.verify(seal=True)
            path.write_bytes(original)
        fake_returns = self.targets['development'] / 'metrics.json'
        self.write_json(fake_returns, {})
        with self.assertRaisesRegex(verifier.VerificationError, 'must not contain returns'):
            self.verify(seal=True)
        fake_returns.unlink()
        path = self.full['development'] / 'holdings_combined.csv'
        path.rename(path.with_suffix('.missing'))
        with self.assertRaises(FileNotFoundError):
            self.verify(seal=True)

    def test_independent_cash_check_detects_inconsistent_cash_holdings(self):
        self.mutate_csv(self.full['development'], 'holdings_combined.csv', 'weight', '0.5', index=-1)
        with self.assertRaises(verifier.VerificationError):
            verifier.check_cash(self.full['development'], 'combined', ['2023-12-01'])

    def test_tampered_dev_seal_or_run_cannot_open_holdout(self):
        self.verify(seal=True)
        seal_path = self.full['development'] / 'seal.json'
        original = seal_path.read_bytes()
        for key, value in (('status', 'FAIL'), ('segment', 'holdout'), ('version', 'untrusted'), ('checks', [])):
            seal = json.loads(original)
            seal[key] = value
            self.write_json(seal_path, seal)
            with self.assertRaises(verifier.VerificationError):
                self.verify('holdout', seal=True, development_seal=seal_path)
            seal_path.write_bytes(original)
        self.mutate_csv(self.full['development'], 'nav_combined.csv', 'nav', '2')
        with self.assertRaises(verifier.VerificationError):
            self.verify('holdout', seal=True, development_seal=seal_path)
        self.assertFalse((self.full['holdout'] / 'seal.json').exists())

    def test_dev_and_holdout_execution_pins_must_be_identical(self):
        self.verify(seal=True)
        seal_path = self.full['development'] / 'seal.json'
        original = seal_path.read_bytes()
        for key, value in (('git_commit', 'b' * 40), ('config_sha256', '0' * 64), ('inputs_sha256', {})):
            seal = json.loads(original)
            seal['execution'][key] = value
            self.write_json(seal_path, seal)
            with self.assertRaises(verifier.VerificationError):
                self.verify('holdout', development_seal=seal_path)
            seal_path.write_bytes(original)

    def test_input_or_run_mutation_during_verification_prevents_seal(self):
        real_replay = verifier.replay
        for path in (self.c8, self.full['development'] / 'metrics.json'):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                changed = False
                def changing_replay(*args, **kwargs):
                    nonlocal changed
                    result = real_replay(*args, **kwargs)
                    if not changed:
                        path.write_bytes(original + b'\n')
                        changed = True
                    return result
                with patch.object(verifier, 'replay', side_effect=changing_replay):
                    with self.assertRaises(verifier.VerificationError):
                        self.verify(seal=True)
                self.assertFalse((self.full['development'] / 'seal.json').exists())
                path.write_bytes(original)

    def test_cli_failure_is_nonzero_and_creates_no_seal(self):
        argv = ['verify', '--run', str(self.full['holdout']), '--targets-run', str(self.targets['holdout']),
                '--baseline-run', str(self.baseline['holdout']), '--seal']
        with patch.object(sys, 'argv', argv), patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(verifier.main(), 1)
            self.assertEqual(json.loads(output.getvalue())['status'], 'FAIL')
        self.assertFalse((self.full['holdout'] / 'seal.json').exists())


if __name__ == '__main__':
    unittest.main()
