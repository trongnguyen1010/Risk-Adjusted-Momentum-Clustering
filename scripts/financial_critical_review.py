import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_critical_review import run

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['run', 'verify'])
    p.add_argument('--config', default='configs/data/financial_critical_review_gas_shs2025_v1.json')
    a = p.parse_args()
    try:
        print(json.dumps(run(ROOT, a.config, a.action), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED', reason=str(error))))
        raise SystemExit(2)
