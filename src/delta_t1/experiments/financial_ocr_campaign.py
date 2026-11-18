"""Single-worker OCR coordinator; persistent imported reservations retain all caps."""
from collections import Counter
from datetime import datetime, timezone
import json

from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import put, read
from .financial_selected_ocr import prepare, run as ocr_run, snapshot, validate_jobs
from .financial_user_workflow import exclusive


def budget_check(records, reservations, limits, batches, now, executing):
    pages, per_pdf, per_batch = set(), Counter(), Counter()
    known = {}
    for record in records:
        if record['batch_id'] not in batches:
            raise ValueError('unknown OCR batch')
        for job in record['jobs']:
            key = (job['pdf_sha256'], job['pdf_page'])
            if key in pages:
                raise ValueError('duplicate PDF page across OCR runs')
            pages.add(key)
            per_pdf[key[0]] += 1
            per_batch[record['batch_id']] += 1
            known[(record['output_root'], job['id'])] = job
        if executing and now > batches[record['batch_id']]['created_at'] + 259200:
            # Completed old batches may remain imported into a later live batch.
            pending = any((record['output_root'], j['id']) not in reservations for j in record['jobs'])
            if pending:
                raise ValueError('inherited batch deadline expired')
    for key, reservation in reservations.items():
        if key not in known or reservation.get('charged_pages') != 1 or reservation.get('job') != known[key]:
            raise ValueError('unknown or altered OCR reservation')
    if len(pages) > limits['campaign_pages'] or any(n > limits['per_pdf_pages'] for n in per_pdf.values()):
        raise ValueError('campaign/per-PDF OCR budget exceeded')
    if any(n > batches[b]['page_cap'] for b, n in per_batch.items()):
        raise ValueError('batch OCR budget exceeded')
    if executing and now > limits['created_at'] + 90 * 86400:
        raise ValueError('inherited 90-day campaign deadline expired')
    return dict(charged_pages=len(reservations), planned_total_pages=len(pages),
                pending_pages=len(pages)-len(reservations), per_pdf_pages=dict(sorted(per_pdf.items())),
                per_batch_pages=dict(sorted(per_batch.items())))


def coordinate(root, config_path, action):
    config = read(inside(root, config_path))
    if config.get('version') != 'financial-ocr-campaign-v1':
        raise ValueError('OCR campaign contract required')
    limits = config['limits']
    if (type(limits['campaign_pages']) is not int or not 1 <= limits['campaign_pages'] <= 12000
            or type(limits['per_pdf_pages']) is not int or not 1 <= limits['per_pdf_pages'] <= 40):
        raise ValueError('invalid OCR campaign caps')
    out = inside(root, config['output_root']); out.mkdir(parents=True, exist_ok=True)
    with exclusive(out):
        def persist(path, value):
            if action=='verify':
                if read(path)!=value:raise ValueError('OCR persisted policy/registration changed')
            else:put(path,value)
        persist(out/'policy.json', limits)
        # Persist every registration separately; a later config cannot forget old jobs.
        for batch_id, batch in config['batches'].items():
            if (not batch_id.replace('-', '').isalnum() or type(batch['page_cap']) is not int
                    or not 1 <= batch['page_cap'] <= 1000 or batch['created_at'] < limits['created_at']):
                raise ValueError('invalid OCR batch cap/anchor')
            persist(out/'batches'/(batch_id+'.json'), batch)
        records = {p.stem:read(p) for p in (out/'registrations').glob('*.json')}
        for item in config['runs']:
            raw = inside(root,item['config_path']).read_bytes()
            if digest(raw) != item['config_sha256']:
                raise ValueError('OCR child config changed')
            child = json.loads(raw)
            validate_jobs(child['jobs'],child['max_ocr_pages'])
            if any('/' in j['id'] or '\\' in j['id'] or j['id'] in ['.','..'] for j in child['jobs']):
                raise ValueError('invalid OCR task ID')
            if child['campaign_anchor'] != config['batches'][item['batch_id']]['created_at']:
                raise ValueError('OCR child reset batch deadline')
            record = dict(item, output_root=child['output_root'], jobs=child['jobs'])
            previous = [r for r in records.values() if r['config_path']==item['config_path']
                        or r['output_root']==child['output_root']]
            if previous and previous != [record]:
                raise ValueError('OCR registration changed')
            records[item['config_sha256']] = record
        records = sorted(records.values(),key=lambda r:r['output_root'])
        batches = {p.stem:read(p) for p in (out/'batches').glob('*.json')}
        for record in records:
            raw=inside(root,record['config_path']).read_bytes()
            child=json.loads(raw)
            if (digest(raw)!=record['config_sha256'] or child['jobs']!=record['jobs']
                    or child['output_root']!=record['output_root']
                    or child['campaign_anchor']!=batches[record['batch_id']]['created_at']):
                raise ValueError('persisted OCR registration lost source identity/anchor')
        reservations = {}
        registered_roots = {r['output_root'] for r in records}
        # This exact namespace is the history OCR campaign; legacy campaigns stay separate.
        for candidate in inside(root,'data/financial').glob('history_selected_ocr*'):
            if (candidate/'reservations').exists() and candidate.relative_to(root).as_posix() not in registered_roots:
                raise ValueError('unregistered history OCR reservations; inventory before running')
        def inventory():
            found={}
            for record in records:
                for p in (inside(root,record['output_root'])/'reservations').glob('*.json'):
                    found[record['output_root'],p.stem]=read(p)
            return found
        reservations=inventory()
        for record in records:
            child_out=inside(root,record['output_root'])
            for folder in ['pages','errors']:
                for p in (child_out/folder).glob('*.json'):
                    if (record['output_root'],p.stem) not in reservations:
                        raise ValueError('OCR terminal receipt without charged reservation')
        now=datetime.now(timezone.utc).timestamp()
        budget_check(records,reservations,limits,batches,now,action=='run')
        for record in records:
            persist(out/'registrations'/(record['config_sha256']+'.json'),record)
        if action=='run':
            for record in records:
                budget_check(records,inventory(),limits,batches,datetime.now(timezone.utc).timestamp(),True)
                child_out=inside(root,record['output_root'])
                if all((child_out/'pages'/(j['id']+'.json')).exists()
                       or (child_out/'errors'/(j['id']+'.json')).exists() for j in record['jobs']):
                    continue
                child,child_out=prepare(root,record['config_path'])
                with exclusive(child_out):
                    ocr_run(root,child,child_out)
                    snapshot(root,child_out,False)
        pins={config_path:digest(inside(root,config_path).read_bytes())}
        for relative in ['src/delta_t1/experiments/financial_ocr_campaign.py','scripts/financial_ocr_campaign.py']:
            pins[relative]=digest(inside(root,relative).read_bytes())
        children=[]
        checked={}
        for record in records:
            child_out=inside(root,record['output_root'])
            contract=read(child_out/'contract.json')
            for path,expected in contract['pins'].items():
                if path not in checked:checked[path]=digest(inside(root,path).read_bytes())
                if checked[path]!=expected:raise ValueError('frozen OCR child pin changed: '+path)
            children.append(snapshot(root,child_out,True))
        counts=budget_check(records,inventory(),limits,batches,now,False)
        products={'summary.json':encoded(dict(counts,status='PARTIAL',child_runs=len(records),
                    successful_pages=sum(c['successful_ocr_pages'] for c in children),
                    errors=sum(c['errors'] for c in children),accepted_facts=0,pit_ready=False)),
                  'children.json':encoded(children),'registrations.json':encoded(records),
                  'policy.json':encoded(limits),'batches.json':encoded(batches),'pins.json':encoded(pins),
                  'reservations.json':encoded([dict(output_root=k[0],id=k[1],reservation=v)
                                               for k,v in sorted(inventory().items())])}
        manifest={n:digest(raw) for n,raw in products.items()}
        result=out/'results'/digest(encoded(manifest))[:20]
        if action=='verify':
            if read(result/'manifest.json')!=manifest:raise ValueError('OCR campaign snapshot differs')
            for name,expected in manifest.items():
                if digest((result/name).read_bytes())!=expected:raise ValueError('OCR campaign artifact changed')
        else:
            for name,raw in products.items():put(result/name,raw)
            put(result/'manifest.json',manifest)
        return dict(json.loads(products['summary.json']),status='VERIFIED' if action=='verify' else 'PARTIAL',
                    output=result.relative_to(root).as_posix())
