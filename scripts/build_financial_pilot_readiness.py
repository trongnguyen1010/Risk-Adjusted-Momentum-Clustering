"""Overlay reviewed annual PDF observations without promoting financial PIT."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_pilot_readiness import export

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-run',required=True)
    p.add_argument('--fact-run',required=True,action='append')
    p.add_argument('--output',required=True)
    p.add_argument('--document-review-run')
    p.add_argument('--correction-run')
    a=p.parse_args(); out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data'): raise ValueError('output must be under data')
    r=export(ROOT/a.baseline_run,[ROOT/x for x in a.fact_run],out,
             ROOT/a.document_review_run if a.document_review_run else None,
             ROOT/a.correction_run if a.correction_run else None)
    print(json.dumps({'counts':r['counts'],'accepted_annual_observations':r['accepted_annual_observations']}))
