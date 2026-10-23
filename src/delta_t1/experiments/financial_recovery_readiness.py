"""Offline provenance cache repair and coverage delivery; no data acceptance or I/O."""
import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from .financial_history_documents import put, read
from .financial_pdf_pipeline import file_hash
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

VERSION = 'financial-recovery-readiness-v1'


def csv_rows(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row.get(k), (list, dict)) else row.get(k, '') for k in fields})
    return stream.getvalue().encode('utf-8-sig')


def records(value, pointer=''):
    if isinstance(value, dict):
        yield pointer, value
        for key, child in sorted(value.items()):
            yield from records(child, pointer+'/'+key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from records(child, pointer+'/'+str(i))


def metadata_paths(root, inventory):
    """Bounded legacy schema discovery near known PDFs, never scan all API JSON."""
    result = set()
    for row in inventory:
        p = inside(root, row['path'])
        for base in [p.parent, p.parent.parent]:
            for name in ['inventory.json', 'results.json', 'result.json', 'document-receipt.json']:
                if (base/name).is_file():
                    result.add(base/name)
            result.update(base.glob('*.receipt.json'))
            if (base/'receipts').is_dir():
                result.update((base/'receipts').rglob('*.json'))
    return sorted(result)


def resolved_path(root, metadata, raw):
    if not isinstance(raw, str):
        return None
    p = Path(raw)
    candidates = [p] if p.is_absolute() else [root/p, metadata.parent/p]
    for candidate in candidates:
        p = candidate.resolve()
        if p.is_relative_to(root.resolve()) and p.is_file():
            return p.relative_to(root.resolve()).as_posix()
    return None


def resolve_cache(root, inventory, paths):
    inventory_map = {row['path']: row for row in inventory}
    for row in inventory:
        p = inside(root, row['path'])
        if file_hash(p) != row['sha256'] or p.stat().st_size != int(row['bytes']):
            raise ValueError('PDF bytes changed: '+row['path'])
    matches, pins = {}, {}
    for metadata in paths:
        rel = metadata.relative_to(root).as_posix()
        pins[rel] = file_hash(metadata)
        for pointer, record in records(read(metadata)):
            payload = record.get('payload', record)
            if not isinstance(payload, dict):
                continue
            path = resolved_path(root, metadata, payload.get('path'))
            if path not in inventory_map or payload.get('sha256') != inventory_map[path]['sha256']:
                continue
            source = record.get('request') or record.get('job') or record
            selected = record.get('provider_report') or record.get('selected') or {}
            url = source.get('url') or selected.get('Link')
            if not isinstance(url, str):
                continue
            parsed = urlsplit(url)
            if parsed.scheme not in ['http', 'https'] or not parsed.hostname or parsed.username or parsed.password:
                continue
            # Hints remain provider metadata, never statement identity or PIT facts.
            hints = dict(symbol=source.get('symbol', record.get('symbol')),
                         year=source.get('year', record.get('year')),
                         quarter=source.get('quarter', record.get('quarter')),
                         scope=source.get('scope', record.get('scope_status')),
                         title=source.get('listing_name') or source.get('listing_title') or selected.get('Name'),
                         provider_report_id=selected.get('id'),
                         identity_status=record.get('identity_status'))
            entry = dict(path=path, sha256=payload['sha256'], url=url, metadata=rel,
                         metadata_sha256=pins[rel], json_pointer=pointer, hints=hints,
                         evidence_basis='EXACT_PATH_AND_HASH_RECEIPT', statement_identity_verified=False,
                         published_at=None, accepted=False)
            matches[digest(encoded(entry))] = entry
    entries = sorted(matches.values(), key=lambda r: (r['path'], r['url'], r['metadata'], r['json_pointer']))
    resolved = {r['path'] for r in entries}
    urls = {}
    for row in entries:
        urls.setdefault(row['url'], set()).add(row['sha256'])
    return dict(entries=entries, unresolved_paths=sorted(set(inventory_map)-resolved),
                url_vintage_conflicts={u: sorted(h) for u, h in sorted(urls.items()) if len(h)>1}), pins


def coverage(features, registry):
    years = {}
    for row in features:
        year = int(row['year'])
        if not 2016 <= year <= 2025:
            raise ValueError('unexpected reference period')
        key = row['registry_id']
        if key not in registry or registry[key]['ticker'] != row['symbol']:
            raise ValueError('registry mismatch')
        if year in years.setdefault(key, set()):
            raise ValueError('duplicate candidate/year')
        if row.get('research_ready') != 'False' or row.get('strict_pit_ready') != 'False':
            raise ValueError('unexpected research/PIT promotion')
        years[key].add(year)
    result = []
    for key, security in sorted(registry.items()):
        observed = sorted(years.get(key, set()))
        best = current = 0
        for year in range(2016, 2026):
            current = current+1 if year in observed else 0
            best = max(best, current)
        result.append(dict(registry_id=key, symbol=security['ticker'], observed_years=observed,
                           missing_years=sorted(set(range(2016, 2026))-set(observed)),
                           observed_periods=len(observed), longest_consecutive=best,
                           full10=len(observed)==10, reference_only=True,
                           strict_pit_ready=False, research_ready=False))
    return result


def recovery_queue(cov, gaps, cache, registry):
    """Planning only: metadata overlaps cannot authorize downloads or accept values."""
    by_key = {(r['registry_id'], int(r['year'])): r for r in gaps}
    symbol_counts = Counter(r['ticker'] for r in registry.values())
    one = sorted([r for r in cov if r['observed_periods']==9], key=lambda r:r['registry_id'])
    two = sorted([r for r in cov if r['observed_periods']==8], key=lambda r:r['registry_id'])
    full = sum(r['full10'] for r in cov)
    needed_two = max(0, 1000-full-len(one))
    plan = one+two[:needed_two]
    result = []
    for candidate in plan:
        for year in candidate['missing_years']:
            gap = by_key.get((candidate['registry_id'], year))
            if gap is None:
                raise ValueError('missing gap evidence')
            matching = [r for r in cache['entries'] if r['hints']['symbol']==candidate['symbol'] and
                        str(r['hints']['year'])==str(year) and symbol_counts[candidate['symbol']]==1]
            docs = sorted({r['sha256'] for r in matching})
            result.append(dict(registry_id=candidate['registry_id'], symbol=candidate['symbol'], year=year,
                               prior_periods=candidate['observed_periods'], reasons=gap['reasons'],
                               cache_candidate_hashes=docs,
                               status='CACHE_METADATA_CANDIDATE_REVIEW_REQUIRED' if docs else 'NO_METADATA_MATCH_NOT_PROOF_OF_ABSENCE',
                               download_authorized=False, pdf_required_confirmed=False,
                               statement_identity_verified=False))
    return result, dict(full10=full, one_gap=len(one), two_gap=len(two),
                        selected_two_gap=min(needed_two,len(two)), selected_candidates=len(plan),
                        annual_dependencies=len(result), hypothetical_full10=full+len(plan),
                        guarantee=False, confirmed_pdf_count=None)


def execute(root, config_path):
    c = read(inside(root, config_path)); pins = {}
    if c['version'] != VERSION or not {c[k] for k in ['inventory','registry','features','gaps']} <= set(c['inputs']):
        raise ValueError('required input pins missing')
    for path, sha in c['inputs'].items():
        if file_hash(inside(root, path)) != sha:
            raise ValueError('input changed: '+path)
        pins[path] = sha
    inventory = csv_rows(inside(root, c['inventory']))
    cache, meta_pins = resolve_cache(root, inventory, metadata_paths(root, inventory))
    pins.update(meta_pins)
    for path in [config_path, 'src/delta_t1/experiments/financial_recovery_readiness.py',
                 'scripts/financial_recovery_readiness.py', 'scripts/financial_recovery_readiness.ps1',
                 'src/delta_t1/experiments/financial_history_documents.py',
                 'src/delta_t1/experiments/financial_pdf_pipeline.py',
                 'src/delta_t1/ingestion/cafef_financial.py',
                 'src/delta_t1/ingestion/financial_batch_evidence.py']:
        pins[path] = file_hash(inside(root, path))
    registry_rows = csv_rows(inside(root,c['registry']))
    registry = {r['registry_id']:r for r in registry_rows}
    if len(registry) != len(registry_rows):
        raise ValueError('duplicate registry id')
    features = csv_rows(inside(root,c['features']))
    cov = coverage(features, registry)
    queue, target = recovery_queue(cov,csv_rows(inside(root,c['gaps'])),cache,registry)
    summary = dict(version=VERSION, feature_rows=len(features), candidates=len(cov),
                   at_least_one=sum(r['observed_periods']>0 for r in cov),
                   consecutive_cohorts={str(n):sum(r['longest_consecutive']>=n for r in cov) for n in [3,5,8,10]},
                   cache_files=len(inventory), cache_resolved_files=len(inventory)-len(cache['unresolved_paths']),
                   cache_unknown_files=len(cache['unresolved_paths']), metadata_files=len(meta_pins),
                   cache_entries=len(cache['entries']), url_vintage_conflicts=len(cache['url_vintage_conflicts']),
                   route_to_1000=target, new_reference_rows=0, new_full10=0,
                   network_requests=0, pdf_downloads=0, ocr_pages=0,
                   strict_pit_ready=False, research_ready=False, status='PARTIAL_COVERAGE_GOAL')
    result = inside(root,c['output_root'])/'results'/digest(encoded(pins))[:20]
    outputs = {'input-pins.json':encoded(pins), 'cache-index.json':encoded(cache), 'summary.json':encoded(summary)}
    outputs['coverage.csv'] = csv_bytes(cov,list(cov[0]))
    for n in [3,5,8,10]:
        subset = [r for r in cov if r['longest_consecutive']>=n]
        outputs[f'cohort-{n}y-reference.csv'] = csv_bytes(subset,list(cov[0]))
        ids = {r['registry_id'] for r in subset}
        outputs[f'features-{n}y-reference.csv'] = csv_bytes([r for r in features if r['registry_id'] in ids],list(features[0]))
    outputs['route-to-1000-review-queue.csv'] = csv_bytes(queue,list(queue[0]))
    for name,raw in outputs.items():
        put(result/name,raw)
    put(result/'manifest.json',{name:digest(raw) for name,raw in sorted(outputs.items())})
    return dict(path=result.relative_to(root).as_posix(),manifest_sha256=file_hash(result/'manifest.json'),summary=summary)


def cli(root):
    p=argparse.ArgumentParser();p.add_argument('--config',default='configs/data/financial_recovery_readiness_v1.json')
    args=p.parse_args();print(json.dumps(execute(root,args.config),ensure_ascii=False))
