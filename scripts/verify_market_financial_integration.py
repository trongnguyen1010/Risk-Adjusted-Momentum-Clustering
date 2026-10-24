"""Verify current 60+24 market artifacts and financial reference compatibility."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.market_financial_integration import verify, publish

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='write versioned verification and reference manifest')
    args = parser.parse_args()
    result = verify(ROOT)
    if args.publish:
        print(publish(ROOT, result))
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ('model_pins', 'overlap_by_snapshot', 'counts_by_snapshot')}, indent=2))
