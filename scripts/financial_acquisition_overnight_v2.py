import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_acquisition_overnight_v2 import run
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args()
 try:print(json.dumps(run(ROOT,a.config),ensure_ascii=False,indent=2))
 except Exception as error:print(json.dumps(dict(status='FAIL_CLOSED',reason=str(error))));raise SystemExit(2)
