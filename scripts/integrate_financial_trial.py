"""Offline reviewed-reference integration; no acquisition flag exists."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.stdout.reconfigure(encoding='utf8')
from delta_t1.experiments.financial_trial_integration import export, verify

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['run', 'verify'])
    p.add_argument('--config', default='configs/data/financial_trial_integration_v1.json')
    p.add_argument('--output')
    p.add_argument('--run')
    a = p.parse_args()
    if a.action == 'run' and not a.output:
        p.error('--output required; use a new immutable directory')
    if a.action == 'verify' and not a.run:
        p.error('--run required')
    try:
        result = export(ROOT, a.config, a.output) if a.action == 'run' else verify(ROOT, a.run)
        print(json.dumps({k:v for k,v in result.items() if k != 'source_evidence_pins'}, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as e:
        print(json.dumps(dict(status='ERROR', error=str(e)), ensure_ascii=False))
        raise SystemExit(2)
