import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.experiments.financial_reference_flow import export

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Replay bounded PDF/OCR/date-PIT/reference calculator flow')
    p.add_argument('--config', default='configs/data/financial_reference_flow_v1.json')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    out = (ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data/financial'):
        raise ValueError('output must be under data/financial')
    result = export(ROOT, ROOT/a.config, out)
    print(json.dumps(dict(counts=result['counts'],review_queue=len(result['review_queue']))))
