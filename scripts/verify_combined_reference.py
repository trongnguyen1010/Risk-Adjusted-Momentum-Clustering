"""Independent artifact/scaler/nearest-centroid review; no fitting or network."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import mean, pstdev
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def inside(relative):
    p = (ROOT / relative).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('path outside repository')
    return p


def table(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes() != data:
        raise ValueError('immutable review differs: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', required=True)
    args = parser.parse_args()
    result = inside(args.result)
    manifest = json.loads((result/'manifest.json').read_bytes())
    for name, expected in manifest.items():
        assert sha(result/name) == expected, name
    pins = json.loads((result/'input-pins.json').read_bytes())
    for name, expected in pins.items():
        assert sha(inside(name)) == expected, name
    config = json.loads((result/'protocol.json').read_bytes())
    assert config['owner_approval']['status'] == 'APPROVED'
    assert config['mode'] == 'EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT'
    assert not any(config[k] for k in ['strict_pit_ready','research_ready','backtest_allowed','holdout_claim'])
    review = inside(config['input_review']['path'])
    review_manifest = json.loads((review/'manifest.json').read_bytes())
    source_path = review/'combined-input-reference.csv'
    assert sha(source_path) == review_manifest['combined-input-reference.csv']
    source = table(source_path)
    assignments = table(result/'assignments.csv')
    key = lambda r: (r['snapshot_date'], r['symbol'])
    keyed_source = {key(r): r for r in source}
    assert len(keyed_source) == len(source) == len(assignments)
    assert {key(r) for r in assignments} == set(keyed_source)
    for row in assignments:
        assert all(row[f] == v for f, v in keyed_source[key(row)].items())
    snapshots = json.loads((result/'snapshots.json').read_bytes())
    checks = []
    for year in config['years']:
        group = [r for r in assignments if int(r['fiscal_year']) == year]
        model = snapshots[str(year)]
        fields = config['market_features'] + config['financial_features']
        assert model['feature_order'] == fields
        scalers = model['scalers']
        for f in fields:
            values = [float(r[f]) for r in group]
            s = scalers[f]
            family = 'market' if f in config['market_features'] else 'financial'
            assert math.isclose(s['center'],mean(values),rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(s['scale'],pstdev(values) or 1,rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(s['weight'],math.sqrt(.5/len(config[family+'_features'])),rel_tol=1e-14)
        inertia = 0
        by_cluster = {}
        for row in group:
            vector = [(float(row[f])-scalers[f]['center'])/scalers[f]['scale']*scalers[f]['weight'] for f in fields]
            label = int(row['combined_cluster_id'])
            distances = [sum((a-b)**2 for a,b in zip(vector,c)) for c in model['centroids']]
            assert distances[label] <= min(distances)+1e-10
            inertia += distances[label]
            by_cluster.setdefault(label, []).append((row, vector))
        assert set(by_cluster) == set(range(config['k']))
        assert math.isclose(inertia,model['metrics']['inertia'],rel_tol=1e-12,abs_tol=1e-8)
        for p in model['profiles']:
            selected = by_cluster[p['cluster_id']]
            assert len(selected) == p['size']
            for i,f in enumerate(fields):
                assert math.isclose(mean(float(r[f]) for r,_ in selected),p['means'][f],rel_tol=1e-12,abs_tol=1e-10)
                assert math.isclose(mean(v[i] for _,v in selected),model['centroids'][p['cluster_id']][i],rel_tol=1e-10,abs_tol=1e-10)
        checks.append(dict(year=year,n=len(group),cluster_sizes={k:len(v) for k,v in by_cluster.items()},
                           inertia_recomputed=inertia,checks='SCALER_WEIGHTS_NEAREST_CENTROID_INERTIA_PROFILES_PASS'))
    output = ROOT/'artifacts/reports/combined-reference-v1'
    verification = dict(status='PASS',snapshot_count=len(checks),assignments_checked=len(assignments),
                        checks=checks,refits=0,strict_pit_ready=False,quality_status='REVIEW_REQUIRED',
                        review_script_sha256=sha(Path(__file__)))
    write(output/'verification.json',verification)
    write(output/'result-ref.json',dict(path=args.result,manifest_sha256=sha(result/'manifest.json')))
    print(json.dumps(verification,indent=2))


if __name__ == '__main__':
    main()
