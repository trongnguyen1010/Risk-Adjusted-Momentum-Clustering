"""Build the standardized annual input table for product indicators (D-IND-01).

Offline only. Writes a new versioned folder under
data/financial/indicators_v1/inputs/<run-id>/ and never touches older artifacts.
"""
import argparse
import glob
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import pandas as pd  # noqa: E402

from delta_t1.indicators import inputs as ind  # noqa: E402

JOB = 'data/financial/history_api_input_review1522_v1/jobs/a4585089037bb3d9e5f2'
READINESS = JOB + '/results/f5ae2b9bff8017c53091/symbols-readiness.csv'
DSTOCK_GLOB = 'data/financial/history_dstock_*/raw/*.json'
TERMINAL = 'data/web/delta-intelligence-v1/terminal.sqlite'
OUT = 'data/financial/indicators_v1/inputs'
CODE = ['src/delta_t1/indicators/inputs.py', 'scripts/build_indicator_inputs.py',
        'src/delta_t1/experiments/financial_template_candidates.py', 'src/delta_t1/ingestion/dstock_financial.py']


def digest(body):
    return hashlib.sha256(body).hexdigest()


def securities():
    con = sqlite3.connect(f'file:{ROOT / TERMINAL}?mode=ro', uri=True)
    try:
        return pd.read_sql('select ticker, name, exchange from securities', con)
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    pins = ind.Pins(ROOT)
    families = ind.load_families(pins, READINESS)
    regular, regular_stats = ind.load_cafef_regular(pins, JOB, families)
    financial, financial_stats = ind.load_cafef_financial(pins, JOB, families)
    direct, direct_stats = ind.load_cafef_direct_cashflow(pins, JOB, families, regular)
    raw = sorted(Path(p).relative_to(ROOT).as_posix() for p in glob.glob(str(ROOT / DSTOCK_GLOB)))
    regular_tickers = set(families.loc[families.template_family == 'Regular', 'ticker'])
    dstock, dstock_stats = ind.load_dstock(pins, raw, regular_tickers)
    dstock_report = ind.validate_dstock(regular, dstock)
    accepted = set(dstock_report.loc[dstock_report.accepted, 'field'])
    long = ind.combine([regular, financial, direct], dstock, accepted)
    wide = ind.pivot_wide(long, families, securities())
    checks = ind.run_checks(wide)
    coverage = ind.coverage(wide)

    pins.files[TERMINAL] = ind.sha256_file(ROOT / TERMINAL)
    for path in CODE:
        pins.files[path] = ind.sha256_file(ROOT / path)
    pin_body = json.dumps(dict(sorted(pins.files.items())), indent=1).encode()
    run_id = 'inputs-' + digest(pin_body)[:16]
    out = ROOT / OUT / run_id
    products = {
        'inputs-wide.parquet': None,
        'inputs-long.csv.gz': None,
        'coverage.csv': coverage.to_csv(index=False).encode(),
        'checks.csv': checks.to_csv(index=False).encode(),
        'dstock-mapping-qa.csv': dstock_report.to_csv(index=False).encode(),
        'input-pins.json': pin_body,
    }
    if out.exists():
        print('run exists, not overwritten:', out.relative_to(ROOT).as_posix())
        return
    out.mkdir(parents=True)
    wide.to_parquet(out / 'inputs-wide.parquet', index=False)
    long.sort_values(['ticker', 'fiscal_year', 'field']).to_csv(out / 'inputs-long.csv.gz', index=False)
    for name, body in products.items():
        if body is not None:
            (out / name).write_bytes(body)
    by_source = long.source.str.split(':').str[0].value_counts().to_dict()
    summary = dict(run_id=run_id, tickers=int(wide.ticker.nunique()), rows=len(wide), cells=len(long),
                   cells_by_source=by_source, regular=regular_stats, financial=financial_stats, direct_cashflow=direct_stats, dstock=dstock_stats,
                   dstock_fields_accepted=sorted(accepted), checks=checks.check.str.split(':').str[0].value_counts().to_dict(),
                   tickers_by_year=wide.groupby('fiscal_year').ticker.nunique().to_dict())
    manifest = {name: digest((out / name).read_bytes()) for name in sorted(products)}
    manifest['input_pins_sha256'] = digest(pin_body)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    manifest['summary.json'] = digest((out / 'summary.json').read_bytes())
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (ROOT / OUT / 'latest.json').write_text(json.dumps(dict(run_id=run_id, path=out.relative_to(ROOT).as_posix())), encoding='utf-8')
    print(f'{run_id}: {summary["tickers"]} tickers, {summary["rows"]} ticker-years, {summary["cells"]} cells')
    print('dstock fields accepted:', len(accepted), '| checks:', summary['checks'])
    print('output:', out.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
