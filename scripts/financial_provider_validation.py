"""Bounded provider pilot and reviewed PDF conflict decisions."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_provider_validation import plan, acquire, probe_ssi, review, verify

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'acquire', 'probe-ssi', 'review', 'verify'])
    parser.add_argument('--config', default='configs/data/financial_provider_validation_v1.json')
    parser.add_argument('--network', action='store_true')
    parser.add_argument('--output', help='Existing review output to verify')
    args = parser.parse_args()
    config = json.loads((ROOT/args.config).read_bytes())
    if args.action in {'acquire','probe-ssi'} and not args.network:
        parser.error('acquire requires explicit --network; other actions are offline')
    if args.action not in {'acquire','probe-ssi'} and args.network:
        parser.error('--network only valid with acquire')
    if args.action == 'verify' and not args.output:
        parser.error('verify requires --output')
    result = verify(ROOT, args.output) if args.action == 'verify' else {
        'plan': plan, 'acquire': acquire, 'probe-ssi':probe_ssi, 'review': review}[args.action](ROOT, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
