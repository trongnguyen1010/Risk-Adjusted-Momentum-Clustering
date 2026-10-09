"""Run/resume bounded financial evidence + review queue + offline references."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_batch_flow import run

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--resume-from', action='append', default=[])
    p.add_argument('--execute-network', action='store_true', help='Bounded public acquisition; offline by default')
    p.add_argument('--stop-after', choices=['acquire'])
    a = p.parse_args()
    result = run(ROOT, a.config, a.output, a.resume_from, a.execute_network, a.stop_after)
    print(json.dumps({k:result[k] for k in ['engineering_status', 'acceptance_status', 'metrics', 'review_queue_items']}))
