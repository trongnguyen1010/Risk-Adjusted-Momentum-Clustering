"""Verify and reparse a sealed CafeF run offline without creating another data root."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from crawl_cafef_financial import verify_handoff
from delta_t1.experiments.cafef_financial_trial import parse,exports,prepare,source_pins
from delta_t1.experiments.financial_source_benchmark import qa
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.ingestion.financial_batch_evidence import inside
from delta_t1.ingestion.financial_crawl_candidates import csv_bytes


def replay(root,relative):
    verification=verify_handoff(root,relative);folder=inside(root,relative,'data')
    result=json.loads((folder/'results.json').read_bytes());c=json.loads((folder/'config.json').read_bytes())
    if result['source_pins']!=source_pins(root):raise ValueError('replay requires pinned core source version')
    _,members=prepare(root,c);kinds={m['ticker']:m['proposed_company_type'] for m in members}
    cells=[]
    for request in result['requests']:
        if request['status']!='PARSED_CANDIDATES':continue
        body=inside(root,request['path'],'data').read_bytes()
        if digest(body)!=request['sha256']:raise ValueError('raw replay pin mismatch')
        cells.extend(parse(body,request,kinds[request['symbol']]))
    coverage,requirements,tasks,_=exports(cells,c,members)
    refs=json.loads((folder/'references.json').read_bytes())
    comparisons=[r for r in qa(cells,refs['references']) if r['provider']=='CAFEF']
    generated={'candidates.jsonl':''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in cells).encode('utf8'),
        'coverage.json':encoded(coverage),'requirements.json':encoded(requirements),
        'feature-readiness.json':encoded(tasks),'qa.json':encoded(comparisons)}
    for name,rows in [('coverage.csv',coverage),('requirements.csv',requirements),('feature-readiness.csv',tasks)]:
        fields=[k for k in rows[0] if k not in ('evidence','inputs')];generated[name]=csv_bytes(rows,fields)
    hashes={}
    for name,body in generated.items():
        if body!=(folder/name).read_bytes():raise ValueError('offline export replay differs: '+name)
        hashes[name]=digest(body)
    return dict(status='PASS',run=relative,verification=verification,raw_candidate_cells=len(cells),
        byte_identical_exports=hashes,new_network_requests=0,new_raw_files=0,new_data_roots=0,
        meaning='Offline raw reparse/export check; journal-resume exercised separately by pilot and regression tests')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    try:
        result=replay(ROOT,a.run);immutable_write(inside(ROOT,a.output,'artifacts'),encoded(result))
        print(json.dumps(dict(status=result['status'],exports=len(result['byte_identical_exports']),new_network_requests=0)))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps(dict(status='ERROR',error=str(exc))));raise SystemExit(2)
