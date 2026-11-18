"""Verify sealed triage evidence and unchanged financial dataset, offline."""
import csv
import io
import json
from pathlib import Path
from collections import defaultdict
from delta_t1.ingestion.cafef_financial import digest, encoded
from delta_t1.ingestion.financial_batch_evidence import inside
from delta_t1.experiments.financial_history_documents import put


def run(root):
    report = root / 'artifacts/reports/financial-quarter-gap-triage-v2'
    ref = json.loads((report / 'result-ref.json').read_bytes())
    output = inside(root, ref['path'])
    body = (output / 'manifest.json').read_bytes()
    assert digest(body) == ref['manifest_sha256']
    manifest = json.loads(body)
    for name, sha in manifest.items():
        assert digest((output / name).read_bytes()) == sha, name
    pins = json.loads((output / 'input-pins.json').read_bytes())
    for path, sha in pins.items():
        assert digest(inside(root, path).read_bytes()) == sha, path
    config = json.loads((output / 'config.json').read_bytes())
    baseline = inside(root, config['baseline']['path'])
    bmanifest = json.loads((baseline / 'manifest.json').read_bytes())
    for name, sha in bmanifest.items():
        assert digest((baseline / name).read_bytes()) == sha, name
    coverage = list(csv.DictReader(io.StringIO((baseline / 'coverage-by-symbol.csv').read_text(encoding='utf-8-sig'))))
    near = {r['registry_id']: set(json.loads(r['missing_years'])) for r in coverage if int(r['after_periods']) == 9}
    targets = json.loads((output / 'quarter-triage.json').read_bytes())
    assert len({(r['registry_id'], r['year']) for r in targets}) == len(targets)
    assert all(r['year'] in near[r['registry_id']] for r in targets)
    assert all(not r['annual_conversion_accepted'] and not r['recovered'] and not r['strict_pit_ready'] and not r['research_ready'] for r in targets)
    summary = json.loads((output / 'summary.json').read_bytes())
    assert summary['targets'] == len(targets) == 124
    assert summary['full10_before'] == summary['full10_after'] == sum(int(r['after_periods']) == 10 for r in coverage) == 463
    observations = list(csv.DictReader(io.StringIO((output / 'quarter-headers.csv').read_text(encoding='utf-8-sig'))))
    receipt_rows = list(csv.DictReader(io.StringIO((output / 'receipt-evidence.csv').read_text(encoding='utf-8-sig'))))
    by_target = defaultdict(list)
    for r in observations:
        by_target[r['symbol'], int(r['target_year'])].append(r)
    # Independent set reconstruction, without importing the triage helper.
    required = {('CDKT', 'TN'), ('CDKT', 'NV'), ('KQKD', 'KQKD'), ('LCTT', 'HDKD')}
    for r in targets:
        groups = defaultdict(set)
        for h in by_target[r['symbol'], r['year']]:
            if int(h['numeric_cells']) > 0 and h['provider_type']:
                groups[h['provider_type'], int(h['quarter'])].add((h['statement'], h['group']))
        providers = {p for p, q in groups}
        assert r['q4_same_provider_tokens'] == sorted(p for p in providers if required <= groups[p, 4])
        assert r['four_quarters_same_provider_tokens'] == sorted(p for p in providers if all(required <= groups[p, q] for q in range(1, 5)))
    result = dict(status='PASS', input_pins_verified=len(pins), output_files_verified=len(manifest), baseline_files_unchanged=len(bmanifest), targets_verified=len(targets), header_observations=len(observations), max_pinned_quarter_page=max(int(r['page']) for r in receipt_rows), full10=463, recovered_rows=0, strict_pit_ready=False, research_ready=False)
    put(report / 'verification.json', encoded(result))
    print(json.dumps(result))


if __name__ == '__main__':
    run(Path(__file__).resolve().parents[1])
