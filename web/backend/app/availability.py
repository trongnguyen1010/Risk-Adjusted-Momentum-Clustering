"""Annual-report availability dates (configs/product/financial_availability_v1.json), read-only and hash-pinned.

Summarises, per fiscal year, how many model-B companies have a CafeF disclosure date versus the 30/06 lag rule.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from .repository import MissingData

CONFIG = 'configs/product/financial_availability_v1.json'


class FinancialAvailability:
    def __init__(self, rows, meta):
        self.rows = rows  # {(ticker, fiscal_year): row}
        self.meta = meta

    @classmethod
    def from_config(cls, root):
        root = Path(root)
        pointer = json.loads((root / CONFIG).read_text(encoding='utf-8'))
        path = root / pointer['file']
        if not path.is_file():
            raise MissingData('Financial availability table not published with this deploy.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != pointer['file_sha256']:
            raise MissingData('Financial availability table checksum mismatch.')
        with path.open(encoding='utf-8') as f:
            rows = {(r['ticker'], int(r['fiscal_year'])): r for r in csv.DictReader(f)}
        return cls(rows, dict(version=pointer['version'], rule=pointer['rule']))

    def summary(self, tickers_by_year):
        """tickers_by_year: {fiscal_year: [ticker]} from the served model B."""
        years = []
        for year, tickers in sorted(tickers_by_year.items()):
            sources, pending = Counter(), 0
            for t in tickers:
                row = self.rows.get((t, year))
                sources[row['date_source'] if row else 'MISSING'] += 1
                pending += bool(row and not row['usable_from_date'])
            years.append(dict(year=year, companies=len(tickers), cafef=sources['CAFEF_DISCLOSURE'],
                              lag_rule=sources['LAG_RULE'], missing=sources['MISSING'], calendar_pending=pending))
        return dict(version=self.meta['version'], rule=self.meta['rule'], years=years)


def financial_tickers(repo):
    out = defaultdict(list)
    for r in repo.query("SELECT date, ticker FROM observations WHERE kind='financial'"):
        out[int(r['date'])].append(r['ticker'])
    return out
