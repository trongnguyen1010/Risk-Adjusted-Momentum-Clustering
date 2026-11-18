"""Q17 phải tuân theo strict segment isolation trước official backtest."""
import importlib.util
import csv
from datetime import datetime, timezone
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from delta_t1.m3 import inputs
from delta_t1.m3.prices import PriceBook


class PriceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.bundle = self.root / 'prices.sqlite'
        self.calendar = ['2023-12-27', '2023-12-28', '2023-12-29', '2024-01-02']
        with closing(sqlite3.connect(self.bundle)) as db, db:
            db.execute('create table prices (ticker text, date text, adj_close real, raw_close real, volume real)')
            db.executemany('insert into prices values (?, ?, ?, ?, ?)', [
                ('AAA', '2023-12-27', 100, 100, 10),
                ('AAA', '2023-12-28', 100, 100, 10),
                ('AAA', '2023-12-29', 200, 100, 10),
                ('AAA', '2024-01-02', 100, 100, 10),
            ])

    def book(self, dates, start='2023-12-27', end='2023-12-29'):
        return PriceBook(dates, self.calendar, bundle=self.bundle, segment_start=start, segment_end=end)

    def test_segment_end_does_not_use_next_segment_for_repair(self):
        book = self.book(['2023-12-29'])
        self.assertEqual(book.price('AAA', '2023-12-29'), 200)
        self.assertEqual(book.flags, [])
        self.assertNotIn(('AAA', '2024-01-02'), book.volume)
        self.assertIsNone(book.price('AAA', '2024-01-02'))
        self.assertIsNone(book.next_session('2023-12-29'))

    def test_future_price_and_calendar_append_do_not_change_segment(self):
        before = self.book(['2023-12-29'])
        with closing(sqlite3.connect(self.bundle)) as db, db:
            db.execute("update prices set adj_close=1000, volume=999 where date='2024-01-02'")
            db.execute("insert into prices values ('AAA', '2024-01-03', 1, 100, 999)")
        self.calendar.append('2024-01-03')
        after = self.book(['2023-12-29'])
        self.assertEqual((before.adj, before.volume, before.flags), (after.adj, after.volume, after.flags))

    def test_in_segment_glitch_still_repairs_and_source_stays_immutable(self):
        with closing(sqlite3.connect(self.bundle)) as db, db:
            db.execute("update prices set adj_close=200 where date='2023-12-28'")
            db.execute("update prices set adj_close=100 where date='2023-12-29'")
        source = inputs.sha256(self.bundle)
        book = self.book(['2023-12-28'])
        self.assertEqual(book.price('AAA', '2023-12-28'), 100)
        self.assertEqual(book.flags, [('AAA', '2023-12-28', 'ADJ_GLITCH_REPAIRED')])
        self.assertEqual(inputs.sha256(self.bundle), source)

    def test_segment_start_excludes_previous_segment_prices(self):
        book = self.book(['2023-12-29'], start='2023-12-29')
        self.assertEqual(set(book.volume), {('AAA', '2023-12-29')})
        self.assertEqual(book.flags, [])

    def test_sparse_loaded_neighbours_do_not_create_a_glitch(self):
        calendar = ['2023-12-01', '2023-12-04', '2023-12-05', '2023-12-06', '2023-12-07', '2023-12-08']
        with closing(sqlite3.connect(self.bundle)) as db, db:
            db.execute('delete from prices')
            db.executemany('insert into prices values (?, ?, ?, ?, ?)', [
                ('AAA', date, adjusted, 100, 10)
                for date, adjusted in zip(calendar, [100, 100, 200, 200, 100, 100])
            ])
        book = PriceBook(['2023-12-04', '2023-12-08'], calendar, bundle=self.bundle,
                         segment_start=calendar[0], segment_end=calendar[-1])
        self.assertNotIn(('AAA', '2023-12-06'), book.volume)
        self.assertEqual(book.price('AAA', '2023-12-05'), 200)
        self.assertEqual(book.flags, [])

    def test_missing_previous_session_does_not_repair_execution_price(self):
        calendar = ['2023-12-01', '2023-12-04', '2023-12-05', '2023-12-06']
        with closing(sqlite3.connect(self.bundle)) as db, db:
            db.execute('delete from prices')
            db.executemany('insert into prices values (?, ?, ?, ?, ?)', [
                ('AAA', '2023-12-01', 100, 100, 10),
                ('AAA', '2023-12-05', 200, 100, 10),
                ('AAA', '2023-12-06', 100, 100, 10),
            ])
        book = PriceBook(['2023-12-01', '2023-12-05'], calendar, bundle=self.bundle,
                         segment_start=calendar[0], segment_end=calendar[-1])
        self.assertEqual(book.price('AAA', '2023-12-05'), 200)
        self.assertEqual(book.flags, [])

    def test_exchange_sessions_across_holiday_still_repair(self):
        book = self.book(['2023-12-29'], end='2024-01-02')
        self.assertEqual(book.price('AAA', '2023-12-29'), 100)
        self.assertEqual(book.flags, [('AAA', '2023-12-29', 'ADJ_GLITCH_REPAIRED')])

    def test_requested_date_outside_segment_is_rejected(self):
        for d in ('2023-12-27', '2024-01-02'):
            with self.subTest(date=d), self.assertRaises(ValueError):
                self.book([d], start='2023-12-28')

    def test_enriched_full_dev_k4_k8_outputs_are_unchanged_by_future_append(self):
        for k in (4, 8):
            with self.subTest(k=k):
                root = self.root / f'k{k}'
                root.mkdir()
                bundle, database = root / 'terminal.sqlite', root / 'indicators.sqlite'
                names = [f'T{c}' for c in range(k)]
                calendar = ['2023-10-31', '2023-11-01', '2023-11-30', '2023-12-01',
                            '2023-12-27', '2023-12-28', '2023-12-29', '2024-01-02']
                with closing(sqlite3.connect(bundle)) as db, db:
                    db.execute('create table prices (ticker, date, adj_close, raw_close, volume)')
                    for date in calendar:
                        raw = 100 if date <= '2023-11-30' else 110 if date <= '2023-12-01' else 120
                        db.executemany('insert into prices values (?, ?, ?, ?, ?)', [
                            (t, date, raw * (2 if date == '2023-12-28' else 1), raw, 100) for t in names])
                with closing(sqlite3.connect(database)) as db, db:
                    db.execute('create table indicator_values (ticker, fiscal_year, metric, value, status)')
                    db.execute('create table company (ticker, sector_group)')
                    db.executemany('insert into company values (?, ?)', [(t, 'NON_FINANCIAL') for t in names])
                    db.executemany('insert into indicator_values values (?, ?, ?, ?, ?)', [
                        (t, 2022, 'roe', None if c == k - 2 else c + 1,
                         'IMPUTED_MEDIAN' if c == k - 1 else 'OK') for c, t in enumerate(names)])
                availability = root / 'availability.csv'
                availability.write_text('ticker,fiscal_year,date_source,usable_from_date\n' + ''.join(
                    f'{t},2022,CAFEF_DISCLOSURE,2023-03-01\n' for t in names), encoding='utf-8')
                artifact = root / 'bpit'
                artifact.mkdir()
                (artifact / 'models.json').write_text(json.dumps({'2022': dict(
                    k=k, cutoff='2023-04-30', cluster_order=list(reversed(range(k))))}), encoding='utf-8')
                (artifact / 'labels.csv').write_text('ticker,fiscal_year,cluster\n' + ''.join(
                    f'{t},2022,{c}\n' for c, t in enumerate(names)), encoding='utf-8')
                source_pins = dict(indicators_path=str(database), indicators_sha256=inputs.sha256(database),
                                   availability_path=str(availability), availability_sha256=inputs.sha256(availability))
                (artifact / 'manifest.json').write_text(json.dumps(dict(version='bpit_enriched_v1', inputs=dict(
                    indicators_enriched_sha256=source_pins['indicators_sha256'],
                    availability_sha256=source_pins['availability_sha256']))), encoding='utf-8')
                # LOCKED is confined to this synthetic fixture; never edit the actual READY config.
                cfg = dict(status='LOCKED', strategies=['combined', 'financial_only'], n_min=2, top_share=0.3,
                           financial_rule='not_weakest', market_rule='leading', stale_months=18,
                           market_criteria={'mom_126': True}, financial_criteria={'roe': True},
                           combined_weight_market=0.5, sharpe_allowed_segments=['final'],
                           segments={'development': ['2023-10-31', '2023-12-29']},
                           segment_end_dates={'development': '2023-12-29'}, financial_data=source_pins,
                           financial_pit=dict(artifact=str(artifact),
                                              labels_sha256=inputs.sha256(artifact / 'labels.csv'),
                                              models_sha256=inputs.sha256(artifact / 'models.json')),
                           limits_cache='data/experiments/m3/inputs/enriched_v1/limits.json')
                config = root / 'config.json'
                config.write_text(json.dumps(cfg), encoding='utf-8')
                def snapshot():
                    return [dict(ticker=t, cluster=0, liquidity='LIQUID',
                                 features=dict(mom_126=c + 1, mdd_126=-0.1, liquidity_21=100))
                            for c, t in enumerate(names)]
                market = {d: snapshot() for d in ('2023-10-31', '2023-11-30', '2023-12-29')}
                benchmark = {d: 100 for d in calendar}
                calendar_path = root / 'calendar.json'
                calendar_path.write_text(json.dumps(calendar), encoding='utf-8')
                benchmark_path = root / 'benchmark.json'
                benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')
                limits = {(t, d): (100, 1000, 1) for t in names for d in calendar}
                spec = importlib.util.spec_from_file_location('m3_append_runner',
                    Path(__file__).resolve().parents[2] / 'scripts/run_m3.py')
                runner = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(runner)
                def bounded_book(*args, **kwargs):
                    kwargs['bundle'] = bundle
                    return PriceBook(*args, **kwargs)
                def execute(second):
                    with patch.object(runner, 'ROOT', root), \
                            patch.object(runner, 'PriceBook', side_effect=bounded_book), \
                            patch.object(runner, 'load_limits', return_value=limits), \
                            patch.object(runner, 'git_state', return_value=('fixture', False)), \
                            patch.object(runner, 'datetime') as clock, \
                            patch.object(inputs, 'BUNDLE', bundle), patch.object(inputs, 'CALENDAR', calendar_path), \
                            patch.object(inputs, 'BENCHMARK', benchmark_path), \
                            patch.object(inputs, 'INDICATORS', root / 'forbidden-baseline.sqlite'), \
                            patch.object(inputs, 'AVAILABILITY', root / 'forbidden-baseline.csv'), \
                            patch.object(inputs, 'market_snapshots', return_value=market), \
                            patch.object(inputs, 'calendar', return_value=calendar), \
                            patch.object(inputs, 'benchmark', return_value=benchmark), \
                            patch.object(sys, 'argv', ['run_m3', '--config', str(config), '--segment', 'development',
                                                      '--skip-c8-prices-hash']), patch('builtins.print'):
                        clock.now.return_value = datetime(2026, 1, 1, 0, 0, second, tzinfo=timezone.utc)
                        runner.main()
                    output = sorted((root / 'data/experiments/m3/development').iterdir())[-1]
                    return output, {p.name: p.read_bytes() for p in output.iterdir() if p.name != 'manifest.json'}
                output, before = execute(0)
                before_manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
                with closing(sqlite3.connect(bundle)) as db, db:
                    db.execute("update prices set adj_close=99999, volume=99999 where date='2024-01-02'")
                    db.execute("insert into prices values ('T0', '2024-01-03', 1, 100, 1)")
                calendar.append('2024-01-03')
                market['2024-01-31'] = snapshot()
                benchmark.update({'2024-01-02': 99999, '2024-01-03': 1})
                calendar_path.write_text(json.dumps(calendar), encoding='utf-8')
                benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')
                after_output, after = execute(1)
                after_manifest = json.loads((after_output / 'manifest.json').read_text(encoding='utf-8'))
                self.assertEqual(before, after)  # targets/audit/NAV/ledger/holdings/metrics: identical bytes.
                self.assertEqual(before_manifest['counts'], after_manifest['counts'])
                self.assertNotEqual(before_manifest['inputs_sha256']['terminal_sha256'],
                                    after_manifest['inputs_sha256']['terminal_sha256'])
                for name in cfg['strategies']:
                    self.assertEqual(before_manifest['counts'][name], dict(
                        decisions=3, executed=2, too_small=0, not_executed_segment_end=1))
                    def read_csv(filename):
                        with (output / filename).open(encoding='utf-8', newline='') as f:
                            return list(csv.DictReader(f))
                    targets = read_csv(f'targets_{name}.csv')
                    audit = read_csv(f'universe_audit_{name}.csv')
                    for date in cfg['segments']['development'][0], '2023-11-30', '2023-12-29':
                        part = [r for r in targets if r['decision_date'] == date]
                        self.assertEqual({int(r['candidates']) for r in part}, {k - 2})
                        self.assertAlmostEqual(sum(float(r['target_weight']) for r in part), 1)
                        self.assertEqual(sum(r['in_candidate_universe'] == 'True' for r in audit
                                             if r['decision_date'] == date), k - 2)
                    self.assertEqual({r['status'] for r in targets if r['decision_date'] == '2023-12-29'},
                                     {'NOT_EXECUTED_SEGMENT_END'})
                    nav = read_csv(f'nav_{name}.csv')
                    self.assertEqual(nav[-1]['date'], '2023-12-29')
                    self.assertAlmostEqual(float(nav[-1]['nav']), 1.2)
                    self.assertTrue(all('2023-10-31' <= r['date'] <= '2023-12-29' for r in nav))
                    ledger = read_csv(f'trade_ledger_{name}.csv')
                    self.assertEqual({r['date'] for r in ledger}, {'2023-11-01', '2023-12-01'})
                metrics = json.loads((output / 'metrics.json').read_text(encoding='utf-8'))
                self.assertGreater(metrics['adj_glitches_repaired'], 0)
                self.assertTrue(all('sharpe_rf0' not in metrics[name] for name in cfg['strategies']))
                self.assertEqual(before_manifest['inputs_sha256']['indicators_sha256'], source_pins['indicators_sha256'])
                self.assertEqual(inputs.sha256(database), source_pins['indicators_sha256'])

    def test_runner_passes_both_boundaries_to_pricebook(self):
        spec = importlib.util.spec_from_file_location('m3_boundary_runner', Path('scripts/run_m3.py').resolve())
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        cfg = dict(status='LOCKED', strategies=['equal_weight'], n_min=10, top_share=0.3,
                   financial_rule='not_weakest', market_criteria={}, financial_criteria={},
                   segments={'development': ['2023-12-27', '2023-12-29']},
                   segment_end_dates={'development': '2023-12-29'}, sharpe_allowed_segments=['final'])
        config = self.root / 'config.json'
        config.write_text(json.dumps(cfg), encoding='utf-8')
        market = {d: [dict(ticker='AAA', cluster=0, liquidity='LIQUID', features={})]
                  for d in ('2023-12-27', '2023-12-29')}
        real_book = PriceBook
        def bounded_book(*args, **kwargs):
            self.assertEqual(kwargs['segment_start'], '2023-12-27')
            self.assertEqual(kwargs['segment_end'], '2023-12-29')
            kwargs['bundle'] = self.bundle
            return real_book(*args, **kwargs)
        with patch.object(runner, 'ROOT', self.root), \
                patch.object(runner, 'load_financial', return_value=({}, {}, 'B_PIT', None, {})), \
                patch.object(runner, 'git_state', return_value=('fixture', False)), \
                patch.object(runner, 'input_hashes', return_value={}), \
                patch.object(runner, 'PriceBook', side_effect=bounded_book) as book_call, \
                patch.object(runner, 'load_limits', return_value={('AAA', '2023-12-28'): (100, 110, 90)}), \
                patch.object(inputs, 'market_snapshots', return_value=market), \
                patch.object(inputs, 'availability', return_value={}), \
                patch.object(inputs, 'sectors', return_value={}), \
                patch.object(inputs, 'indicators', return_value={}), \
                patch.object(inputs, 'calendar', return_value=self.calendar), \
                patch.object(inputs, 'benchmark', return_value={d: 100 for d in self.calendar}), \
                patch.object(sys, 'argv', ['run_m3', '--config', str(config), '--segment', 'development']), \
                patch('builtins.print'):
            runner.main()
        book_call.assert_called_once()
        run = next((self.root / 'data/experiments/m3/development').iterdir())
        manifest = json.loads((run / 'manifest.json').read_text())
        self.assertEqual(manifest['counts']['equal_weight']['not_executed_segment_end'], 1)
        metrics = json.loads((run / 'metrics.json').read_text())
        self.assertEqual(metrics['adj_glitches_repaired'], 0)
        nav = (run / 'nav_equal_weight.csv').read_text()
        self.assertIn('2023-12-29,', nav)
        self.assertNotIn('2024-01-02', nav)


if __name__ == '__main__':
    unittest.main()
