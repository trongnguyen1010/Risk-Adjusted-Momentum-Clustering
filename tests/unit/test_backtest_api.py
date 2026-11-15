"""M3-B backtest bundle: hash pin, segment lookup, and traceability to the sealed M3/outputs files."""
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'web' / 'backend'))
from app.backtest import BacktestResults  # noqa: E402
from app.repository import MissingData, InvalidQuery  # noqa: E402

PERIOD = dict(date='2024-02-01', decision_date='2024-01-31', candidates=20, status='OK', executed=True,
              items=[dict(ticker='AAA', weight=0.5, rank=1)])
BUNDLE = dict(version='t', strategies=['combined'], benchmark='vnindex', final_status='NOT_READY', source_commit='c',
              config_sha256='s', outputs_manifest={}, segments=dict(holdout=dict(
                  segment='holdout', run_id='r', start='2024-01-31', end='2024-02-29', status='LOCKED',
                  financial_source='B_PIT', git_commit='c', config='x', config_sha256='s', counts={}, seal={},
                  inputs_sha256={}, metrics={}, adj_glitches_repaired=0, sources=[],
                  nav=dict(dates=['2024-02-01'], series={}), drawdown={}, turnover={},
                  holdings=dict(strategy='combined', periods=[PERIOD, dict(PERIOD, date='2024-03-01', status='NOT_EXECUTED_SEGMENT_END', executed=False, items=[])]))))


class BacktestResultsTests(unittest.TestCase):
    def build(self, sha=None, version='t'):
        root = Path(tempfile.mkdtemp())
        (root / 'configs/product').mkdir(parents=True)
        raw = json.dumps(BUNDLE).encode()
        (root / 'bundle.json').write_bytes(raw)
        (root / 'configs/product/m3_backtest_v1.json').write_text(json.dumps(
            dict(version=version, file='bundle.json', file_sha256=sha or hashlib.sha256(raw).hexdigest())), encoding='utf-8')
        return BacktestResults.from_config(root)

    def test_checksum_or_version_mismatch_fails_closed(self):
        with self.assertRaises(MissingData):
            self.build(sha='0' * 64)
        with self.assertRaises(MissingData):
            self.build(version='other')

    def test_holdings_default_to_last_executed_period(self):
        out = self.build().holdings('holdout')
        self.assertEqual(out['period']['date'], '2024-02-01')
        self.assertEqual([p['n'] for p in out['periods']], [1, 0])
        with self.assertRaises(MissingData):
            self.build().holdings('holdout', '2030-01-01')
        with self.assertRaises(InvalidQuery):
            self.build().series('final')


class BacktestEndpointTests(unittest.TestCase):
    def test_endpoints_serve_the_injected_bundle(self):
        try:
            from fastapi.testclient import TestClient
            from app.main import create_app
        except ImportError as error:
            raise self.skipTest('Optional API dependencies unavailable: ' + str(error))
        results = BacktestResultsTests().build()
        repo = type('Repo', (), dict(manifest={'database_sha256': 'x'}, meta={'model_configs': {}}))()
        with TestClient(create_app(repository=repo, fundamentals=False, availability=False, backtest=results)) as client:
            self.assertEqual(client.get('/api/v2/backtest').json()['segments'][0]['run_id'], 'r')
            self.assertEqual(client.get('/api/v2/backtest/holdout/holdings').json()['period']['date'], '2024-02-01')
            self.assertEqual(client.get('/api/v2/backtest/final/series').status_code, 400)
            self.assertEqual(client.get('/api/v2/backtest/holdout/holdings?date=2030-01-01').status_code, 404)


class PublishedBundleTests(unittest.TestCase):
    """The committed bundle must equal a fresh build and carry the sealed numbers unchanged."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.results = BacktestResults.from_config(ROOT)
        except (MissingData, FileNotFoundError) as error:
            raise unittest.SkipTest(str(error))

    def test_bundle_is_reproducible(self):
        done = subprocess.run([sys.executable, str(ROOT / 'scripts/build_m3_presentation.py'), '--check'],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_metrics_and_series_match_sealed_files(self):
        for seg in self.results.summary()['segments']:
            run = ROOT / Path(seg['seal']['path']).parent
            self.assertEqual(seg['metrics'], {k: v for k, v in json.loads((run / 'metrics.json').read_text()).items()
                                              if k in seg['metrics']})
            series = self.results.series(seg['segment'])
            with (run / 'nav_combined.csv').open(newline='') as f:
                nav = [float(r['nav']) for r in csv.DictReader(f)]
            self.assertEqual(series['nav']['series']['combined'], nav)
            for key in ('combined', 'vnindex'):
                self.assertAlmostEqual(min(series['drawdown']['series'][key]), seg['metrics'][key]['max_drawdown'], 12)


if __name__ == '__main__':
    unittest.main()
