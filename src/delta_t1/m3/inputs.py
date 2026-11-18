"""Read the pinned M3 inputs (bundle v4, indicators v1, availability table, C8 benchmark/calendar)."""
import csv
import hashlib
import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / 'data/web/delta-intelligence-v4/terminal.sqlite'
INDICATORS = ROOT / 'data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/indicators.sqlite'
AVAILABILITY = ROOT / 'data/financial/disclosure_dates_v1/availability-4f0f83108e761dae/availability.csv'
C8 = ROOT / 'artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical'
BENCHMARK = C8 / 'benchmark_daily.jsonl'
CALENDAR = C8 / 'trading_calendar.jsonl'
PRICES_C8 = C8 / 'prices_daily.jsonl'
M2_LABELS_REF = 'origin/m2-clustering-experiment:M2/artifacts/m2-final-handoff-v1/m2_cluster_labels_for_m3.csv'
BPIT_BASE = ROOT / 'data/financial/b_pit_v1'


def sha256(path, chunk=1 << 22):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def _ro(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def financial_sources(cfg, *, root=ROOT):
    """Resolve and validate the optional financial_data pins; legacy configs keep baseline paths."""
    if 'financial_data' not in cfg:
        return dict(indicators_path=INDICATORS, availability_path=AVAILABILITY)
    pin = cfg['financial_data']
    if not isinstance(pin, dict):
        raise ValueError('financial_data must contain explicit paths and SHA-256 pins')
    paths = {}
    for name in ('indicators', 'availability'):
        value, expected = pin.get(f'{name}_path'), pin.get(f'{name}_sha256')
        if not value or not expected:
            raise ValueError(f'financial_data requires {name}_path and {name}_sha256')
        path = Path(value)
        path = (Path(root) / path).resolve() if not path.is_absolute() else path.resolve()
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f'{name} sha256 {actual} does not match pinned {expected}')
        paths[f'{name}_path'] = path
    return paths


def market_snapshots(bundle=BUNDLE):
    """{date: [{ticker, cluster, liquidity, features}]} for model A."""
    out = defaultdict(list)
    with closing(_ro(bundle)) as connection:
        for date, ticker, cluster, features, liquidity in connection.execute(
                "select date, ticker, cluster, features, liquidity from observations where kind='market' order by date, ticker"):
            out[date].append(dict(ticker=ticker, cluster=cluster, liquidity=liquidity, features=json.loads(features)))
    return dict(out)


def financial_labels(bundle=BUNDLE):
    """{fiscal_year: {ticker: (cluster, features)}} for model B."""
    out = defaultdict(dict)
    with closing(_ro(bundle)) as connection:
        for date, ticker, cluster, features in connection.execute(
                "select date, ticker, cluster, features from observations where kind='financial'"):
            out[int(date)][ticker] = (cluster, json.loads(features))
    return dict(out)


def indicators(path=INDICATORS, metrics=('roe', 'f_score', 'z_score')):
    """{(ticker, fiscal_year): {metric: value or None}}."""
    out = defaultdict(dict)
    marks = ','.join('?' * len(metrics))
    with closing(_ro(path)) as connection:
        for ticker, year, metric, value in connection.execute(
                f'select ticker, fiscal_year, metric, value from indicator_values where metric in ({marks})', metrics):
            out[(ticker, int(year))][metric] = value
    return dict(out)


def sectors(path=INDICATORS):
    with closing(_ro(path)) as connection:
        return dict(connection.execute('select ticker, sector_group from company'))


def availability(path=AVAILABILITY, *, historical_reference=False):
    """Read availability under Q-date, or reproduce the original B v4 reference."""
    rows = {}
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            year = int(row['fiscal_year'])
            required_source = 'LAG_RULE' if year < 2022 else 'CAFEF_DISCLOSURE'
            if historical_reference or row['date_source'] == required_source:
                rows[row['ticker'], year] = row
    return rows


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


def bpit(artifact_dir, *, include_cutoffs=False):
    """Read a B-PIT artifact (scripts/build_financial_pit_clusters.py).

    Returns (labels, order, manifest): labels = {fiscal_year: {ticker: (cluster, {})}} in the same shape as
    financial_labels(); order = {fiscal_year: [cluster best → worst]} frozen at the cutoff (plan §3.1.5).
    include_cutoffs adds a fourth result mapping model-ready fiscal years to their cutoff dates.
    """
    artifact_dir = Path(artifact_dir)
    if not artifact_dir.is_absolute():
        artifact_dir = ROOT / artifact_dir
    manifest = json.loads((artifact_dir / 'manifest.json').read_text(encoding='utf-8'))
    models = json.loads((artifact_dir / 'models.json').read_text(encoding='utf-8'))
    labels = defaultdict(dict)
    with open(artifact_dir / 'labels.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            year, ticker = int(r['fiscal_year']), r['ticker']
            if ticker in labels[year]:
                raise ValueError(f'Duplicate B-PIT label: {ticker}, FY{year}')
            labels[year][ticker] = (int(r['cluster']), {})
    order = {int(y): m.get('cluster_order', []) for y, m in models.items()}
    if include_cutoffs:
        cutoffs = {}
        for y, model in models.items():
            year = int(y)
            # Old artifacts without k retain their three-cluster contract.
            k = model.get('k', 3)
            ranked = order[year]
            if type(k) is not int or k < 3 or not isinstance(ranked, list):
                continue
            if (any(type(c) is not int for c in ranked)
                    or sorted(ranked) != list(range(k))):
                continue
            observed = {c for c, _ in labels.get(year, {}).values()}
            expected = set(range(k))
            if not observed or not observed <= expected:
                continue
            # Explicit k identifies the complete model export; every cluster must occur.
            if 'k' in model and observed != expected:
                continue
            if model.get('cutoff'):
                cutoffs[year] = date.fromisoformat(model['cutoff']).isoformat()
        return dict(labels), order, manifest, cutoffs
    return dict(labels), order, manifest
