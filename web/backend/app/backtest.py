"""Sealed M3-A backtest results for M3-B (configs/product/m3_backtest_v1.json), read-only and hash-pinned.

The bundle is built by scripts/build_m3_presentation.py from M3/outputs; nothing here recomputes a metric.
"""
import hashlib
import json
from pathlib import Path

from .repository import MissingData, InvalidQuery

CONFIG = 'configs/product/m3_backtest_v1.json'


class BacktestResults:
    def __init__(self, bundle):
        self.bundle = bundle

    @classmethod
    def from_config(cls, root):
        root = Path(root)
        pointer = json.loads((root / CONFIG).read_text(encoding='utf-8'))
        path = root / pointer['file']
        if not path.is_file():
            raise MissingData('M3 backtest bundle not published with this deploy.')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != pointer['file_sha256']:
            raise MissingData('M3 backtest bundle checksum mismatch.')
        bundle = json.loads(raw)
        if bundle.get('version') != pointer['version']:
            raise MissingData('M3 backtest bundle version mismatch.')
        return cls(bundle)

    def segment(self, name):
        found = self.bundle['segments'].get(name)
        if found is None:
            raise InvalidQuery(f'Unknown backtest segment: {name}.')
        return found

    def summary(self):
        """Metrics, counts and provenance of every segment, without the series."""
        keep = ('segment', 'run_id', 'start', 'end', 'status', 'financial_source', 'git_commit', 'config', 'config_sha256',
                'counts', 'seal', 'inputs_sha256', 'metrics', 'adj_glitches_repaired', 'sources')
        b = self.bundle
        return dict(version=b['version'], strategies=b['strategies'], benchmark=b['benchmark'],
                    final_status=b['final_status'], source_commit=b['source_commit'], config_sha256=b['config_sha256'],
                    outputs_manifest=b['outputs_manifest'],
                    segments=[{k: s[k] for k in keep} for s in b['segments'].values()])

    def series(self, name):
        s = self.segment(name)
        return dict(segment=name, run_id=s['run_id'], nav=s['nav'], drawdown=s['drawdown'], turnover=s['turnover'])

    def holdings(self, name, date=None):
        s = self.segment(name)
        periods = s['holdings']['periods']
        dates = [p['date'] for p in periods]
        if date is None:
            executed = [p for p in periods if p['executed']]
            period = executed[-1] if executed else periods[-1]
        elif date in dates:
            period = periods[dates.index(date)]
        else:
            raise MissingData(f'No {name} period on {date}.')
        return dict(segment=name, run_id=s['run_id'], strategy=s['holdings']['strategy'],
                    periods=[dict(date=p['date'], decision_date=p['decision_date'], status=p['status'],
                                  executed=p['executed'], n=len(p['items'])) for p in periods],
                    period=period)
