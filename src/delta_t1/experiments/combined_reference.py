"""Owner-gated annual joint reference model; separate from historical M2/M3."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev

from .dual_cluster_review import FEATURES_M, FEATURES_F, csv_bytes
from .market_financial_integration import inside, sha, check_hashes, rows


def validate(config, execute=False):
    expected = dict(version='combined-reference-v1', mode='EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT',
                    k=3, seed=42, n_init=20, max_iter=300, minimum_common_cohort=100,
                    scaling='PER_YEAR_COMMON_COHORT_ZSCORE', block_weights={'market': .5, 'financial': .5},
                    clipping=False, pca=False, imputation=False, strict_pit_ready=False,
                    research_ready=False, backtest_allowed=False, holdout_claim=False)
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError('unsupported/reference boundary changed: ' + key)
    if config['market_features'] != FEATURES_M or config['financial_features'] != FEATURES_F:
        raise ValueError('joint feature contract changed')
    if config['years'] != list(range(2019, 2026)):
        raise ValueError('expected 2019–2025 descriptive years')
    if execute and config.get('owner_approval', {}).get('status') != 'APPROVED':
        raise ValueError('MANUAL_REVIEW_REQUIRED: owner must approve the concrete protocol before execution')


def transform(group, config):
    fields = config['market_features'] + config['financial_features']
    matrix = [[] for _ in group]
    scalers = {}
    for f in fields:
        values = [float(r[f]) for r in group]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('nonfinite/missing joint feature')
        family = 'market' if f in config['market_features'] else 'financial'
        count = len(config[family + '_features'])
        weight = math.sqrt(config['block_weights'][family] / count)
        center, scale = mean(values), pstdev(values) or 1
        scalers[f] = dict(center=center, scale=scale, weight=weight, family=family,
                          fit_scope='THIS_YEAR_COMMON_COHORT_ONLY')
        for vector, value in zip(matrix, values):
            vector.append((value-center)/scale * weight)
    return matrix, scalers


def fit_one_year(group, config):
    """Used by bounded synthetic tests; real entry point enforces owner approval."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
    if len({r['snapshot_date'] for r in group}) != 1:
        raise ValueError('one annual snapshot required')
    if len(group) < config['minimum_common_cohort']:
        raise ValueError('common cohort below approved minimum')
    group = sorted(group, key=lambda r: r['symbol'])
    if len({r['symbol'] for r in group}) != len(group):
        raise ValueError('duplicate joint symbol')
    matrix, scalers = transform(group, config)
    model = KMeans(n_clusters=config['k'], random_state=config['seed'],
                   n_init=config['n_init'], max_iter=config['max_iter']).fit(matrix)
    labels = model.labels_.tolist()
    sizes = Counter(labels)
    if len(sizes) != config['k'] or model.n_iter_ >= config['max_iter']:
        raise ValueError('joint K-Means did not verify convergence/distinct clusters')
    fields = config['market_features'] + config['financial_features']
    profiles = []
    for label in range(config['k']):
        selected = [r for r, c in zip(group, labels) if c == label]
        profiles.append(dict(cluster_id=label, size=len(selected),
                             means={f: mean(float(r[f]) for r in selected) for f in fields}))
    metrics = dict(n=len(group), k=config['k'], inertia=float(model.inertia_),
                   silhouette=float(silhouette_score(matrix, labels)),
                   davies_bouldin=float(davies_bouldin_score(matrix, labels)),
                   calinski_harabasz=float(calinski_harabasz_score(matrix, labels)),
                   min_cluster_size=min(sizes.values()), cluster_balance=min(sizes.values())/max(sizes.values()),
                   iterations=int(model.n_iter_), converged=True)
    metrics['quality_status'] = ('REVIEW_REQUIRED' if metrics['min_cluster_size'] < 10
                                 or metrics['cluster_balance'] < .05 else 'REVIEW_REQUIRED_INTERPRETATION')
    return dict(scalers=scalers, centroids=model.cluster_centers_.tolist(), profiles=profiles,
                feature_order=fields, metrics=metrics,
                assignments=[dict(r, combined_cluster_id=c, combined_label_scope='THIS_YEAR_ONLY')
                             for r, c in zip(group, labels)])


def preflight(root, config_path, execute=False):
    root = Path(root).resolve()
    config = json.loads(inside(root, config_path).read_bytes())
    validate(config, execute=execute)
    review = config['input_review']
    base = inside(root, review['path'])
    if sha(base / 'manifest.json') != review['manifest_sha256']:
        raise ValueError('review manifest hash changed')
    manifest = json.loads((base / 'manifest.json').read_bytes())
    if sha(base / 'combined-input-reference.csv') != manifest['combined-input-reference.csv']:
        raise ValueError('combined reference inputs changed')
    pins = json.loads((base / 'input-pins.json').read_bytes())
    if sha(base / 'input-pins.json') != manifest['input-pins.json']:
        raise ValueError('review pins changed')
    check_hashes(root, pins)
    data = rows(root, review['path'] + '/combined-input-reference.csv')
    counts = Counter(r['fiscal_year'] for r in data)
    if set(counts) != {str(y) for y in config['years']} or min(counts.values()) < config['minimum_common_cohort']:
        raise ValueError('joint annual cohort missing/below minimum')
    if any(r['strict_pit_ready'].lower() != 'false' or r['research_ready'].lower() != 'false'
           or r['join_scope'] != 'EX_POST_FISCAL_YEAR_REFERENCE_NOT_PIT' for r in data):
        raise ValueError('reference input gates changed')
    return config, data, counts


def run(root, config_path, execute=False):
    config, data, counts = preflight(root, config_path, execute=execute)
    if not execute:
        return dict(status='PREPARED_NOT_FITTED', owner_approval=config['owner_approval'], counts=dict(counts))
    root = Path(root).resolve()
    code = ['src/delta_t1/experiments/combined_reference.py',
            'src/delta_t1/experiments/dual_cluster_review.py', 'scripts/combined_reference.py']
    pins = {p: sha(inside(root, p)) for p in code + [config_path]}
    pins[config['input_review']['path'] + '/manifest.json'] = config['input_review']['manifest_sha256']
    identity = hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()[:20]
    target = inside(root, 'data/experiments/combined_reference_v1/results/' + identity)
    if target.exists():
        check_hashes(target, json.loads((target/'manifest.json').read_bytes()))
        return json.loads((target/'summary.json').read_bytes())
    snapshots, assignments, metrics = {}, [], []
    for year in config['years']:
        fitted = fit_one_year([r for r in data if int(r['fiscal_year']) == year], config)
        assignments.extend(fitted.pop('assignments'))
        snapshots[str(year)] = fitted
        metrics.append(dict(year=year, **fitted['metrics']))
    summary = dict(status='COMPLETE_DESCRIPTIVE_COMBINED_REFERENCE', run_id=identity,
                   result_path=str(target.relative_to(root)).replace('\\', '/'), counts=dict(counts),
                   snapshots=len(snapshots), assignments=len(assignments),
                   quality_status='REVIEW_REQUIRED', strict_pit_ready=False, research_ready=False,
                   backtest_allowed=False, holdout_claim=False,
                   source_baselines_refitted=False, k=config['k'], block_weights=config['block_weights'])
    target.mkdir(parents=True)
    files = {'summary.json': summary, 'snapshots.json': snapshots, 'protocol.json': config, 'input-pins.json': pins}
    for name, value in files.items():
        (target/name).write_bytes((json.dumps(value, indent=2, sort_keys=True)+'\n').encode())
    (target/'assignments.csv').write_bytes(csv_bytes(assignments))
    (target/'metrics.csv').write_bytes(csv_bytes(metrics))
    (target/'manifest.json').write_bytes((json.dumps({p.name: sha(p) for p in target.iterdir()},indent=2,sort_keys=True)+'\n').encode())
    return summary
