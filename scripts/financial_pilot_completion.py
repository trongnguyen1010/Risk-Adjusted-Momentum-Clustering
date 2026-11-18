"""Replay pilot5 with reviewed closing debt components; bounded PDF acquisition."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_pilot_completion import acquire, run, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['acquire', 'run', 'verify'])
    parser.add_argument('--config', default='configs/data/financial_pilot5_completion_v1.json')
    parser.add_argument('--review', help='Reviewed consolidated closing-debt JSON; optional until available')
    parser.add_argument('--output', help='Sealed result directory for verification')
    parser.add_argument('--network', action='store_true')
    args = parser.parse_args()
    if (args.action == 'acquire') != args.network:
        parser.error('only acquire requires --network; run/verify are offline')
    if args.action == 'verify' and not args.output:
        parser.error('verify requires --output')
    config = json.loads((ROOT/args.config).read_bytes())
    result = (acquire(ROOT, config) if args.action == 'acquire' else
              run(ROOT, config, args.review) if args.action == 'run' else verify(ROOT, args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
