"""Replay pinned new-symbol financial reference QA offline."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_scale_review import build
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build(ROOT,a.config,a.output),ensure_ascii=False,indent=2))
