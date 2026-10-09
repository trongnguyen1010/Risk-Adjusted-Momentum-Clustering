import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.stdout.reconfigure(encoding='utf8')
from delta_t1.ingestion.financial_retention import inventory,archive_root,verify_before_prune,restore,sha_file

def write(path,value):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Financial retention; archive verification precedes physical pruning')
    parser.add_argument('action',choices=['inventory','archive','verify-prune','restore'])
    parser.add_argument('--inventory',default='.tmp/financial-source-review/retention-inventory.json')
    parser.add_argument('--archive-dir',default='artifacts/archives/financial-cleanup-20261008-v1')
    parser.add_argument('--plan',default='artifacts/archives/financial-cleanup-20261008-v1/prune-plan.json')
    parser.add_argument('--ready',default='artifacts/archives/financial-cleanup-20261008-v1/prune-ready.json')
    parser.add_argument('--archive')
    args=parser.parse_args()
    if args.action=='inventory':
        result=inventory(ROOT);write(args.inventory,result)
        print(json.dumps({k:result[k] for k in ['roots','files','bytes']},indent=2))
    elif args.action=='archive':
        snapshot=json.loads((ROOT/args.inventory).read_bytes());records=[]
        for row in snapshot['items']:
            if row['action']!='ARCHIVE_INACTIVE':continue
            record=archive_root(ROOT,row['name'],ROOT/args.archive_dir)
            record.pop('manifest');records.append(record)
            print(json.dumps(record,ensure_ascii=False),flush=True)
        write(args.plan,dict(version='financial-retention-prune-v1',records=records,inventory=args.inventory))
    elif args.action=='verify-prune':
        plan=json.loads((ROOT/args.plan).read_bytes());rows=[]
        # An active run may have completed after the archive inventory was taken.
        # Recompute closure once, then never prune a newly active dependency.
        latest=inventory(ROOT)
        active={r['name'] for r in latest['items'] if r['action']=='KEEP_ACTIVE_DEPENDENCY'}
        kept=[]
        for record in plan['records']:
            if record['name'] in active:
                kept.append(record['name'])
                print(json.dumps(dict(name=record['name'],status='KEEP_NEW_ACTIVE_DEPENDENCY')),flush=True)
                continue
            rows.append(verify_before_prune(ROOT,record))
            print(json.dumps(rows[-1]),flush=True)
        write(args.ready,dict(status='ALL_ARCHIVES_AND_SOURCE_HASHES_VERIFIED',targets=rows,
            active_roots=sorted(active),kept_after_archive=kept,plan_sha256=sha_file(ROOT/args.plan)))
    else:
        if not args.archive:parser.error('--archive required')
        archive=(ROOT/args.archive).resolve()
        plan=json.loads((ROOT/args.plan).read_bytes())
        records=[r for r in plan['records'] if (ROOT/r['archive']).resolve()==archive]
        if len(records)!=1:raise ValueError('exact archive pin missing from prune plan')
        print(json.dumps(restore(ROOT,archive,records[0]['archive_sha256']),ensure_ascii=False,indent=2))
