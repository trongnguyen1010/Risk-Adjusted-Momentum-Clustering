"""Build the annual-report availability table (ticker × fiscal year → usable_from_date) for M3.

Rule (owner, 25/10/2026, D-CRAWL-02 + M3_PLAN Q-dates):
- Fiscal year >= 2022: publication_date = earliest CafeF "Công bố thông tin" CreateDate (Asia/Ho_Chi_Minh date) among
  the audited annual reports (Quarter 5, ReportType HK/K/MK). date_source = CAFEF_DISCLOSURE.
- CafeF re-imported its history on 2022-11-26: every older record carries that date, so it is never used.
- Fiscal year < 2022, or no usable CafeF record: publication_date = 30/06 of the next year. date_source = LAG_RULE.
- usable_from_date = first observed trading session strictly after publication_date (price calendar of the served
  bundle); beyond the calendar end it stays empty with status CALENDAR_PENDING.

Usage: python scripts/build_financial_availability.py --run full-20261025
"""
import argparse
import bisect
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/financial/disclosure_dates_v1'
BUNDLE = ROOT / 'data/web/delta-intelligence-v4/terminal.sqlite'
MIGRATION_DATE = '2022-11-26'
FIRST_CAFEF_YEAR = 2022
ANNUAL_TYPES = {'HK', 'K', 'MK'}
YEARS = range(2016, 2026)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--run', required=True)
    parser.add_argument('--lag', default='06-30', help='MM-DD of the year after the fiscal year (LAG_RULE).')
    args = parser.parse_args()
    run_dir = BASE / args.run
    db = sqlite3.connect(f'file:{BUNDLE}?mode=ro', uri=True)
    tickers = [r[0] for r in db.execute("select distinct ticker from observations where kind='financial' order by 1")]
    calendar = [r[0] for r in db.execute('select distinct date from prices order by 1')]
    state = json.loads((run_dir / 'state.json').read_text(encoding='utf-8'))

    dates = defaultdict(list)
    for path in sorted((run_dir / 'records').glob('*.csv')):
        for r in csv.DictReader(path.open(encoding='utf-8')):
            if r['quarter'] == '5' and r['report_type'] in ANNUAL_TYPES and r['created_date_vn'] != MIGRATION_DATE:
                dates[(r['symbol'], int(r['year']))].append((r['created_date_vn'], r['report_type'], r['id']))

    rows = []
    for ticker in tickers:
        for year in YEARS:
            found = sorted(dates.get((ticker, year), [])) if year >= FIRST_CAFEF_YEAR else []
            if found:
                publication, report_type, report_id = found[0]
                source = 'CAFEF_DISCLOSURE'
            else:
                publication, report_type, report_id = f'{year + 1}-{args.lag}', '', ''
                source = 'LAG_RULE'
            i = bisect.bisect_right(calendar, publication)
            usable = calendar[i] if i < len(calendar) else ''
            rows.append(dict(ticker=ticker, fiscal_year=year, publication_date=publication, date_source=source,
                             report_type=report_type, provider_report_id=report_id, usable_from_date=usable,
                             status='OK' if usable else 'CALENDAR_PENDING',
                             crawl_status=state.get(ticker, 'NOT_CRAWLED')))

    body = ''.join(f'{r}\n' for r in [','.join(rows[0])] + [','.join(str(v) for v in r.values()) for r in rows])
    digest = hashlib.sha256(body.encode()).hexdigest()[:16]
    out = BASE / f'availability-{digest}'
    out.mkdir(exist_ok=True)
    (out / 'availability.csv').write_text(body, encoding='utf-8', newline='\n')

    by_year = {y: Counter(r['date_source'] for r in rows if r['fiscal_year'] == y) for y in YEARS}
    lags = defaultdict(list)
    for r in rows:
        if r['date_source'] == 'CAFEF_DISCLOSURE':
            lags[r['fiscal_year']].append(r['publication_date'][5:])
    summary = dict(
        tickers=len(tickers), crawl=Counter(state.get(t, 'NOT_CRAWLED') for t in tickers),
        by_year={y: dict(c) for y, c in by_year.items()},
        cafef_publication_month_day={y: dict(min=min(v), median=sorted(v)[len(v) // 2], max=max(v),
                                              after_04_30=sum(d > '04-30' for d in v),
                                              after_06_30=sum(d > '06-30' for d in v), n=len(v))
                                     for y, v in sorted(lags.items())},
        calendar_end=calendar[-1], calendar_pending=sum(r['status'] == 'CALENDAR_PENDING' for r in rows))
    manifest = dict(rule=__doc__.split('Usage')[0].strip(), run=args.run, lag=args.lag,
                    bundle_sha256=sha256(BUNDLE), receipts_sha256=sha256(run_dir / 'receipts.jsonl'),
                    output_sha256=hashlib.sha256(body.encode()).hexdigest(), rows=len(rows))
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(out)
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
