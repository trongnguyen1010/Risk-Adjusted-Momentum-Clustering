"""Verify immutable financial flow including reused external evidence; no network."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_batch_flow import verify_flow
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True)
    print(json.dumps(verify_flow(ROOT,p.parse_args().run)))
