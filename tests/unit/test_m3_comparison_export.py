"""R2-10: sealed provenance, independent segments, cash/positions, controls and adverse results."""
import csv
from contextlib import ExitStack
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_m3_enriched_verifier as run_tests

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('comparison_export_tests', ROOT / 'scripts/export_backtest_comparison_metrics.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ComparisonExportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = run_tests.EnrichedVerifierTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.verify(seal=True)
        self.fixture.verify('holdout', seal=True, development_seal=self.fixture.full['development'] / 'seal.json')
        self.paths = {(s, role): (self.fixture.baseline if role == 'baseline' else self.fixture.full)[s]
                      for s in exporter.SEGMENTS for role in ('baseline', 'enriched')}
        self.pins = {}
        for segment in exporter.SEGMENTS:
            path = self.fixture.baseline[segment]
            manifest = exporter.verifier.read_json(path / 'manifest.json')
            seal = dict(schema_version=1, status='PASS', artifacts_sha256=exporter.verifier.snapshot(path),
                        **exporter.verifier.receipt(manifest))
            self.fixture.write_json(path / 'seal.json', seal)
            self.pins[segment] = exporter.inputs.sha256(path / 'seal.json')
        self.root_patch = patch.object(exporter, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def build(self):
        return exporter.build_comparison(self.paths, baseline_seal_pins=self.pins)

    def reseal(self, segment, role):
        path = self.paths[segment, role]
        seal = exporter.verifier.read_json(path / 'seal.json')
        manifest = exporter.verifier.read_json(path / 'manifest.json')
        if role == 'enriched':
            seal['run_files_sha256'] = exporter.verifier.snapshot(path)
            seal['manifest_sha256'] = exporter.inputs.sha256(path / 'manifest.json')
            seal['execution'] = exporter.verifier.receipt(manifest)
        else:
            seal['artifacts_sha256'] = exporter.verifier.snapshot(path)
            seal.update(exporter.verifier.receipt(manifest))
        self.fixture.write_json(path / 'seal.json', seal)
        if role == 'baseline':
            self.pins[segment] = exporter.inputs.sha256(path / 'seal.json')
        elif segment == 'development':
            hold = self.paths['holdout', 'enriched'] / 'seal.json'
            data = exporter.verifier.read_json(hold)
            data['development_seal_sha256'] = exporter.inputs.sha256(path / 'seal.json')
            self.fixture.write_json(hold, data)

    def test_export_has_24_rows_separate_navs_traceable_pins_and_does_not_mutate_runs(self):
        before = {key: (exporter.verifier.snapshot(path), exporter.inputs.sha256(path / 'seal.json'))
                  for key, path in self.paths.items()}
        output = self.root / 'comparison'
        receipt = exporter.export_comparison(self.paths, baseline_seal_pins=self.pins, output=output)
        summary = exporter.presentation.rows(output / 'summary.csv')
        periods = exporter.presentation.rows(output / 'periods.csv')
        series = exporter.presentation.rows(output / 'nav_series.csv')
        differences = exporter.presentation.rows(output / 'comparison.csv')
        self.assertEqual(len(summary), 24)
        self.assertEqual(len(differences), 12)
        self.assertEqual(len(periods), 40)
        self.assertEqual(len(receipt['source_runs']), 4)
        self.assertEqual(len(receipt['outputs_sha256']), 4)
        for filename, digest in receipt['outputs_sha256'].items():
            self.assertEqual(exporter.inputs.sha256(output / filename), digest)
        for row in summary:
            self.assertIn(row['source_id'], receipt['source_runs'])
            self.assertEqual(float(row['nav_start']), 1)
            self.assertNotIn('sharpe_rf0', row)
        self.assertEqual({row['segment'] for row in series}, {'development', 'holdout'})
        for key, path in self.paths.items():
            self.assertEqual(before[key], (exporter.verifier.snapshot(path), exporter.inputs.sha256(path / 'seal.json')))
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'already exists'):
            exporter.export_comparison(self.paths, baseline_seal_pins=self.pins, output=output)

    def test_final_unexecuted_period_has_no_invented_cash_or_held_positions(self):
        result = self.build()
        final = [r for r in result['periods'] if not r['executed']]
        self.assertEqual(len(final), 20)
        for row in final:
            self.assertEqual(row['status'], 'NOT_EXECUTED_SEGMENT_END')
            self.assertIsNone(row['held_count'])
            self.assertIsNone(row['cash_after_trading'])
            self.assertIsNone(row['failed_buys'])
        self.assertEqual({r['price_basis'] for r in result['summary'] if r['strategy'] == 'vnindex'},
                         {exporter.BENCHMARK_BASIS})
        self.assertEqual({r['price_basis'] for r in result['summary'] if r['strategy'] != 'vnindex'},
                         {exporter.PRICE_BASIS})

    def test_negative_return_and_adverse_difference_are_retained(self):
        # A consistently sealed synthetic adverse result must be reported, not filtered out.
        path = self.paths['development', 'enriched']
        self.fixture.mutate_csv(path, 'nav_combined.csv', 'nav', '0.9', index=-1)
        metrics = exporter.verifier.read_json(path / 'metrics.json')
        metrics['combined'].update(total_return=-0.1, max_drawdown=-0.1, cagr=0.9 ** 12 - 1)
        self.fixture.write_json(path / 'metrics.json', metrics)
        self.reseal('development', 'enriched')
        result = self.build()
        row = next(r for r in result['summary'] if r['segment'] == 'development'
                   and r['source'] == 'enriched' and r['strategy'] == 'combined')
        self.assertEqual(row['total_return'], -0.1)
        change = next(r for r in result['comparison'] if r['segment'] == 'development' and r['strategy'] == 'combined')
        self.assertAlmostEqual(change['delta_total_return_pp'], -20)
        self.assertAlmostEqual(change['delta_max_drawdown_pp'], -10)
        self.assertEqual(len(result['summary']), 24)

    def test_modified_missing_or_nonpass_sealed_artifacts_are_rejected_before_output(self):
        path = self.paths['development', 'enriched']
        nav = path / 'nav_combined.csv'
        original = nav.read_bytes()
        nav.write_bytes(original + b'\n')
        output = self.root / 'bad-export'
        with self.assertRaises(exporter.verifier.VerificationError):
            exporter.export_comparison(self.paths, baseline_seal_pins=self.pins, output=output)
        self.assertFalse(output.exists())
        nav.write_bytes(original)
        seal = exporter.verifier.read_json(path / 'seal.json')
        seal['status'] = 'FAIL'
        self.fixture.write_json(path / 'seal.json', seal)
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'PASS'):
            self.build()

    def test_wrong_published_seal_pin_and_dev_dependency_are_rejected(self):
        expected = self.pins['development']
        self.pins['development'] = '0' * 64
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'published seal hash'):
            self.build()
        self.pins['development'] = expected
        path = self.paths['holdout', 'enriched'] / 'seal.json'
        seal = exporter.verifier.read_json(path)
        seal['development_seal_sha256'] = '0' * 64
        self.fixture.write_json(path, seal)
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'Dev seal dependency'):
            self.build()

    def test_market_source_mismatch_between_baseline_and_enriched_is_rejected(self):
        for segment in exporter.SEGMENTS:
            path = self.paths[segment, 'enriched'] / 'manifest.json'
            manifest = exporter.verifier.read_json(path)
            manifest['inputs_sha256']['c8_prices_sha256'] = '0' * 64
            self.fixture.write_json(path, manifest)
            self.reseal(segment, 'enriched')
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'market input pin'):
            self.build()

    def test_control_drift_is_rejected_even_if_artifact_has_been_resealed(self):
        path = self.paths['development', 'baseline']
        self.fixture.mutate_csv(path, 'nav_market_only.csv', 'nav', '99', index=-1)
        self.reseal('development', 'baseline')
        with self.assertRaises(exporter.verifier.VerificationError):
            self.build()

    def test_nav_bounds_and_metrics_series_mismatch_are_rejected(self):
        path = self.paths['development', 'enriched']
        nav = path / 'nav_combined.csv'; original = nav.read_bytes()
        self.fixture.mutate_csv(path, nav.name, 'date', '2024-01-02', index=-1)
        self.reseal('development', 'enriched')
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'bounds'):
            self.build()
        nav.write_bytes(original)
        metrics = exporter.verifier.read_json(path / 'metrics.json')
        metrics['combined']['total_return'] = 9
        self.fixture.write_json(path / 'metrics.json', metrics)
        self.reseal('development', 'enriched')
        with self.assertRaisesRegex(exporter.verifier.VerificationError, 'return series'):
            self.build()

    def test_cli_accepts_explicit_runs_and_records_source_and_output_hashes(self):
        anchor = self.root / 'baseline-manifest.json'
        self.fixture.write_json(anchor, dict(source_seals={s:dict(seal_sha256=h) for s,h in self.pins.items()}))
        argv = ['export', '--baseline-manifest', str(anchor), '--output', str(self.root / 'cli-export')]
        for (segment, role), path in self.paths.items():
            argv += [f'--{role}-{segment}', str(path)]
        with patch.object(sys, 'argv', argv), patch('sys.stdout', new_callable=io.StringIO) as out:
            exporter.main()
        self.assertIn('"status": "PASS"', out.getvalue())
        receipt = exporter.verifier.read_json(self.root / 'cli-export/manifest.json')
        self.assertEqual(receipt['status'], 'PASS')
        self.assertRegex(receipt['content_sha256'], r'^[0-9a-f]{64}$')


if __name__ == '__main__':
    unittest.main()
