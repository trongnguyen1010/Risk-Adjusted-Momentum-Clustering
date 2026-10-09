"""Pin an independently discovered replacement candidate; retain failed lineage."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_batch_evidence import inside, validate
from delta_t1.ingestion.financial_documents import verify_inventory

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True);p.add_argument('--source-run',required=True)
    p.add_argument('--failed-run',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    c=json.loads(inside(ROOT,a.config).read_bytes())
    source=inside(ROOT,a.source_run,'data');failed=inside(ROOT,a.failed_run,'data')
    verify_inventory(source);verify_inventory(failed)
    requests=json.loads((source/'inventory.json').read_bytes())['requests']
    pdf=[r for r in requests if r['symbol']=='DGC' and r['kind']=='pdf' and r['status']=='DOWNLOADED']
    html=[r for r in requests if r['symbol']=='DGC' and r['kind']=='html' and r['status']=='DOWNLOADED']
    if len(pdf)!=1 or len(html)!=1 or pdf[0]['url'] not in Path(html[0]['path']).read_text(encoding='utf8'):
        raise ValueError('exact independently discovered HTML attachment required')
    r=pdf[0]
    previous=json.loads((failed/'results.json').read_bytes())
    bad=[d for d in previous['documents'] if d['symbol']=='DGC' and d['acquisition']['status']=='FAILED'
         and d['acquisition']['error']=='HTTP 404; no redirect/workaround']
    if len(bad)!=1:raise ValueError('expected recorded 404 candidate')
    # This is an explicit task-plan correction after a 404, not a value reconciliation or source ranking.
    c['discovery']=[d for d in c['discovery'] if d['symbol']!='DGC']
    c['documents'].append(dict(symbol='DGC',year=2025,quarter=0,url=r['url']))
    if 'ducgiangchem.vn' not in c['approved_hosts']:c['approved_hosts'].append('ducgiangchem.vn')
    c['cache_records'].append(dict(url=r['url'],kind='pdf',run=source.relative_to(ROOT).as_posix(),
        manifest_sha256=digest((source/'manifest.json').read_bytes()),
        path=Path(r['path']).relative_to(ROOT).as_posix(),sha256=r['sha256']))
    c['source_resolutions']=[dict(symbol='DGC',status='CANDIDATE_URL_PLAN_CORRECTION_AFTER_404',
        failed_url=bad[0]['url'],failed_run=failed.relative_to(ROOT).as_posix(),
        failed_manifest_sha256=digest((failed/'manifest.json').read_bytes()),
        new_candidate_url=r['url'],source_html=html[0]['url'],
        publication_date_not_auto_accepted=True,value_reconciliation_not_performed=True)]
    c['evidence_pins'][source.relative_to(ROOT).as_posix()+'/manifest.json']=digest((source/'manifest.json').read_bytes())
    c['evidence_pins'][failed.relative_to(ROOT).as_posix()+'/manifest.json']=digest((failed/'manifest.json').read_bytes())
    c['code_sha256']={n:digest((ROOT/n).read_bytes()) for n in c['code_sha256']}
    validate(c);immutable_write(inside(ROOT,a.output,'configs'),encoded(c))
    print(json.dumps(dict(config=a.output,resolution='DGC official candidate; original 404 preserved')))
