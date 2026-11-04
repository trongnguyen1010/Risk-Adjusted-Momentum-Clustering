"""Q17 phải tuân theo strict segment isolation trước official backtest."""
import importlib.util
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

    def test_requested_date_outside_segment_is_rejected(self):
        for d in ('2023-12-27', '2024-01-02'):
            with self.subTest(date=d), self.assertRaises(ValueError):
                self.book([d], start='2023-12-28')

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
