"""Read-only M2 audit. Run from repo root. New evidence directory required."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import median
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--with-c8', action='store_true')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if not (root / 'configs/experiments/m2_market_only_v1.json').is_file():
        parser.error('Run from repository root, where configs, M2 and src exist.')
    out = (root / args.output).resolve()
    if not out.is_relative_to(root) or out.exists():
        parser.error('Output must be a NEW directory inside repository.')
    out.mkdir(parents=True)
    sys.path.insert(0, str(root / 'src'))
    checks, hash_rows = [], []

    def record(name, status, detail):
        checks.append(dict(check=name, status=status, detail=str(detail)))
        print(f'{status}: {name}: {detail}', flush=True)

    def attempt(name, fn):
        try:
            record(name, 'PASS', fn())
        except FileNotFoundError as e:
            record(name, 'BLOCKED', e)
        except Exception as e:
            record(name, 'FAIL', f'{type(e).__name__}: {e}')

    def safe_path(base, name):
        p = (base / name.replace('\\', '/')).resolve()
        if not p.is_relative_to(root):
            raise ValueError('Path outside repo: ' + name)
        return p

    def hashes(name, mapping, base):
        count = len(mapping)
        if not count:
            record(name, 'PARTIAL', 'No expected hashes available; absence is not PASS.')
            return
        failed = missing = equivalent = 0
        for relative, expected in mapping.items():
            p = safe_path(base, relative)
            actual = sha(p) if p.is_file() else ''
            status = 'MISSING' if not actual else 'PASS' if actual == expected else 'MISMATCH'
            equivalence = ''
            if status == 'MISMATCH':
                raw = p.read_bytes()
                lf = raw.replace(b'\r\n', b'\n')
                crlf = lf.replace(b'\n', b'\r\n')
                if hashlib.sha256(lf).hexdigest() == expected:
                    equivalence = 'LF bytes match expected'
                elif hashlib.sha256(crlf).hexdigest() == expected:
                    equivalence = 'CRLF bytes match expected'
                equivalent += bool(equivalence)
            failed += status == 'MISMATCH'
            missing += status == 'MISSING'
            hash_rows.append(dict(group=name, path=p.relative_to(root).as_posix(),
                                  expected=expected, actual=actual, status=status, newline_diagnostic=equivalence))
        record(name, 'FAIL' if failed else 'BLOCKED' if missing else 'PASS',
               f'{count} files; {failed} mismatch ({equivalent} newline-equivalent); {missing} missing. '
               'Newline equivalence is diagnostic, not automatic checksum acceptance.')

    from delta_t1.experiments.protocol import validate_protocol
    from delta_t1.experiments.final_holdout import freeze_gate, verify_existing
    protocol = read(root / 'configs/experiments/m2_market_only_v1.json')
    attempt('12.1 protocol', lambda: (validate_protocol(protocol), 'Frozen protocol validated')[1])
    holdout_path = root / 'M2/artifacts/m2-final-holdout-v1/manifest.json'
    holdout = read(holdout_path)
    for key in ['artifacts', 'input_sha256', 'code_sha256']:
        hashes('12.1 holdout ' + key, holdout.get(key, {}), root)
    ward_path = root / 'M2/artifacts/m2-task5-ward-v1/manifest.json'
    ward = read(ward_path)
    hashes('12.1 Ward outputs', ward['artifacts'], ward_path.parent)
    pca_path = root / 'M2/artifacts/m2-task6-pca-kmeans-v1/manifest.json'
    pca = read(pca_path)
    hashes('12.1 PCA outputs', pca['artifacts'], root)
    baseline = read(root / 'M2/artifacts/m2-task4-kmeans-baseline-v1/manifest.json')
    record('12.1 baseline manifest', 'PARTIAL',
           'Task 4 manifest has output paths but no complete output checksum map. '
           'Holdout input hashes cover selected dependencies, not every Task 4 file.')

    def global_k():
        path = root / 'artifacts/experiments/m2-task3-development-v1'
        decision = read(path / 'global_k_decision.json')
        hashes('12.2 original K metrics', {
            'per_snapshot_k_metrics.csv': decision['per_snapshot_sha256'],
            'aggregate_by_k.csv': decision['aggregate_sha256']}, path)
        rows = csv_rows(path / 'per_snapshot_k_metrics.csv')
        days, ks = protocol['development_snapshots'], protocol['clustering']['k_range']
        expected = {(day, k) for day in days for k in ks}
        pairs = [(r['snapshot'], int(r['k'])) for r in rows]
        assert len(rows) == 105 and len(set(pairs)) == 105 and set(pairs) == expected
        assert all(r['status'] == 'ok' for r in rows)
        recomputed = []
        for k in ks:
            subset = [r for r in rows if int(r['k']) == k]
            recomputed.append(dict(k=k, median_silhouette=median(float(r['silhouette']) for r in subset),
                median_davies_bouldin=median(float(r['davies_bouldin']) for r in subset)))
        stored = {int(r['k']): r for r in csv_rows(path / 'aggregate_by_k.csv')}
        for row in recomputed:
            for metric in ['median_silhouette', 'median_davies_bouldin']:
                assert abs(row[metric] - float(stored[row['k']][metric])) < 1e-10
        best_sil = max(r['median_silhouette'] for r in recomputed)
        tied = [r for r in recomputed if r['median_silhouette'] == best_sil]
        best_db = min(r['median_davies_bouldin'] for r in tied)
        tied = [r for r in tied if r['median_davies_bouldin'] == best_db]
        assert len(tied) == 1, 'Exact unresolved tie requires manual review.'
        chosen = tied[0]['k']
        assert chosen == decision['proposed_global_k'] == protocol['clustering']['k'] == baseline['global_k'] == holdout['global_k'] == 2
        return '105 development runs; aggregates reproduced; frozen K=2 matches winning rule.'
    attempt('12.2 Global K decision', global_k)
    attempt('12.2 selected method freeze gate', lambda: freeze_gate(root)['selected_method'])

    def split():
        dev, ho = set(protocol['development_snapshots']), set(protocol['holdout_snapshots'])
        assert len(dev) == 15 and len(ho) == 7 and not dev & ho and max(dev) < min(ho)
        assert holdout['methods_executed'] == ['kmeans'] and holdout['k_values_executed'] == [2]
        assert holdout['portfolio_evaluation_enabled'] is False
        assert datetime.fromisoformat(holdout['decision_timestamp']) < datetime.fromisoformat(holdout['holdout_opened_at'])
        for directory in ['m2-task4-kmeans-baseline-v1', 'm2-task5-ward-v1', 'm2-task6-pca-kmeans-v1']:
            dates = {r['snapshot_date'] for r in csv_rows(root / 'M2/artifacts' / directory / 'diagnostics.csv')}
            assert dates == dev, directory + ' development date mismatch'
        assert {r['snapshot_date'] for r in csv_rows(holdout_path.parent / 'diagnostics.csv')} == ho
        return 'Actual diagnostic dates segregated; one frozen method; decision precedes holdout.'
    attempt('12.3 split and selection firewall', split)
    record('12.3 preregistration PCA', 'MANUAL_REVIEW_REQUIRED',
           'ADR-050 and OPEN-07 explicitly retain missing preregistration evidence for PCA v1. '
           'Later validation of 4 components does not establish historical preregistration.')
    record('12.3 final-method rule history', 'MANUAL_REVIEW_REQUIRED',
           'Task 10 uses Occam threshold 0.03. Verify dated approval/commit preceding '
           'selection against the supplied plan; report/code alone does not prove prior registration. '
           'Do not change the frozen decision after seeing holdout.')

    def temporal():
        checked = 0
        sources = [('m2-evaluation-kmeans', 'temporal_stability.csv', set(protocol['development_snapshots'])),
            ('m2-evaluation-ward', 'temporal_stability.csv', set(protocol['development_snapshots'])),
            ('m2-evaluation-pca-kmeans', 'temporal_stability.csv', set(protocol['development_snapshots'])),
            ('m2-final-holdout-v1', 'temporal_stability.csv', set(protocol['holdout_snapshots']))]
        for directory, file, allowed in sources:
            pairs = []
            for row in csv_rows(root / 'M2/artifacts' / directory / file):
                a, b = row['from_date'], row['to_date']
                assert a in allowed and b in allowed, directory + ' boundary crossed'
                month = lambda s: int(s[:4])*12 + int(s[5:7])
                assert month(b) == month(a) + 1, directory + ' temporal gap crossed'
                pairs.append((a,b)); checked += 1
            assert len(set(pairs)) == len(pairs), directory + ' duplicate pair'
            assert set(pairs) == set(zip(sorted(allowed)[:-1], sorted(allowed)[1:])), directory + ' missing pair'
        return f'{checked} temporal pairs checked; no Development-to-Holdout link.'
    attempt('12.4 saved temporal gaps', temporal)

    tests = ['tests.unit.experiments.test_protocol',
        'tests.unit.experiments.test_pca_notebook_artifacts',
        'tests.unit.experiments.test_final_holdout.FinalHoldoutTests',
        'tests.unit.clustering.test_algorithms',
        'tests.integration.test_research_pipeline.ResearchUnitTests.test_clustering_deterministic_and_degenerate',
        'tests.integration.test_research_pipeline.ResearchUnitTests.test_pca_is_deterministic_and_snapshot_scoped']
    if args.with_c8:
        tests += ['tests.unit.experiments.test_m2_runner',
                  'tests.unit.experiments.test_final_holdout.SavedFinalHoldoutEvidenceTests']
    result = subprocess.run([sys.executable, '-m', 'unittest', *tests, '-v'], cwd=root,
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    (out / 'tests.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    record('12.5 targeted tests and bounded fixtures', 'PASS' if result.returncode == 0 else 'FAIL',
           f'exit={result.returncode}; see tests.log. Synthetic fixtures are separate from real holdout.')

    if args.with_c8:
        attempt('12.1 C8 and holdout verify-only', lambda: verify_existing(root, freeze_gate(root))[1]['status'])
        def rerun():
            from delta_t1.experiments.runner import prepare_m2_market_only_snapshots
            from delta_t1.features.preprocessing import preprocess
            from delta_t1.clustering.kmeans import fit_kmeans
            _, prepared = prepare_m2_market_only_snapshots(root / 'artifacts/cafef_primary/cafef-c8-complete-only-v1',
                protocol, snapshot_dates=('2023-11-30',))
            cfg = freeze_gate(root)['clustering']
            vectors, _ = preprocess(prepared[0]['rows'], dict(cfg, reduction={'method':'none'}))
            a = fit_kmeans(vectors, 2, cfg['seed'], cfg['n_init'], cfg['max_iter'])
            b = fit_kmeans(vectors, 2, cfg['seed'], cfg['n_init'], cfg['max_iter'])
            assert a == b and prepared[0]['eligible_count'] == 142
            (out / 'bounded_rerun.json').write_text(json.dumps(dict(snapshot='2023-11-30',
                n=142, k=2, result=a, same_result=True), ensure_ascii=False, indent=2), encoding='utf-8')
            return 'Two independent in-memory fits on 142 development rows are identical; no saved model overwritten.'
        attempt('12.5 real bounded development rerun', rerun)
    else:
        record('12.1 real C8 inputs', 'BLOCKED', 'Not requested; rerun with --with-c8 after restoring original C8 store.')
        record('12.5 real bounded development rerun', 'BLOCKED', 'C8 required; synthetic tests alone do not verify the real input.')
    statuses = {r['status'] for r in checks}
    status = 'FAIL' if 'FAIL' in statuses else 'BLOCKED' if 'BLOCKED' in statuses else 'PARTIAL' if statuses != {'PASS'} else 'PASS'
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True).stdout.strip()
    summary = dict(stage='M2_TASK_12_VERIFY', status=status, checked_at=datetime.now(timezone.utc).isoformat(),
        git_commit=commit, with_c8=args.with_c8, methodology_clearance=False,
        note='Automated checks are bounded evidence. Manual research-history review remains required.', checks=checks)
    (out / 'verify_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    for filename, rows in [('checks.csv',checks),('hash_checks.csv',hash_rows)]:
        with (out / filename).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    manifest = {p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    (out / 'evidence_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('M2 VERIFY STATUS:',status)
    print('Evidence:',out)
    return 0 if status == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
