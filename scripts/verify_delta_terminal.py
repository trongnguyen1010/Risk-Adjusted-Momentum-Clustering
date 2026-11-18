"""Verify presentation counts, source pins and read API contracts without fitting."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'web/backend'))
from app.repository import TerminalRepository

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',default='data/web/delta-intelligence-v1')
    parser.add_argument('--check-sources',action='store_true',help='Replay all pinned input file hashes, including the large price source.')
    args=parser.parse_args();start=time.perf_counter();repo=TerminalRepository(ROOT/args.bundle)
    counts={r['kind']:r['n'] for r in repo.query('SELECT kind,count(*) n FROM observations GROUP BY kind')}
    assert counts==dict(market=75801,financial=11720,combined=5593),counts
    snapshots=repo.catalog()['datasets']
    assert {k:len(v['dates']) for k,v in snapshots.items()}==dict(market=84,financial=10,combined=7)
    for kind,ds in snapshots.items():
        for date in ds['dates']:
            data=repo.snapshot(kind,date)
            assert len(data['points'])==data['snapshot']['n']==sum(p['size'] for p in data['profiles'])
            assert all(all(v is not None for v in p['features'].values()) for p in data['points'])
    assert snapshots['combined']['latest']['sizes']=={'0':479,'1':663,'2':6}
    for year in range(2019,2026):
        matrix=repo.matrix(str(year));assert matrix['total']==repo.resolve_snapshot('combined',matrix['date'])['n']
        for cell in matrix['cells']:
            members=repo.members('financial',str(year),matrix_market=cell['market_cluster'],matrix_financial=cell['financial_cluster'])
            assert members['total']==cell['n']
    price_source=next(ROOT/p for p in repo.manifest['sources'] if p.endswith('/prices_daily.jsonl'))
    with price_source.open(encoding='utf8') as f:source=json.loads(next(f))
    actual=repo.query('SELECT * FROM prices WHERE security_id=? AND date=?',(source['security_id'],source['trade_date']))[0]
    assert actual['adj_close']==source.get('adj_close') and actual['raw_close']==source.get('raw_close')
    assert repo.query('SELECT count(*) n FROM prices')[0]['n']==3214287
    checked=0
    if args.check_sources:
        for relative,pin in repo.manifest['sources'].items():
            with (ROOT/relative).open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            assert digest==pin['sha256'],relative
            checked+=1
    result=dict(status='PASS',observations=counts,snapshots=101,profiles=219,price_rows=3214287,matrix_years=7,
                source_hashes_replayed=checked,seconds=round(time.perf_counter()-start,2),no_model_fitting=True)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
