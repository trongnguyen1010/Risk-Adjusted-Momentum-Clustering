import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_cached_fact_reconciliation import run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True)
    print(json.dumps(run(ROOT,p.parse_args().config),ensure_ascii=False,indent=2))
