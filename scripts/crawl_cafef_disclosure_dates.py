"""Crawl CafeF "Công bố thông tin" listings to get the submission date (CreateDate) of each financial report.

D-CRAWL-02: raw pages + receipts + sha256 are kept; 403/429/5xx/timeouts retry 3 times with backoff
(30 s, 2 min, 10 min), then the symbol is marked DEFERRED and the run moves on. CAPTCHA/JS challenges stop the
symbol (no bypass). Output: data/financial/disclosure_dates_v1/<run_id>/.

Usage:
  python scripts/crawl_cafef_disclosure_dates.py --symbols FPT,BRC,PVS --run-id smoke20
  python scripts/crawl_cafef_disclosure_dates.py --symbols-file tickers.txt --run-id full --resume
"""
import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/financial/disclosure_dates_v1'
URL = ('https://cafef.vn/du-lieu/ajax/ajaxcongbothongtin.ashx'
       '?symbol={symbol}&pageindex={page}&pagesize={size}&reporttype=&startdate=&enddate=&center=0')
HEADERS = {'User-Agent': 'Mozilla/5.0 (DELTA research crawler)',
           'Referer': 'https://cafef.vn/du-lieu/cong-bo-thong-tin.chn'}
BACKOFF = (30, 120, 600)
VN = timezone(timedelta(hours=7))
RETRYABLE = {403, 429, 500, 502, 503, 504}


def fetch(url):
    """Return (status, body bytes, error); retries per D-CRAWL-02."""
    for attempt in range(len(BACKOFF) + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return r.status, r.read(), None
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE or attempt == len(BACKOFF):
                return e.code, e.read() if hasattr(e, 'read') else b'', f'HTTP {e.code}'
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == len(BACKOFF):
                return None, b'', repr(e)
        time.sleep(BACKOFF[attempt])
    return None, b'', 'unreachable'


def parse_date(raw):
    """'/Date(1787381335736)/' -> (utc iso, Asia/Ho_Chi_Minh date)."""
    m = re.fullmatch(r'/Date\((-?\d+)\)/', raw or '')
    if not m:
        return None, None
    moment = datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc)
    return moment.isoformat(), moment.astimezone(VN).date().isoformat()


def crawl_symbol(symbol, run_dir, size, delay):
    raw_dir = run_dir / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    receipts, rows, page = [], [], 1
    while True:
        url = URL.format(symbol=symbol, page=page, size=size)
        status, body, error = fetch(url)
        sha = hashlib.sha256(body).hexdigest()
        if body:
            (raw_dir / f'{sha}.json').write_bytes(body)
        receipt = dict(symbol=symbol, page=page, url=url, http_status=status, sha256=sha, bytes=len(body),
                       fetched_at=datetime.now(timezone.utc).isoformat(), error=error)
        try:
            payload = json.loads(body.decode('utf-8-sig')) if status == 200 else None
        except ValueError:
            payload = None
        if payload is None:
            challenge = b'captcha' in body.lower() or b'<html' in body[:200].lower()
            receipt['status'] = 'CHALLENGE_STOPPED' if challenge else 'DEFERRED'
            receipts.append(receipt)
            return receipt['status'], receipts, rows
        items = (payload.get('Data') or {}).get('BctcList') or []
        total = (payload.get('Data') or {}).get('Count')
        receipt.update(status='ACQUIRED', items=len(items), count=total)
        receipts.append(receipt)
        for item in items:
            utc, day = parse_date(item.get('CreateDate'))
            rows.append(dict(symbol=symbol, id=item.get('Id'), year=item.get('Year'), quarter=item.get('Quarter'),
                             report_type=item.get('ReportType'), type=item.get('Type'), content=item.get('Content'),
                             link_file=item.get('LinkFile'), create_date_raw=item.get('CreateDate'),
                             created_at_utc=utc, created_date_vn=day, raw_sha256=sha))
        if not items or (isinstance(total, int) and page * size >= total):
            return 'DONE', receipts, rows
        page += 1
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--symbols', default='')
    parser.add_argument('--symbols-file')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--page-size', type=int, default=100)
    parser.add_argument('--delay', type=float, default=0.5)
    parser.add_argument('--resume', action='store_true', help='Skip symbols already DONE in this run.')
    args = parser.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
    if args.symbols_file:
        symbols += [s.strip().upper() for s in Path(args.symbols_file).read_text(encoding='utf-8').split() if s.strip()]
    run_dir = OUT / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / 'state.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.is_file() else {}
    for symbol in dict.fromkeys(symbols):
        if args.resume and state.get(symbol) == 'DONE':
            continue
        status, receipts, rows = crawl_symbol(symbol, run_dir, args.page_size, args.delay)
        with (run_dir / 'receipts.jsonl').open('a', encoding='utf-8') as f:
            for r in receipts:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        path = run_dir / 'records' / f'{symbol}.csv'
        path.parent.mkdir(exist_ok=True)
        if rows:
            with path.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        state[symbol] = status
        state_path.write_text(json.dumps(state, indent=1), encoding='utf-8')
        print(f'{symbol:5} {status:18} pages={len(receipts)} records={len(rows)}', flush=True)
        time.sleep(args.delay)
    summary = {s: v for s, v in state.items()}
    print(json.dumps({'done': sum(v == 'DONE' for v in summary.values()), 'other': {k: v for k, v in summary.items() if v != 'DONE'}}))


if __name__ == '__main__':
    main()
