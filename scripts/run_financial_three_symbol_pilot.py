"""Replay the bounded reviewed annual VNM/PVS/ACV pilot without network."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.experiments.financial_three_symbol_pilot import export

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    r = export(ROOT, a.config, a.output)
    print(json.dumps(dict(status=r['stage_status'], facts=r['reviewed_fact_count'],
                          counts={x['symbol']: x['reference_metric_families_with_arithmetic'] for x in r['results']})))
