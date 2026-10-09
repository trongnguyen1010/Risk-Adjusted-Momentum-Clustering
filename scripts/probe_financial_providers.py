import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_provider_probe import collect
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data'):raise ValueError('output must be under data')
    r=collect(json.loads((ROOT/a.config).read_bytes()),out)
    print(json.dumps({'statuses':[{k:x.get(k) for k in ['provider','report','status','envelope_keys','error']} for x in r['requests']]}))
