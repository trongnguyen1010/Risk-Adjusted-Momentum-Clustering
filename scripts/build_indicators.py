"""Compute annual product indicators 2016-2025 from a standardized input run (D-IND-01).

Reads data/financial/indicators_v1/inputs/<run-id>/ (latest.json by default) and
year-end raw closes from terminal.sqlite; writes a new versioned folder under
data/financial/indicators_v1/results/<run-id>/. Older results are never touched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import pandas as pd  # noqa: E402

from delta_t1.indicators import compute as c  # noqa: E402
from delta_t1.indicators import inputs as ind  # noqa: E402

INPUTS = 'data/financial/indicators_v1/inputs'
RESULTS = 'data/financial/indicators_v1/results'
TERMINAL = 'data/web/delta-intelligence-v1/terminal.sqlite'
READINESS = ('data/financial/history_api_input_review1522_v1/jobs/a4585089037bb3d9e5f2/results/'
             'f5ae2b9bff8017c53091/symbols-readiness.csv')
CODE = ['src/delta_t1/indicators/compute.py', 'scripts/build_indicators.py']
YEARS = range(2016, 2026)
MAX_PRICE_GAP_DAYS = 30
LATEST_METRICS = ('eps', 'bvps', 'pe', 'pb', 'roe', 'roa', 'market_cap', 'f_score', 'm_score', 'z_score', 'z_score_dp')


def digest(body):
    return hashlib.sha256(body).hexdigest()


def year_end_prices(con):
    """Last raw_close on or before 31/12 of each year, at most 30 days earlier."""
    rows = con.execute("select ticker, date, raw_close from prices where substr(date, 6, 2) = '12' "
                       "and raw_close is not null order by ticker, date").fetchall()
    out = {}
    for ticker, date, close in rows:
        year = int(date[:4])
        gap = (pd.Timestamp(f'{year}-12-31') - pd.Timestamp(date)).days
        if gap <= MAX_PRICE_GAP_DAYS:
            out.setdefault(ticker, {})[year] = (float(close), date)  # Ordered by date: last one wins.
    return out


def last_prices(con):
    return {t: (d, float(p)) for t, d, p in con.execute(
        'select p.ticker, p.date, p.raw_close from prices p join (select ticker, max(date) d from prices '
        'where raw_close is not null group by ticker) m on p.ticker = m.ticker and p.date = m.d')}


def write_sqlite(path, company, values, latest, metadata):
    con = sqlite3.connect(path)
    con.executescript('''
        create table company(ticker text primary key, name text, exchange text, template_family text, sector_group text);
        create table indicator_values(ticker text, fiscal_year integer, metric text, value real, status text,
                                      inputs_json text, primary key(ticker, fiscal_year, metric));
        create table latest(ticker text primary key, latest_fiscal_year integer, last_price real, last_price_date text,
                            shares real, market_cap_last real, metrics_json text);
        create table metadata(key text primary key, value text);
    ''')
    con.executemany('insert into company values (?,?,?,?,?)', company)
    con.executemany('insert into indicator_values values (?,?,?,?,?,?)', values)
    con.executemany('insert into latest values (?,?,?,?,?,?,?)', latest)
    con.executemany('insert into metadata values (?,?)', metadata)
    con.execute('create index indicator_ticker on indicator_values(ticker, metric, fiscal_year)')
    con.commit()
    con.execute('vacuum')
    con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', help='input run folder (default: latest.json)')
    args = parser.parse_args()
    inputs_dir = ROOT / (args.inputs or json.loads((ROOT / INPUTS / 'latest.json').read_text())['path'])
    wide = pd.read_parquet(inputs_dir / 'inputs-wide.parquet')
    families = pd.read_csv(ROOT / READINESS, usecols=['symbol', 'diagnostic_template_family']).rename(
        columns={'symbol': 'ticker', 'diagnostic_template_family': 'template_family'})
    con = sqlite3.connect(f'file:{ROOT / TERMINAL}?mode=ro', uri=True)
    try:
        meta = pd.read_sql('select ticker, name, exchange from securities', con)
        prices, last = year_end_prices(con), last_prices(con)
    finally:
        con.close()
    company = families.merge(meta, on='ticker', how='left')
    company['sector_group'] = [ind.sector_group(t, f) for t, f in zip(company.ticker, company.template_family)]

    fields = list(ind.FIELDS)
    by_ticker = {t: {int(r['fiscal_year']): {f: r[f] for f in fields if pd.notna(r[f])}
                     for r in g.to_dict('records')} for t, g in wide.groupby('ticker')}
    sources = {(r['ticker'], int(r['fiscal_year'])): sorted({r['src__' + f] for f in fields if pd.notna(r['src__' + f])})
               for r in wide.to_dict('records')}

    values, latest, wide_rows = [], [], []
    for t, sector in zip(company.ticker, company.sector_group):
        rows = by_ticker.get(t, {})
        px = {y: v[0] for y, v in prices.get(t, {}).items()}
        cells = c.compute_ticker(rows, px, sector, YEARS)
        for year, metrics in cells.items():
            src = sources.get((t, year), [])
            for metric, item in metrics.items():
                body = dict(item['inputs'])
                if src:
                    body['sources'] = src
                if metric == 'price' and year in prices.get(t, {}):
                    body['price_date'] = prices[t][year][1]
                values.append((t, year, metric, item['value'], item['status'],
                               json.dumps(body, ensure_ascii=False, separators=(',', ':'), allow_nan=False, default=str)))
            wide_rows.append(dict(ticker=t, fiscal_year=year, **{m: metrics[m]['value'] for m in c.METRICS},
                                  **{m + '__status': metrics[m]['status'] for m in c.METRICS}))
        reported = [y for y in YEARS if rows.get(y)]
        fy = max(reported) if reported else None
        date, close = last.get(t, (None, None))
        shares = cells[fy]['shares']['value'] if fy else None
        summary = {m: dict(value=cells[fy][m]['value'], status=cells[fy][m]['status']) for m in LATEST_METRICS} if fy else {}
        latest.append((t, fy, close, date, shares, close * shares if close and shares else None,
                       json.dumps(summary, allow_nan=False)))

    code_pins = {p: ind.sha256_file(ROOT / p) for p in CODE}
    inputs_manifest = (inputs_dir / 'manifest.json').read_bytes()
    pins = dict(inputs_run=inputs_dir.name, inputs_manifest_sha256=digest(inputs_manifest),
                terminal_sha256=ind.sha256_file(ROOT / TERMINAL), readiness_sha256=ind.sha256_file(ROOT / READINESS),
                code=code_pins)
    run_id = 'indicators-' + digest(json.dumps(pins, sort_keys=True).encode())[:16]
    out = ROOT / RESULTS / run_id
    if out.exists():
        print('run exists, not overwritten:', out.relative_to(ROOT).as_posix())
        return
    out.mkdir(parents=True)
    company_rows = [tuple(None if pd.isna(v) else v for v in r)
                    for r in company[['ticker', 'name', 'exchange', 'template_family', 'sector_group']].itertuples(index=False)]
    metadata = [('run_id', run_id), ('pins', json.dumps(pins)), ('years', '2016-2025'),
                ('decision', 'D-IND-01'), ('price_basis', 'raw_close last session <= 31/12, gap <= 30 days')]
    write_sqlite(out / 'indicators.sqlite', company_rows, values, latest, metadata)

    frame = pd.DataFrame(wide_rows)
    frame.to_csv(out / 'indicators-wide.csv', index=False)
    status = pd.DataFrame(values, columns=['ticker', 'fiscal_year', 'metric', 'value', 'status', 'inputs_json'])
    status = status.merge(company[['ticker', 'sector_group']], on='ticker')
    coverage = (status.groupby(['metric', 'fiscal_year', 'sector_group', 'status']).size()
                .rename('cells').reset_index())
    coverage.to_csv(out / 'coverage-summary.csv', index=False)
    (out / 'input-pins.json').write_text(json.dumps(pins, indent=2), encoding='utf-8')
    manifest = {n: digest((out / n).read_bytes()) for n in
                ('indicators.sqlite', 'indicators-wide.csv', 'coverage-summary.csv', 'input-pins.json')}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (ROOT / RESULTS / 'latest.json').write_text(json.dumps(dict(run_id=run_id, path=out.relative_to(ROOT).as_posix())),
                                                encoding='utf-8')
    ok25 = status[(status.fiscal_year == 2025) & (status.status == 'OK')].groupby('metric').ticker.nunique()
    print(f'{run_id}: {len(company)} tickers, {len(values)} cells from {inputs_dir.name}')
    print('2025 OK tickers:', ', '.join(f'{m}={ok25.get(m, 0)}' for m in ('eps', 'pe', 'pb', 'roe', 'f_score', 'm_score', 'z_score')))
    print('output:', out.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
