import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_catalogue_rows import run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','verify']);p.add_argument('--config',default='configs/data/financial_catalogue_rows_v1.json');a=p.parse_args()
    try:print(json.dumps(run(ROOT,a.config,a.action),ensure_ascii=False,indent=2))
    except Exception as e:print(json.dumps(dict(status='FAIL_CLOSED',reason=str(e))));raise SystemExit(2)
