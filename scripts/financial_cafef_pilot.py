"""PowerShell-facing pilot entrypoint; logic lives in experiments."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.financial_cafef_pilot import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['doctor', 'plan', 'run', 'resume', 'report', 'verify'])
    parser.add_argument('--config', default='configs/data/financial_cafef_pilot5_execution_v1.json')
    parser.add_argument('--network', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(main(ROOT, args.config, args.action, args.network), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED', error=str(error)), ensure_ascii=False))
        sys.exit(2)
