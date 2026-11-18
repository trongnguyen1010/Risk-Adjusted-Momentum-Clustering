"""Local CLI for bounded historical financial acquisition."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.financial_history_pit import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['doctor','plan','regression','run','resume','qa','report','verify'])
    parser.add_argument('--config', default='configs/data/financial_history_pit_v1.json')
    parser.add_argument('--network', action='store_true')
    parser.add_argument('--max-network-requests', type=int, default=25)
    args = parser.parse_args()
    try:
        if not 0 <= args.max_network_requests <= 1600:
            raise ValueError('max-network-requests must be 0..1600')
        result = main(ROOT, args.config, args.action, args.network, args.max_network_requests)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        if result.get('status') == 'FAIL_CLOSED': sys.exit(2)
    except Exception as error:
        print(json.dumps(dict(status='FAIL_CLOSED', error=str(error)), ensure_ascii=False))
        sys.exit(2)
