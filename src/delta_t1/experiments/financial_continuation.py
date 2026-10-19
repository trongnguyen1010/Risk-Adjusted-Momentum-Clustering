"""Branch-aligned successor of a frozen financial run, without resetting costs.

No existing pinned code or evidence is edited. Recovery is an explicit one-shot
request epoch for one pinned failed PDF; all global limits/deadlines survive.
"""
import json
import subprocess
from pathlib import Path

from . import financial_user_workflow as f
from ..ingestion.financial_batch_evidence import seal, validate_url
from ..ingestion.financial_compact_trial import CompactTrialTransport
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.sources.base import AccessControlError, RateLimitError
from ..ingestion.financial_trial_transport import TrialBudgetError

VERSION = 'financial-continuation-v2'


def branch(root):
    return subprocess.run(['git', 'branch', '--show-current'], cwd=root,
        text=True, capture_output=True, check=True).stdout.strip()


def descriptor(root, path):
    d = f.load(f.inside(root, path, 'configs'))
    if d.get('version') != VERSION or any(d.get(k) is not False for k in f.CLOSED):
        raise ValueError('closed continuation descriptor required')
    if d.get('max_recovery_attempts') != 1:
        raise ValueError('exactly one explicit recovery attempt allowed')
    if branch(root) != d['expected_branch']:
        raise ValueError('continuation branch mismatch')
    return d


def prepare(root, path):
    root = Path(root).resolve(); d = descriptor(root, path)
    parent, c, _ = f.open_run(root, d['parent_run'])
    output = f.inside(root, d['run'], 'data')
    seed = f.inside(root, d['run'] + '_seeds', 'data')
    cfg_path = f.inside(root, d['successor_config'], 'configs')
    if output.exists() or seed.exists() or cfg_path.exists():
        raise ValueError('continuation output/config already exists; resume, do not prepare again')
    # Verify before acquiring the lock; read all mutable parent state under lock.
    f.verify(root, d['parent_run'])
    with f.exclusive(parent):
        state = f.transport_state(parent)
        rs = f.receipts(parent)
        job = rs.get(d['recovery_job_key'])
        source = f.pin(root, d['recovery_receipt'], d['recovery_receipt_sha256'])
        if job != f.load(source) or job['status'] != 'FAILED' or job['kind'] != 'pdf':
            raise ValueError('recovery must name an exact terminal failed PDF receipt')
        if job['error'] != 'bounded transport attempts exhausted':
            raise ValueError('only transient exhausted transport is eligible; no HTTP/access workaround')
        if state and (state['boundary'] or state['budget_stop']):
            raise ValueError('parent transport latch cannot be cleared by continuation')
        docs = f.document_index(root, parent, c)
        pages = f.page_index(root, parent, c)
        references = f.baseline_references(root, c) + f.review_references(root, parent, c)
        cache, _, _ = f.seeds(root, c)
        cache.update((state or {}).get('cache', {}))
        for r in rs.values():
            if r['status'] in f.GOOD:
                cache[r['url']] = r
        grouped = {}
        for (sha, _), p in pages.items():
            grouped.setdefault(sha, []).append(p)
        seed.mkdir(parents=True)
        snapshots = {
            'probe/results.json': dict(requests=list(cache.values()), documents=[dict(
                symbol=x['symbol'], year=x['year'], acquisition=x,
                provider_report=dict(Name=x['listing_name'])) for x in docs if x.get('url')]),
            'ocr/index.json': dict(documents=[dict(pdf_sha256=sha, pages=ps,
                status='OCR_CANDIDATE_COMPLETE') for sha, ps in grouped.items()]),
            'review/references.json': [], 'integration/reference-ledger.json': references,
            'parent-receipts.json': rs, 'parent-transport-state.json': state,
            'continuation.json': dict(descriptor=d, parent_run=d['parent_run'],
                parent_frozen_manifest_sha256=f.digest((parent/'frozen/manifest.json').read_bytes()),
                inherited_ocr_reservations=f.ocr_reserved(parent),
                inherited_extraction_failures=sum(f.load(p)['status']=='EXTRACTION_FAILED'
                    for p in (parent/'extract').glob('*/result.json')),
                recovery_receipt_sha256=d['recovery_receipt_sha256'], **f.CLOSED)}
        for name, obj in snapshots.items():
            f.write_new(seed/name, f.encoded(obj))
        # Review source pins are immutable even when the parent gets later reports.
        lineage = {p.relative_to(root).as_posix(): f.digest(p.read_bytes())
            for p in (parent/'reviews').glob('*/review.json')}
        snapshots['lineage.json'] = lineage
        f.write_new(seed/'lineage.json', f.encoded(lineage)); seal(seed)
        new = json.loads(json.dumps(c))
        new.update(expected_branch=d['expected_branch'],
            probe_run=(seed/'probe').relative_to(root).as_posix(),
            ocr_run=(seed/'ocr').relative_to(root).as_posix(),
            review_run=(seed/'review').relative_to(root).as_posix(),
            integration_run=(seed/'integration').relative_to(root).as_posix(),
            extra_cached_pdfs=[x for x in docs if not x.get('url')])
        new['input_pins'].update(lineage)
        new['input_pins'].update({p.relative_to(root).as_posix(): f.digest(p.read_bytes())
            for p in seed.rglob('*') if p.is_file()})
        new['input_pins'][path] = f.digest((root/path).read_bytes())
        for name in ['src/delta_t1/experiments/financial_continuation.py',
                     'scripts/financial_continue.py', 'scripts/financial_continue.ps1']:
            new['code_paths'].append(name)
        f.write_new(cfg_path, f.encoded(new))
        f.make_plan(root, d['successor_config'], d['run'])
        # Preserve receipt history and terminal jobs; no re-request on normal acquire.
        for p in (parent/'receipts').glob('*/receipt.json'):
            if not (p.parent/'manifest.json').exists():
                continue
            dest = output/'receipts'/p.parent.name
            f.write_new(dest/'receipt.json', p.read_bytes()); seal(dest)
        # Keep historical failures and conservative reservation cost without copying images.
        for p in (parent/'extract').glob('*/reservation.json'):
            dest = output/'extract'/('inherited-'+p.parent.name)
            f.write_new(dest/'reservation.json', p.read_bytes())
            prior = f.load(p.parent/'result.json') if (p.parent/'result.json').exists() else {}
            f.write_new(dest/'result.json', f.encoded(dict(status=prior.get('status', 'INHERITED_INTERRUPTED'),
                pages=[], parent_attempt=p.parent.relative_to(root).as_posix())))
            seal(dest)
        if state:
            out = output/'transport'/f.stamp(); out.mkdir(parents=True)
            CompactTrialTransport(root, out, new, state)  # no I/O; inherited deadline/cost/latch
    return dict(status='CONTINUATION_PREPARED', run=d['run'], config=d['successor_config'],
        pdf_vintages=len(docs), ocr_pages=len(pages), **f.CLOSED)


def publish_recovery(run, job, record):
    # Original receipt suffixes are hexadecimal. One z1 successor sorts later;
    # its deterministic short name also avoids Windows long-path failures.
    dest = run/'receipts'/(job['job_key']+'-z1')
    if not (dest/'receipt.json').exists():
        f.write_new(dest/'receipt.json', f.encoded(record))
    elif f.load(dest/'receipt.json') != record:
        raise ValueError('recovery receipt conflict')
    if not (dest/'manifest.json').exists():
        seal(dest)
    verify_inventory(dest)


def recover(root, path, network=False, factory=CompactTrialTransport):
    root = Path(root).resolve(); d = descriptor(root, path)
    run, c, _ = f.open_run(root, d['run'])
    seed = f.inside(root, d['run']+'_seeds', 'data'); verify_inventory(seed)
    job = f.load(seed/'parent-receipts.json')[d['recovery_job_key']]
    f.pin(root, d['recovery_receipt'], d['recovery_receipt_sha256'])
    validate_url(job['url'], c['approved_hosts'])
    with f.exclusive(run):
        attempts = list((run/'recovery').glob('*/request.json'))
        if attempts:
            # Finalize a committed cache/result after process death, without I/O.
            if len(attempts)!=1:
                raise ValueError('multiple recovery reservations')
            out=attempts[0].parent
            request=f.load(attempts[0])
            if request.get('job')!=job or request.get('parent_sha256')!=d['recovery_receipt_sha256']:
                raise ValueError('recovery reservation drift')
            record=f.load(out/'result.json') if (out/'result.json').exists() else (
                (f.transport_state(run) or {}).get('cache',{}).get(job['url']))
            if record and record.get('recovery_request')==out.relative_to(root).as_posix():
                if record['status'] in f.GOOD:
                    f.pin(root,record['path'],record['sha256'])
                if not (out/'result.json').exists(): f.write_new(out/'result.json',f.encoded(record))
                if not (out/'manifest.json').exists(): seal(out)
                verify_inventory(out)
                if record['status']!='GLOBAL_STOP': publish_recovery(run,job,record)
            # Interrupted uncommitted requests count, too. Never make a second epoch.
            return dict(status='RECOVERY_ALREADY_RESERVED', attempts=len(attempts), **f.CLOSED)
        if not network:
            return dict(status='RECOVERY_PLANNED', job=job, max_attempts=1, **f.CLOSED)
        if f.receipts(run)[d['recovery_job_key']]['status'] in f.GOOD:
            return dict(status='ALREADY_CACHED', **f.CLOSED)
        state = f.transport_state(run)
        out = run/'recovery'/f.stamp()
        f.write_new(out/'request.json', f.encoded(dict(job=job,
            parent_receipt=d['recovery_receipt'], parent_sha256=d['recovery_receipt_sha256'], **f.CLOSED)))
        txout = run/'transport'/f.stamp(); txout.mkdir(parents=True)
        tx = factory(root, txout, dict(c, cache_epoch=d['run']+'/explicit-recovery-v1'), state)
        tx.context = dict(kind='pdf', symbol=job['symbol'], year=job['year'])
        record = dict(job, recovery_of=d['recovery_receipt'], recovery_request=out.relative_to(root).as_posix())
        record.pop('error', None)
        try:
            body, _ = tx.get(job['url'])
            if not body.startswith(b'%PDF'):
                raise ValueError('invalid PDF signature')
            pdf = run/'raw'/(f.digest(body)+'.pdf')
            if not pdf.exists():
                f.write_new(pdf, body)
            record.update(status='DOWNLOADED', path=pdf.relative_to(root).as_posix(), sha256=f.digest(body))
            tx.commit_cache(job['url'], record)
        except (AccessControlError, RateLimitError, TrialBudgetError) as exc:
            record.update(status='GLOBAL_STOP', error=str(exc))
        except (OSError, ValueError) as exc:
            record.update(status='FAILED', error=str(exc))
        f.write_new(out/'result.json', f.encoded(record)); seal(out)
        if record['status'] != 'GLOBAL_STOP':
            publish_recovery(run,job,record)
        return dict(status=record['status'], recovery=out.relative_to(root).as_posix(),
            record=record, counters={k:v for k,v in tx.state.items() if k not in ['requests','cache']}, **f.CLOSED)


def extract(root, path, pdf_sha, full_ocr=False, retry_failed=False, worker=None):
    """Scope by exact PDF hash, and expose per-PDF failures instead of just batch end."""
    root=Path(root).resolve(); d=descriptor(root,path)
    run,c,_=f.open_run(root,d['run'])
    docs=f.document_index(root,run,c)
    selected=[x for x in docs if x['sha256']==pdf_sha]
    if len(selected)!=1:
        raise ValueError('exact PDF hash must identify one document')
    before={p.parent for p in (run/'extract').glob('*/result.json')}
    original=f.document_index
    try:
        # Legacy v1 has no hash selector. Scope only this synchronous call, keeping
        # its OS lock, page cache, reservations and every OCR bound unchanged.
        f.document_index=lambda *_: selected
        result=f.extract(root,d['run'],1,full_ocr,worker,None,retry_failed)
    finally:
        f.document_index=original
    results=[f.load(p) for p in (run/'extract').glob('*/result.json') if p.parent not in before]
    result['documents']=results
    result['status']='EXTRACTION_FAILED' if any(x['status']=='EXTRACTION_FAILED' for x in results) else (
        'OCR_CANDIDATES_COMPLETE' if results else 'CACHED_OR_SKIPPED')
    return result
