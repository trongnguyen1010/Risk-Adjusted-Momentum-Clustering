import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.stdout.reconfigure(encoding='utf8')
from delta_t1.experiments.financial_source_benchmark import run

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Bounded fresh KBS/CafeF comparison; no feature acceptance')
    parser.add_argument('--config',default='configs/data/financial_source_benchmark_v1.json')
    parser.add_argument('--output',required=True)
    parser.add_argument('--execute-network',action='store_true')
    args=parser.parse_args()
    result=run(ROOT,args.config,args.output,args.execute_network)
    print(json.dumps({key:result[key] for key in ['engineering_status','source_summary','collection_seconds','transport_totals']},ensure_ascii=False,indent=2))
