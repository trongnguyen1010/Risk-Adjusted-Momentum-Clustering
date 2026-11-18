"""R2-04: feasibility config, source pins, segment bounds and parity with runner audit."""
from collections import Counter
from contextlib import ExitStack
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from delta_t1.m3 import inputs
import test_m3_enriched_sources as source_tests

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('m3_feasibility_config', ROOT / 'scripts/m3_feasibility_variants.py')
feasibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feasibility)
runner = feasibility.m3_runner


class FeasibilityConfigTests(unittest.TestCase):
    def fixture(self, root):
        builder = source_tests.EnrichedSourceTests()
        cfg, artifact, databases, availability = builder.fixture(root)
        cfg.update(n_min=2, segments={'development': ['2024-03-29', '2024-04-30'],
                                      'holdout': ['2024-05-31', '2024-06-28']},
                   segment_end_dates={'development': '2024-04-30', 'holdout': '2024-06-28'})
        for path in availability.values():
            with path.open('a', encoding='utf-8') as f:
                f.write('BBB,2023,CAFEF_DISCLOSURE,2024-03-01\n')
                f.write('CCC,2023,CAFEF_DISCLOSURE,2024-03-01\n')
        cfg['financial_data']['availability_sha256'] = inputs.sha256(availability['enriched'])
        models = json.loads((artifact / 'models.json').read_text(encoding='utf-8'))
        models['2023']['cutoff'] = '2024-04-30'
        (artifact / 'models.json').write_text(json.dumps(models), encoding='utf-8')
        cfg['financial_pit']['models_sha256'] = inputs.sha256(artifact / 'models.json')
        builder.write_provenance(artifact, cfg)
        dates = ['2024-01-31', '2024-03-29', '2024-04-30', '2024-05-31', '2024-06-28', '2024-07-31']
        market = {date: [dict(ticker=ticker, cluster=0, liquidity='LIQUID',
                            features=dict(mom_126=0.5, mdd_126=-0.1, liquidity_21=1))
                         for ticker in ('AAA', 'BBB', 'CCC')] for date in dates}
        return cfg, market, databases, availability

    def environment(self, root, market, databases, availability):
        stack = ExitStack()
        other = root / 'other-input'
        other.write_text('fixture', encoding='utf-8')
        for obj, name, value in (
                (feasibility, 'ROOT', root), (runner, 'ROOT', root),
                (inputs, 'INDICATORS', databases['baseline']), (inputs, 'AVAILABILITY', availability['baseline']),
                (inputs, 'BUNDLE', other), (inputs, 'BENCHMARK', other), (inputs, 'CALENDAR', other)):
            stack.enter_context(patch.object(obj, name, value))
        stack.enter_context(patch.object(inputs, 'market_snapshots', return_value=market))
        stack.enter_context(patch.object(inputs, 'calendar', return_value=[
            '2024-03-29', '2024-04-01', '2024-04-30', '2024-05-02',
            '2024-05-31', '2024-06-03', '2024-06-28']))
        stack.enter_context(patch.object(runner, 'git_state', return_value=('fixture', False)))
        stack.enter_context(patch('builtins.print'))
        return stack

    def run_feasibility(self, root, cfg, *, default=False, extra=()):
        config = root / 'config.json'
        config.write_text(json.dumps(cfg), encoding='utf-8')
        argv = ['feasibility'] + ([] if default else ['--config', 'config.json']) + list(extra)
        with patch.object(feasibility, 'CONFIG', config if default else root / 'forbidden-baseline.json'), \
                patch.object(sys, 'argv', argv):
            feasibility.main()
        result = max((root / 'data/experiments/m3/feasibility-variants').glob('*/variants.json'))
        return json.loads(result.read_text(encoding='utf-8'))

    def test_explicit_baseline_and_enriched_match_runner_counts_and_exclusion_reasons(self):
        for source in ('baseline', 'enriched'):
            with self.subTest(source=source), TemporaryDirectory() as folder:
                root = Path(folder)
                cfg, market, databases, availability = self.fixture(root)
                if source == 'baseline':
                    del cfg['financial_data']
                with self.environment(root, market, databases, availability):
                    report = self.run_feasibility(root, cfg)
                    for segment in cfg['segments']:
                        with patch.object(sys, 'argv', ['runner', '--config', 'config.json', '--segment', segment,
                                                       '--targets-only']):
                            runner.main()
                        output = next((root / 'data/experiments/m3' / segment).iterdir())
                        with (output / 'targets_combined.csv').open(encoding='utf-8', newline='') as f:
                            targets = list(csv.DictReader(f))
                        with (output / 'universe_audit_combined.csv').open(encoding='utf-8', newline='') as f:
                            audit = list(csv.DictReader(f))
                        monthly = [r for r in report['official_config']['monthly'] if r['segment'] == segment]
                        self.assertEqual([r['date'] for r in monthly], sorted({r['decision_date'] for r in targets}))
                        for row in monthly:
                            target = next(t for t in targets if t['decision_date'] == row['date'])
                            self.assertEqual(row['candidates'], int(target['candidates']))
                            expected = [a for a in audit if a['decision_date'] == row['date']]
                            self.assertEqual({a['ticker']: a['reason'] for a in row['audit']},
                                             {a['ticker']: a['reason'] for a in expected})
                            self.assertEqual(row['reason_counts'],
                                             dict(Counter(a['reason'] for a in expected if a['reason'])))
                        stats = report['official_config']['summary'][segment]
                        self.assertEqual(stats['months'], 2)
                        self.assertEqual(stats['below_10'], 2)
                        self.assertEqual(stats['universe_too_small'], 2)
                        self.assertEqual(stats['selected_median'], 0)
                        self.assertEqual(stats['considered'], 6)
                        self.assertTrue(all(stats['reason_rates'][k] == n / 6
                                            for k, n in stats['reason_counts'].items()))
                self.assertEqual(report['inputs_sha256']['indicators_sha256'], inputs.sha256(databases[source]))
                self.assertEqual(report['inputs_sha256']['availability_sha256'], inputs.sha256(availability[source]))
                self.assertEqual(len(report['official_config']['monthly']), 4)
                if source == 'enriched':
                    april = report['official_config']['monthly'][1]
                    self.assertEqual(april['candidates'], 1)
                    self.assertEqual(april['reason_counts']['FINANCIAL_CRITERIA_MISSING'], 1)
                    self.assertEqual(report['official_config']['monthly'][0]['reason_counts'],
                                     {'FINANCIAL_MODEL_BEFORE_CUTOFF': 3})
                    va = next(v for v in report['variants'].values() if v['market_rule'] == 'leading'
                              and v['financial_rule'] == 'not_weakest')
                    self.assertEqual(va['monthly'][1]['candidates'], 2)
                else:
                    self.assertEqual(report['official_config']['monthly'][1]['reason_counts']['FINANCIAL_SECTOR_NO_B'], 1)

    def test_omitted_config_keeps_legacy_default(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg, market, databases, availability = self.fixture(root)
            del cfg['financial_data']
            with self.environment(root, market, databases, availability):
                report = self.run_feasibility(root, cfg, default=True)
            self.assertEqual(report['config'], str(root / 'config.json'))
            self.assertTrue(report['financial_source'].startswith('B_PIT:'))

    def test_bad_pins_stop_before_any_market_read_or_output(self):
        for section, key in (('financial_data', 'indicators_sha256'), ('financial_data', 'availability_sha256'),
                             ('financial_pit', 'labels_sha256'), ('financial_pit', 'models_sha256')):
            with self.subTest(key=key), TemporaryDirectory() as folder:
                root = Path(folder)
                cfg, market, databases, availability = self.fixture(root)
                cfg[section][key] = '0' * 64
                with self.environment(root, market, databases, availability), \
                        patch.object(inputs, 'market_snapshots') as read_market:
                    with self.assertRaises(ValueError):
                        self.run_feasibility(root, cfg)
                    read_market.assert_not_called()
                self.assertFalse((root / 'data/experiments').exists())

    def test_b_v4_override_is_rejected_for_enriched_config(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg, market, databases, availability = self.fixture(root)
            with self.environment(root, market, databases, availability), patch.object(inputs, 'financial_labels') as fallback:
                with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit) as error:
                    self.run_feasibility(root, cfg, extra=['--b-v4'])
                self.assertEqual(error.exception.code, 2)
                fallback.assert_not_called()
            self.assertFalse((root / 'data/experiments').exists())

    def test_empty_configured_segments_report_zero_months_and_null_statistics(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg, _, databases, availability = self.fixture(root)
            with self.environment(root, {}, databases, availability):
                report = self.run_feasibility(root, cfg)
            for segment in cfg['segments']:
                stats = report['official_config']['summary'][segment]
                self.assertEqual(stats['months'], 0)
                self.assertEqual(stats['below_10'], 0)
                self.assertIsNone(stats['min'])
                self.assertIsNone(stats['median'])
                self.assertEqual(stats['reason_rates'], {})

    def test_missing_end_and_overlapping_segments_are_rejected(self):
        cfg = dict(segments={'development': ['2024-01-01', '2024-12-31']}, segment_end_dates={})
        with self.assertRaisesRegex(ValueError, 'no segment_end_date'):
            feasibility.decision_segments(cfg, {})
        cfg = dict(segments={'development': ['2024-01-01', '2024-12-31'],
                             'holdout': ['2024-06-01', '2024-12-31']},
                   segment_end_dates={'development': '2024-12-31', 'holdout': '2024-12-31'})
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            feasibility.decision_segments(cfg, {'2024-06-28': []})


if __name__ == '__main__':
    unittest.main()
