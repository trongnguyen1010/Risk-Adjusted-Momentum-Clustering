"""Offline delivery of reported period EPS and explicit six-family coverage.

Copies quoted EPS only after matching its exact raw code, label, period and
value. It does not turn provider observations into independently verified facts,
infer publication dates, manufacture shares, or fit a model.
"""
import argparse
import csv
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = 'data/financial/history_inventory1522_qa_v1/jobs/f837ddd94211f5c4b546'
ARCHIVE = 'artifacts/archives/financial-history-20261023'
FAMILIES = ('EPS', 'PE', 'PB', 'F_SCORE', 'M_SCORE', 'Z_SCORE')


def digest(body):
    return hashlib.sha256(body).hexdigest()


def clean(text):
    text = ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if unicodedata.category(c) != 'Mn').replace('đ', 'd')
    return re.sub(r'\s+', '', text)


def finite(value):
    try:
        n = Decimal(str(value))
        return str(n) if n.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def verify_quoted_eps(payload, observation, symbol, year, quarter, mode, provider, value):
    """Require explicit VND/share label; no monetary multiplier is applied."""
    if payload.get('isSuccess') is not True or mode not in ('NAM','QUY','LUYKE'):
        return False
    if (mode == 'NAM' and quarter != 0) or (mode != 'NAM' and quarter not in (1,2,3,4)):
        return False
    body = payload.get('value', {})
    if body.get('timeType') != mode or body.get('type') != 'KQKD':
        return False
    code = observation.get('raw_code')
    templates = [r for r in body.get('templace', []) if str(r.get('code')) == str(code)]
    if len(templates) != 1 or templates[0].get('name') != observation.get('label'):
        return False
    label = clean(templates[0]['name'])
    if not ('laicobantrencophieu' in label and ('dong/1cophieu' in label or 'dong/cophieu' in label)):
        return False
    matches = []
    for period in body.get('data', []):
        if (period.get('symbol', '').upper(), period.get('year'), period.get('quater'), str(period.get('type'))) != (symbol, year, quarter, provider):
            continue
        cells = [c for c in period.get('data', []) if str(c.get('code')) == str(code)]
        if len(cells) != 1:
            return False
        matches.append(finite(cells[0].get('value')))
    return bool(matches) and all(v == value for v in matches) and value != '-1'


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root):
        raise ValueError('Output must stay inside the workspace')
    if output.exists():
        raise ValueError('Output exists; choose a new immutable version.')
    pins = {}

    def read(relative, expected=None):
        candidates = [root / relative, root / ARCHIVE / relative]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None:
            raise FileNotFoundError(relative)
        if not path.resolve().is_relative_to(root):
            raise ValueError('Path escapes workspace')
        body = path.read_bytes()
        sha = digest(body)
        if expected and sha != expected:
            raise ValueError('Checksum mismatch: ' + relative)
        pins[path.relative_to(root).as_posix()] = sha
        return body

    sm_path = INVENTORY + '/results/b4cf240f4249011a534b/symbol-manifests.json'
    result_manifest = json.loads(read(INVENTORY + '/results/b4cf240f4249011a534b/manifest.json'))
    symbols = json.loads(read(sm_path, result_manifest['symbol-manifests.json']))
    candidates, held = defaultdict(list), Counter()
    report_slots, symbol_names = set(), {}
    raw_cache = {}
    for index, (registry, item) in enumerate(sorted(symbols.items()), 1):
        manifest = json.loads(read(item['path'], item['sha256']))
        folder = str(Path(item['path']).parent).replace('\\', '/')
        inventory=json.loads(read(folder+'/inventory.json',manifest['inventory.json']))
        # Coverage includes missing observations, not only periods with numeric cells.
        for target_year in range(2016,2026):
            report_slots.add((inventory['symbol'],target_year,0,'NAM'))
            for target_quarter in range(1,5):
                report_slots.add((inventory['symbol'],target_year,target_quarter,'QUY'))
        rows = csv.DictReader(io.StringIO(read(folder + '/field-presence.csv', manifest['field-presence.csv']).decode('utf-8-sig')))
        raw_cache.clear()
        for row in rows:
            year, quarter = int(row['year']), int(row['quarter'])
            if not 2016 <= year <= 2025:
                continue
            if (row['mode'] == 'NAM' and quarter != 0) or (row['mode'] != 'NAM' and quarter not in (1,2,3,4)):
                continue
            symbol_names[registry] = row['symbol']
            report_slots.add((row['symbol'], year, quarter, row['mode']))
            if row['field'] != 'vendor_basic_eps':
                continue
            values = json.loads(row['candidate_values'])
            if len(values) != 1 or finite(values[0]) is None:
                held['CONFLICT_OR_INVALID_EPS'] += 1
                continue
            value = finite(values[0])
            evidence = json.loads(row['evidence'])
            ok = bool(evidence)
            for e in evidence:
                key = (e['source_path'], e['source_sha256'])
                if key not in raw_cache:
                    try:
                        raw_cache[key] = json.loads(read(*key), parse_float=Decimal)
                    except FileNotFoundError:
                        raw_cache[key] = None
                raw = raw_cache[key]
                if raw is None or not verify_quoted_eps(raw, e, row['symbol'], year, quarter, row['mode'], row['provider_type'], value):
                    ok = False
                    break
            if not ok:
                held['RAW_PERIOD_LABEL_OR_VALUE_NOT_CONFIRMED'] += 1
                continue
            candidates[row['symbol'], year, quarter, row['mode']].append(dict(value=value, provider=row['provider_type'], evidence=evidence))
        if index % 100 == 0:
            print(f'Checked {index}/{len(symbols)} symbols', flush=True)
    metrics, coverage = [], []
    for symbol, year, quarter, mode in sorted(report_slots):
        observations = candidates.get((symbol, year, quarter, mode), [])
        values = {r['value'] for r in observations}
        value = next(iter(values)) if len(values) == 1 else None
        period = 'ANNUAL' if mode == 'NAM' and quarter == 0 else 'QUARTER_REPORTED' if mode == 'QUY' else f'YTD{quarter * 3}'
        if period == 'ANNUAL' and quarter != 0:
            continue
        cohort = f'CAFEF_REPORTED:{symbol}:{year}:{quarter}:{mode}'
        status = 'PROVIDER_REPORTED' if value is not None else 'CONFLICTING_PROVIDER_VALUES' if values else 'MISSING_CONFIRMED_EPS'
        if value is not None:
            metrics.append(dict(symbol=symbol, year=year, family='EPS', value=value, status=status,
                cohort_id=cohort, variant='SOURCE_REPORTED_BASIC_EPS', unit='VND/share', period_kind=period,
                quarter=quarter, input_period=f'{year}' if quarter == 0 else f'{year}-Q{quarter}',
                input_scope='CAFEF_REPORTED_NOT_INDEPENDENT_STATEMENT_VALIDATION',
                price_date='', snapshot_date='', balance_date='', price_basis='', share_basis='SOURCE_REPORTED_BASIC_EPS',
                evidence_ref=json.dumps(observations, ensure_ascii=False, default=str),
                strict_pit_ready=False, production_ready=False))
        for family in FAMILIES:
            reason = status if family == 'EPS' else {
                'PE': 'NEEDS_ELIGIBLE_DATED_PRICE_AND_EPS_SHARE_BASIS',
                'PB': 'NEEDS_PARENT_BOOK_EQUITY_COMMON_SHARES_AND_DATED_PRICE',
                'F_SCORE': 'NEEDS_ALL_NINE_SIGNALS_AND_PARENT_ISSUANCE_PROOF',
                'M_SCORE': 'NEEDS_EXACT_RECEIVABLES_AND_OWNED_PPE_DEPRECIATION_BASIS',
                'Z_SCORE': 'NEEDS_ACCEPTED_EBIT_UNIT_SCOPE_AND_MODEL_APPLICABILITY',
            }[family]
            coverage.append(dict(symbol=symbol, year=year, quarter=quarter, mode=mode, family=family,
                                 value=value if family == 'EPS' else None, status=reason))
    output.mkdir(parents=True)
    def write_csv(name, rows):
        if not rows:
            raise ValueError('No rows for ' + name)
        with (output/name).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)
    write_csv('reported-eps.csv', metrics)
    write_csv('coverage.csv', coverage)
    # Serve only the selected ticker; never load 53k evidence payloads per API request.
    db = sqlite3.connect(output/'reported-eps.sqlite')
    db.executescript('CREATE TABLE observations(symbol TEXT,year INTEGER,payload TEXT); CREATE INDEX by_symbol ON observations(symbol,year); CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);')
    db.executemany('INSERT INTO observations VALUES(?,?,?)', [(r['symbol'],r['year'],json.dumps(r,ensure_ascii=False)) for r in metrics])
    summary = dict(version='financial-serving-v1', symbols_scanned=len(symbols),
        symbols_with_reported_eps=len({r['symbol'] for r in metrics}), numeric_reported_eps=len(metrics),
        annual_eps=sum(r['period_kind'] == 'ANNUAL' for r in metrics),
        nonannual_eps=sum(r['period_kind'] != 'ANNUAL' for r in metrics),
        report_slots=len(report_slots), coverage_cells=len(coverage), held=dict(held),
        calculated_scores_added=0, explanation='Quoted source EPS, not newly calculated EPS or verified six-family scores. No filled values.',
        strict_pit_ready=False, research_ready=False)
    db.execute('INSERT INTO metadata VALUES(?,?)', ('summary',json.dumps(summary)))
    db.commit();db.close()
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    pins['scripts/build_financial_serving.py'] = digest(Path(__file__).read_bytes())
    (output/'input-pins.json').write_text(json.dumps(pins, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {p.name:digest(p.read_bytes()) for p in output.iterdir() if p.is_file()}
    (output/'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='data/financial/financial_serving_v1/results/source-period-eps-v1')
    args = parser.parse_args()
    build(ROOT, ROOT/args.output)
