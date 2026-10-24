"""Independent arithmetic/scaler/assignment review; never fit a model or fetch data."""
import argparse
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.financial_history_documents import put
from delta_t1.experiments.financial_api_input_review import csv_bytes
from delta_t1.ingestion.financial_batch_evidence import inside
from delta_t1.ingestion.cafef_financial import digest, encoded


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, help='verified frozen source overlay for historical code pins')
    parser.add_argument('--output', help='new repository-relative review output; required with source overlay')
    args = parser.parse_args()
    if args.source_root and not args.output:
        parser.error('--source-root requires a separate --output; preserve original review evidence')
    report = ROOT / 'artifacts/reports/financial-full10-baseline-v1'
    ref = json.loads((report / 'result-ref.json').read_bytes())
    out = inside(ROOT, ref['path'])
    assert sha(out / 'manifest.json') == ref['manifest_sha256']
    manifest = json.loads((out / 'manifest.json').read_bytes())
    for name, expected in manifest.items():
        assert sha(out / name) == expected, name
    pins = json.loads((out / 'input-pins.json').read_bytes())
    frozen_source = {}
    for name, expected in pins.items():
        candidate = inside(ROOT, name)
        if args.source_root and name.startswith(('src/', 'scripts/', 'configs/')):
            frozen = inside(inside(ROOT, str(args.source_root)), name)
            if frozen.is_file():
                candidate = frozen
                frozen_source[name] = str(candidate.relative_to(ROOT)).replace('\\', '/')
        assert sha(candidate) == expected, name
    if args.output:
        report = inside(ROOT, args.output)
    rows = list(csv.DictReader(io.StringIO((out / 'features.csv').read_text(encoding='utf-8-sig'))))
    snapshots = json.loads((out / 'snapshots.json').read_bytes())
    protocol = json.loads((out / 'protocol.json').read_bytes())
    config = json.loads((out / 'config.json').read_bytes())
    identity = digest(encoded(dict(config=config, input_pins=pins)))
    checkpoints = inside(ROOT, config['output_root']) / 'runs' / identity[:20]
    features = protocol['features']
    assert len(rows) == 11720 and len({r['registry_id'] for r in rows}) == 1172
    assert len({(r['registry_id'], r['year']) for r in rows}) == len(rows)
    extremes = []; memberships = []; checks = []
    for year in range(2016, 2026):
        group = sorted([r for r in rows if int(r['year']) == year], key=lambda r: r['registry_id'])
        model = snapshots[str(year)]
        saved = json.loads((checkpoints / ('year-' + str(year) + '.json')).read_bytes())
        assert saved['run_identity'] == identity
        assert saved['result_sha256'] == digest(encoded(model)) and saved['result'] == model
        assert len(group) == 1172
        labels = {r['registry_id']: r['cluster_id'] for r in model['assignments']}
        assert set(labels) == {r['registry_id'] for r in group}
        assert all(not r['strict_pit_ready'] and not r['research_ready'] for r in model['assignments'])
        sizes = Counter(labels.values())
        assert {str(k): v for k, v in sizes.items()} == model['diagnostics']['cluster_sizes']
        for f in features:
            values = [float(r[f]) for r in group]
            s = model['scaler'][f]
            assert math.isclose(s['center'], mean(values), rel_tol=1e-13, abs_tol=1e-13)
            assert math.isclose(s['scale'], pstdev(values) or 1, rel_tol=1e-13, abs_tol=1e-13)
            for r in sorted(group, key=lambda r: -abs((float(r[f])-s['center'])/s['scale']))[:3]:
                extremes.append(dict(symbol=r['symbol'], registry_id=r['registry_id'], year=year, field=f,
                    value=r[f], zscore=(float(r[f])-s['center'])/s['scale'], cluster_id=labels[r['registry_id']],
                    source_evidence=r['source_evidence'], reason='TOP3_ABSOLUTE_ZSCORE_REVIEW_NOT_PROOF_OF_SOURCE_ERROR'))
        inertia = 0
        for r in group:
            vector = [(float(r[f])-model['scaler'][f]['center'])/model['scaler'][f]['scale'] for f in features]
            distances = [sum((a-b)**2 for a, b in zip(vector, center)) for center in model['centroids']]
            label = labels[r['registry_id']]
            assert label == min(range(3), key=lambda k: (distances[k], k))
            inertia += distances[label]
            if sizes[label] < 10:
                memberships.append(dict(symbol=r['symbol'], registry_id=r['registry_id'], year=year,
                    cluster_id=label, cluster_size=sizes[label], source_evidence=r['source_evidence']))
        assert math.isclose(inertia, model['diagnostics']['inertia'], rel_tol=1e-12, abs_tol=1e-10)
        for profile in model['profiles']:
            selected = [r for r in group if labels[r['registry_id']] == profile['cluster_id']]
            assert len(selected) == profile['size']
            for f in features:
                assert math.isclose(mean(float(r[f]) for r in selected), profile['means'][f], rel_tol=1e-12, abs_tol=1e-12)
        checks.append(dict(year=year, cluster_sizes=dict(sizes), converged=model['diagnostics']['converged'],
                           small_clusters=sum(v < 10 for v in sizes.values())))
    put(report / 'outlier-review.csv', csv_bytes(extremes))
    put(report / 'small-cluster-members.csv', csv_bytes(memberships))
    verification = dict(status='PASS', result=ref, pinned_files_checked=len(pins), annual_rows_checked=len(rows),
        checks=['RESULT_AND_INPUT_HASHES', 'EXACT_1172_X10_KEYS', 'PER_YEAR_SCALER_NO_FUTURE_ROWS',
                'NEAREST_CENTROID_ALL_ASSIGNMENTS', 'INERTIA_RECOMPUTED', 'PROFILE_MEANS_AND_SIZES',
                'YEAR_CHECKPOINT_IDENTITIES_AND_CHECKSUMS'],
        year_checks=checks, review_script_sha256=sha(Path(__file__)),
        quality_status='REVIEW_REQUIRED_SMALL_CLUSTERS_NOT_RESEARCH_READY', model_refits=0,
        new_network_requests=0, new_pdf_downloads=0)
    if args.source_root:
        verification['frozen_source_overlay'] = frozen_source
    put(report / 'verification.json', verification)
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
