import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_ocr_campaign import coordinate

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['run','snapshot','verify'])
    parser.add_argument('--config',default='configs/data/financial_ocr_campaign_v6.json')
    args=parser.parse_args()
    try:
        print(json.dumps(coordinate(ROOT,args.config,args.action),ensure_ascii=False,indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED',reason=str(error)),ensure_ascii=False))
        raise SystemExit(2)
