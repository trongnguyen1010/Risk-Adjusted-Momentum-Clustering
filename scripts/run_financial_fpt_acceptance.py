"""Run the bounded FPT financial handoff from immutable reviewed inputs."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.financial_fpt_acceptance import export

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    r = export(ROOT, a.config, a.output)
    print(json.dumps(dict(status=r['stage_status'], counts=[x['reference_metric_families_available'] for x in r['results']])))
