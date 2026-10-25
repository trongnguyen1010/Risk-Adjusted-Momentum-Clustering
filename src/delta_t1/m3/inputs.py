"""Read the pinned M3 inputs (bundle v4, indicators v1, availability table, C8 benchmark/calendar)."""
import csv
import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / 'data/web/delta-intelligence-v4/terminal.sqlite'
INDICATORS = ROOT / 'data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite'
AVAILABILITY = ROOT / 'data/financial/disclosure_dates_v1/availability-0c412f60f7c21bd3/availability.csv'
C8 = ROOT / 'artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical'
BENCHMARK = C8 / 'benchmark_daily.jsonl'
CALENDAR = C8 / 'trading_calendar.jsonl'
PRICES_C8 = C8 / 'prices_daily.jsonl'
M2_LABELS_REF = 'origin/m2-clustering-experiment:M2/artifacts/m2-final-handoff-v1/m2_cluster_labels_for_m3.csv'


def sha256(path, chunk=1 << 22):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def _ro(path):
    return sqlite3.connect(f'file:{path}?mode=ro', uri=True)


def market_snapshots(bundle=BUNDLE):
    """{date: [{ticker, cluster, liquidity, features}]} for model A."""
    out = defaultdict(list)
    for date, ticker, cluster, features, liquidity in _ro(bundle).execute(
            "select date, ticker, cluster, features, liquidity from observations where kind='market' order by date, ticker"):
        out[date].append(dict(ticker=ticker, cluster=cluster, liquidity=liquidity, features=json.loads(features)))
    return dict(out)


def financial_labels(bundle=BUNDLE):
    """{fiscal_year: {ticker: (cluster, features)}} for model B."""
    out = defaultdict(dict)
    for date, ticker, cluster, features in _ro(bundle).execute(
            "select date, ticker, cluster, features from observations where kind='financial'"):
        out[int(date)][ticker] = (cluster, json.loads(features))
    return dict(out)


def indicators(path=INDICATORS, metrics=('roe', 'f_score', 'z_score')):
    """{(ticker, fiscal_year): {metric: value or None}}."""
    out = defaultdict(dict)
    marks = ','.join('?' * len(metrics))
    for ticker, year, metric, value in _ro(path).execute(
            f'select ticker, fiscal_year, metric, value from indicator_values where metric in ({marks})', metrics):
        out[(ticker, int(year))][metric] = value
    return dict(out)


def sectors(path=INDICATORS):
    return dict(_ro(path).execute('select ticker, sector_group from company'))


def availability(path=AVAILABILITY):
    """{(ticker, fiscal_year): row} from the availability table (usable_from_date may be empty)."""
    with open(path, encoding='utf-8') as f:
        return {(r['ticker'], int(r['fiscal_year'])): r for r in csv.DictReader(f)}


def benchmark(path=BENCHMARK):
    """{trade_date: close} for VNINDEX (price index)."""
    with open(path, encoding='utf-8') as f:
        return {r['trade_date']: r['close'] for r in map(json.loads, f) if r['index_id'] == 'VNINDEX'}


def calendar(path=CALENDAR, exchange='HOSE'):
    with open(path, encoding='utf-8') as f:
        return sorted(r['trade_date'] for r in map(json.loads, f) if r['exchange'] == exchange and r['is_open'])


def m2_labels(text):
    """Parse the M2 K=2 handoff CSV text -> {date: {ticker: cluster}}."""
    out = defaultdict(dict)
    for r in csv.DictReader(text.lstrip('﻿').splitlines()):
        out[r['snapshot_date']][r['ticker']] = int(r['cluster_label'])
    return dict(out)
