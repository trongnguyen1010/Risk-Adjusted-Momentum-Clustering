import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_acquisition_batches import execute
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','run','verify']);p.add_argument('--config',default='configs/data/financial_acquisition_total100_v1.json');p.add_argument('--network',action='store_true');p.add_argument('--max-new-requests',type=int,default=200);args=p.parse_args()
    try:print(json.dumps(execute(ROOT,args.config,args.action,args.network,args.max_new_requests),ensure_ascii=False,indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED',reason=str(error))));raise SystemExit(2)
