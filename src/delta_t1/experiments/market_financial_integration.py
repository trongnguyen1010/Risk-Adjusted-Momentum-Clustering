"""Offline verification and reference-only handoff; never fit or backtest."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

MARKET = 'artifacts/cafef_primary/cafef-c8-complete-only-v2'
HANDOFF = 'M2/artifacts/m2-final-handoff-v1'
OUTPUT = 'M2/artifacts/market-financial-integration-v1'


def inside(root, relative):
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('path outside repository: ' + relative)
    return path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(root, relative):
    return json.loads(inside(root, relative).read_text(encoding='utf-8-sig'))


def rows(root, relative):
    with inside(root, relative).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check_hashes(root, mapping, prefix=''):
    for relative, expected in mapping.items():
        if sha(inside(root, prefix + relative)) != expected:
            raise ValueError('checksum mismatch: ' + prefix + relative)
    return len(mapping)


def keyed(items, fields):
    result = {}
    for row in items:
        key = tuple(row[f] for f in fields)
        if key in result:
            raise ValueError('duplicate key: ' + repr(key))
        result[key] = row
    return result


def verify(root):
    """Verify exact bytes, current assignments and per-snapshot input eligibility."""
    root = Path(root).resolve()
    source = read(root, MARKET + '/manifest.json')
    n_market = check_hashes(root, source['outputs'], MARKET + '/')
    cfg = read(root, 'configs/experiments/m2_final_holdout.json')
    n_pins = check_hashes(root, cfg['frozen_inputs_sha256'])
    protocol = read(root, cfg['protocol_path'])
    dev, hold = protocol['development_snapshots'], protocol['holdout_snapshots']
    if len(dev) != 60 or len(hold) != 24 or max(dev) >= min(hold):
        raise ValueError('expected disjoint ordered 60+24 snapshots')
    decision = read(root, cfg['decision_path'])
    lineage = decision['source_lineage']['KMeans_Baseline']
    if (sha(root / MARKET / 'manifest.json') != lineage['c8_manifest_sha256']
            or source['outputs']['canonical/feature_snapshots.jsonl'] != lineage['c8_feature_sha256']):
        raise ValueError('C8 lineage mismatch')
    hold_manifest = read(root, cfg['output_dir'] + '/manifest.json')
    n_outputs = check_hashes(root, hold_manifest['artifacts'])
    if hold_manifest['portfolio_evaluation_enabled'] or hold_manifest['global_k'] != 2:
        raise ValueError('frozen market-only boundary changed')
    models = {}
    model_pins = {}
    index = read(root, cfg['selected_models_manifest_path'])
    folder = str(Path(cfg['selected_models_manifest_path']).parent).replace('\\', '/')
    for item in index['files']:
        model_pins[folder + '/' + item['name']] = item['sha256']
    for day in hold:
        path = cfg['model_dir'] + '/' + day + '.json'
        model_pins[path] = hold_manifest['artifacts'][path]
    check_hashes(root, model_pins)
    for path in model_pins:
        models[Path(path).stem] = read(root, path)
    if set(models) != set(dev + hold):
        raise ValueError('expected exactly 84 models')
    handoff = read(root, HANDOFF + '/m2_to_m3_handoff_manifest.json')
    csv_pins = {p: h for p, h in handoff['artifacts_sha256'].items() if p.endswith('.csv')}
    check_hashes(root, csv_pins, HANDOFF + '/')
    assembled = read(root, 'M2/models/final_selected_model/model_file_manifest.json')
    check_hashes(root, assembled['model_files_sha256'], 'M2/models/final_selected_model/')
    check_hashes(root, {'M2/models/final_selected_model/model_file_manifest.json':
                       handoff['artifacts_sha256']['final_selected_models_manifest']})
    labels = keyed(rows(root, HANDOFF + '/m2_cluster_labels_for_m3.csv'),
                   ('snapshot_date', 'security_id'))
    actual = {}
    raw_assignments = {}
    for relative, period in [('M2/artifacts/m2-evaluation-kmeans/cluster_profile_members.csv', 'development'),
                             (cfg['output_dir'] + '/assignments.csv', 'holdout')]:
        for key, row in keyed(rows(root, relative), ('snapshot_date', 'security_id')).items():
            actual[key] = (row['aligned_cluster_id'], period)
    for relative in ['M2/artifacts/m2-task4-kmeans-baseline-v1/assignments.csv',
                     cfg['output_dir'] + '/assignments.csv']:
        raw_assignments.update(keyed(rows(root, relative), ('snapshot_date', 'security_id')))
    if set(labels) != set(actual) or set(labels) != set(raw_assignments):
        raise ValueError('handoff/source membership keys differ')
    for key, row in labels.items():
        if (row['cluster_label'], row['membership_period']) != actual[key]:
            raise ValueError('aligned label mismatch: ' + repr(key))
    financial_path = 'data/handoffs/financial-reference-2016-2025/securities-1172-symbols.csv'
    financial = {r['symbol']: r['registry_id'] for r in rows(root, financial_path)}
    if len(financial) != 1172:
        raise ValueError('financial full10 cohort size changed')
    feature_keys, overlap, member_counts = set(), Counter(), Counter()
    identity_ready = research_ready = 0
    with (root / MARKET / 'canonical/feature_snapshots.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            day = row['as_of_date']
            identity_ready += bool(row.get('historical_identity_ready'))
            research_ready += bool(row.get('research_ready'))
            if day not in models or not row.get('market_feature_ready_v2', row.get('market_feature_ready')):
                continue
            key = day, row['security_id']
            if key in feature_keys:
                raise ValueError('duplicate eligible feature key')
            feature_keys.add(key)
            if key not in labels:
                raise ValueError('eligible feature lacks assignment')
            if row['ticker'] != labels[key]['ticker'] or row['available_at'][:10] > day:
                raise ValueError('ticker/availability mismatch')
            model = models[day]
            vector = []
            feature_order = model.get('feature_order') or model['config']['features']
            for feature in feature_order:
                value = float(row[feature])
                scaler = model['scaler'][feature]
                if not math.isfinite(value):
                    raise ValueError('nonfinite eligible feature')
                vector.append((value - scaler['center']) / scaler['scale'])
            centroids = model.get('centroids_scaled') or model['centroids']
            distances = [sum((a-b)**2 for a, b in zip(vector, c)) for c in centroids]
            assigned = int(raw_assignments[key]['raw_cluster_id'])
            if distances[assigned] > min(distances) + 1e-8 * max(1, min(distances)):
                raise ValueError('not nearest centroid: ' + repr(key))
            member_counts[day] += 1
            overlap[day] += row['ticker'] in financial
    if feature_keys != set(labels):
        raise ValueError('assignment without eligible source feature')
    if identity_ready or research_ready:
        raise ValueError('reference-only gates changed')
    stats = {}
    for period, relative in [('development', 'M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv'),
                             ('holdout', cfg['output_dir'] + '/diagnostics.csv')]:
        diagnostics = rows(root, relative)
        sizes = [min(json.loads(r['cluster_sizes']).values()) for r in diagnostics]
        stats[period] = dict(snapshots=len(diagnostics), median_silhouette=median(float(r['silhouette']) for r in diagnostics),
                            median_cluster_balance=median(float(r['cluster_balance']) for r in diagnostics),
                            smallest_cluster_min=min(sizes), smallest_cluster_median=median(sizes),
                            snapshots_with_cluster_below_10=sum(n < 10 for n in sizes))
    return dict(version='market-financial-integration-v1', technical_status='PASS',
                quality_status='REVIEW_REQUIRED', strict_pit_ready=False, research_ready=False,
                model_refitted=False, market_outputs_verified=n_market, holdout_outputs_verified=n_outputs,
                frozen_input_pins_verified=n_pins, models_verified=len(models), assignments_verified=len(labels),
                model_pins=model_pins, source_manifest_sha256=sha(root / MARKET / 'manifest.json'),
                financial_cohort_sha256=sha(root / financial_path),
                overlap_by_snapshot=dict(sorted(overlap.items())), counts_by_snapshot=dict(sorted(member_counts.items())),
                statistics=stats, join_scope='TICKER_REFERENCE_ONLY_NOT_HISTORICAL_IDENTITY_OR_PIT')


def publish(root, result, output=OUTPUT):
    """Write a new immutable reference handoff, linking existing numeric artifacts."""
    target = inside(root, output)
    payload = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
    manifest = dict(version=result['version'], verification_sha256=hashlib.sha256(payload).hexdigest(),
                    model_pins=result['model_pins'], labels_reference=HANDOFF + '/m2_cluster_labels_for_m3.csv',
                    labels_sha256=sha(Path(root) / HANDOFF / 'm2_cluster_labels_for_m3.csv'),
                    quality_status='REVIEW_REQUIRED', strict_pit_ready=False, model_refitted=False)
    # V1 was sealed on Windows; preserve its explicit CRLF manifest on every OS.
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').replace('\n', '\r\n').encode('utf-8')
    if target.exists():
        if ((target / 'verification.json').read_bytes() != payload
                or (target / 'manifest.json').read_bytes() != manifest_bytes):
            raise ValueError('existing output differs; use a new version')
        return target
    target.mkdir(parents=True)
    (target / 'verification.json').write_bytes(payload)
    (target / 'manifest.json').write_bytes(manifest_bytes)
    return target
