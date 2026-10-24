"""Descriptive A/B review and ex-post common-cohort inputs; no fit or network."""
import csv
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from .market_financial_integration import MARKET, HANDOFF, inside, sha, keyed
from .financial_full10_baseline import extract_values, compare_ratios

FINANCIAL = 'data/financial/financial_full10_baseline_v1/results/4d521e71139a48340d3d'
FEATURES_M = ['mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21']
FEATURES_F = ['gross_margin', 'net_margin', 'liabilities_to_assets', 'current_ratio',
              'operating_cashflow_to_assets', 'asset_turnover_ending_assets']
RATIO_INPUTS = dict(gross_margin=('gross_profit', 'net_revenue'), net_margin=('net_profit', 'net_revenue'),
                    liabilities_to_assets=('total_liabilities', 'total_assets'),
                    current_ratio=('current_assets', 'current_liabilities'),
                    operating_cashflow_to_assets=('operating_cash_flow', 'total_assets'),
                    asset_turnover_ending_assets=('net_revenue', 'total_assets'))


def csv_bytes(items):
    if not items:
        return b''
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(items[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(items)
    return stream.getvalue().encode('utf-8')


def separation_drivers(profiles, scalers, features):
    total = sum(int(p['size']) for p in profiles)
    scores = {}
    for f in features:
        center = sum(int(p['size']) * float(p['means'][f]) for p in profiles) / total
        scores[f] = sum(int(p['size']) * ((float(p['means'][f]) - center) / scalers[f]['scale'])**2
                        for p in profiles)
    denom = sum(scores.values())
    return {f: value / denom if denom else 0 for f, value in scores.items()}


def reference_join(market, financial, dates):
    """Fiscal-year/December association; explicitly forbidden as a trading snapshot."""
    m = keyed(market, ('snapshot_date', 'ticker'))
    f = keyed(financial, ('year', 'symbol'))
    result = []
    for day in dates:
        year = day[:4]
        symbols = sorted({t for d, t in m if d == day} | {t for y, t in f if y == year})
        for symbol in symbols:
            a, b = m.get((day, symbol)), f.get((year, symbol))
            result.append(dict(snapshot_date=day, fiscal_year=year, symbol=symbol,
                market_security_id=a['security_id'] if a else '',
                market_cluster_id=a['cluster_label'] if a else '',
                financial_registry_id=b['registry_id'] if b else '',
                financial_cluster_id=b['cluster_id'] if b else '',
                coverage='BOTH' if a and b else 'MARKET_ONLY' if a else 'FINANCIAL_ONLY',
                join_scope='EX_POST_FISCAL_YEAR_REFERENCE_NOT_PIT', research_ready=False))
    return result


def build(root):
    root = Path(root).resolve()
    pins = {}
    financial_pins = json.loads((root / FINANCIAL / 'input-pins.json').read_bytes())

    def body(relative, expected=None):
        path = inside(root, relative)
        digest = sha(path)
        wanted = expected or financial_pins.get(relative)
        if wanted and digest != wanted:
            raise ValueError('input hash changed: ' + relative)
        if relative in pins and pins[relative] != digest:
            raise ValueError('input changed while reviewing: ' + relative)
        pins[relative] = digest
        return path.read_bytes()

    def load(relative, expected=None):
        return json.loads(body(relative, expected))

    def table(relative, expected=None):
        return list(csv.DictReader(io.StringIO(body(relative, expected).decode('utf-8-sig'))))

    fm = load(FINANCIAL + '/manifest.json')
    ff = table(FINANCIAL + '/features.csv', fm['features.csv'])
    fa = table(FINANCIAL + '/assignments.csv', fm['assignments.csv'])
    snapshots = load(FINANCIAL + '/snapshots.json', fm['snapshots.json'])
    financial_by_key = keyed(ff, ('registry_id', 'year'))
    financial_labels = keyed(fa, ('registry_id', 'year'))
    if set(financial_by_key) != set(financial_labels):
        raise ValueError('financial feature/assignment keys differ')
    mm = load(MARKET + '/manifest.json')
    hm = load(HANDOFF + '/m2_to_m3_handoff_manifest.json')
    labels = table(HANDOFF + '/m2_cluster_labels_for_m3.csv', hm['artifacts_sha256']['m2_cluster_labels_for_m3.csv'])
    mp = table(HANDOFF + '/m2_cluster_profiles_for_m3.csv', hm['artifacts_sha256']['m2_cluster_profiles_for_m3.csv'])
    mp = [p for p in mp if not p['snapshot_date'].startswith('MEDIAN_')]
    days = sorted({r['snapshot_date'] for r in labels})
    december = [d for d in days if d[5:7] == '12']
    joined = reference_join(labels, fa, december)
    overlap = Counter(r['snapshot_date'] for r in joined if r['coverage'] == 'BOTH')
    members = {(r['snapshot_date'], r['market_security_id']): r for r in joined if r['coverage'] == 'BOTH'}
    combined = []
    feature_path = MARKET + '/canonical/feature_snapshots.jsonl'
    actual = sha(root / feature_path)
    if actual != mm['outputs']['canonical/feature_snapshots.jsonl']:
        raise ValueError('market features hash mismatch')
    pins[feature_path] = actual
    with (root / feature_path).open(encoding='utf-8') as stream:
        for line in stream:
            r = json.loads(line)
            key = r['as_of_date'], r['security_id']
            if key not in members:
                continue
            if not r.get('market_feature_ready_v2', r.get('market_feature_ready')):
                raise ValueError('joined market row is not eligible')
            j = members.pop(key)
            f = financial_by_key[j['financial_registry_id'], j['fiscal_year']]
            if r['ticker'] != j['symbol'] or f['symbol'] != j['symbol']:
                raise ValueError('crosswalk ticker mismatch')
            combined.append(dict(j, **{name: float(r[name]) for name in FEATURES_M},
                                  **{name: float(f[name]) for name in FEATURES_F},
                                  financial_source_evidence=f['source_evidence'],
                                  financial_published_at=f.get('published_at', ''),
                                  strict_pit_ready=False))
    if members or Counter(r['snapshot_date'] for r in combined) != overlap:
        raise ValueError('common-cohort feature rows missing or duplicated')
    combined.sort(key=lambda r: (r['snapshot_date'], r['symbol']))
    catalog, drivers = [], []
    for day in days:
        profiles = [dict(size=int(p['size']), means={f: float(p[f]) for f in FEATURES_M},
                         cluster_id=p['cluster_label']) for p in mp if p['snapshot_date'] == day]
        model_path = ('M2/models/final_selected_model_v2/' if day[:4] < '2024' else 'M2/models/holdout/') + day + '.json'
        model = load(model_path)
        shares = separation_drivers(profiles, model['scaler'], FEATURES_M)
        for feature, share in shares.items():
            drivers.append(dict(data_type='MARKET', snapshot=day, feature=feature, separation_share=share))
        for p in profiles:
            catalog.append(dict(data_type='MARKET', snapshot=day, cluster_id=p['cluster_id'],
                                size=p['size'], feature_means_json=json.dumps(p['means'], sort_keys=True),
                                source=HANDOFF + '/m2_cluster_profiles_for_m3.csv'))
    for year, model in sorted(snapshots.items()):
        shares = separation_drivers(model['profiles'], model['scaler'], FEATURES_F)
        for feature, share in shares.items():
            drivers.append(dict(data_type='FINANCIAL', snapshot=year, feature=feature, separation_share=share))
        for p in model['profiles']:
            catalog.append(dict(data_type='FINANCIAL', snapshot=year, cluster_id=p['cluster_id'],
                                size=p['size'], feature_means_json=json.dumps(p['means'], sort_keys=True),
                                source=FINANCIAL + '/snapshots.json'))
    queue = table('artifacts/reports/financial-full10-baseline-v1/outlier-review.csv')
    cache, inputs, reviewed = {}, {}, []

    def cached(relative, expected=None):
        if relative not in cache:
            cache[relative] = load(relative, expected)
        elif expected and pins[relative] != expected:
            raise ValueError('cached evidence pin mismatch')
        return cache[relative]

    for item in queue:
        key = item['registry_id'], item['year']
        row = financial_by_key[key]
        if key not in inputs:
            inputs[key] = extract_values(row, cached, body)
            compare_ratios(row, inputs[key])
        v = inputs[key]
        numerator, denominator = RATIO_INPUTS[item['field']]
        flags = []
        if float(v['total_liabilities']) > float(v['total_assets']):
            flags.append('LIABILITIES_EXCEED_ASSETS_IN_SELECTED_INPUTS')
        if float(v['net_revenue']) / float(v['total_assets']) < .01:
            flags.append('REVENUE_BELOW_1_PERCENT_ASSETS_DIAGNOSTIC_ONLY')
        reviewed.append(dict(symbol=row['symbol'], year=row['year'], field=item['field'],
            numerator_field=numerator, numerator=v[numerator], denominator_field=denominator,
            denominator=v[denominator], ratio=row[item['field']], original_zscore=item['zscore'],
            source_kind=row['source_kind'] or 'CAFEF_API_SELECTED_PARTITION',
            source_evidence=row['source_evidence'], declared_scope=row.get('scope', ''),
            declared_unit=row.get('unit', ''), published_at=row.get('published_at', ''),
            diagnostics=';'.join(flags), arithmetic_replay='PASS',
            source_fact_verdict='NOT_INDEPENDENTLY_REVALIDATED_WITH_ORIGINAL_STATEMENT'))
    contingency = Counter((r['snapshot_date'], r['market_cluster_id'], r['financial_cluster_id'])
                          for r in joined if r['coverage'] == 'BOTH')
    counts = [dict(snapshot_date=d, market_cluster_id=m, financial_cluster_id=f, count=n,
                   common_cohort_n=overlap[d]) for (d, m, f), n in sorted(contingency.items())]
    market_liquidity = [r['separation_share'] for r in drivers if r['data_type'] == 'MARKET' and r['feature'] == 'liquidity_21']
    summary = dict(status='COMPLETE_DESCRIPTIVE_A_B_REVIEW', quality_status='REVIEW_REQUIRED',
        market_cluster_count=sum(r['data_type'] == 'MARKET' for r in catalog),
        financial_cluster_count=sum(r['data_type'] == 'FINANCIAL' for r in catalog),
        common_cohort_by_year_end=dict(sorted(overlap.items())),
        market_liquidity_separation_share_median=median(market_liquidity),
        financial_outlier_rows_replayed=len(reviewed), financial_unique_vectors_replayed=len(inputs),
        financial_rows_with_publication=sum(bool(r.get('published_at')) for r in ff),
        financial_rows_total=len(ff), combined_reference_rows=len(combined),
        model_refits=0, new_network_requests=0, new_pdf_downloads=0, strict_pit_ready=False,
        combined_historical_model_allowed=False,
        non_claim='DECEMBER_MARKET_AND_SAME_FISCAL_YEAR_FINANCIAL_ARE_EX_POST_REFERENCE_NOT_INVESTABLE')
    tables = {'cluster-catalog.csv': catalog, 'dual-memberships-year-end.csv': joined,
              'contingency-year-end.csv': counts, 'separation-drivers.csv': drivers,
              'financial-outlier-input-review.csv': reviewed, 'combined-input-reference.csv': combined}
    return summary, tables, pins


def run(root, output='artifacts/reports/dual-cluster-review-v1'):
    summary, tables, pins = build(root)
    payloads = {name: csv_bytes(items) for name, items in tables.items()}
    payloads.update({'summary.json': (json.dumps(summary, indent=2, sort_keys=True)+'\n').encode(),
                     'input-pins.json': (json.dumps(pins, indent=2, sort_keys=True)+'\n').encode()})
    target = inside(root, output)
    if target.exists():
        for name, data in payloads.items():
            if (target / name).read_bytes() != data:
                raise ValueError('existing review differs; use a new version: ' + name)
        return target, summary
    target.mkdir(parents=True)
    for name, data in payloads.items():
        (target / name).write_bytes(data)
    (target / 'manifest.json').write_bytes((json.dumps({p: sha(target/p) for p in payloads},indent=2,sort_keys=True)+'\n').encode())
    return target, summary
