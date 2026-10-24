"""Prepare the read-only web index once; no research model or feature recomputation."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.product.terminal_export import export

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='data/web/delta-intelligence-v1')
    p.add_argument('--skip-prices',action='store_true',help='explicitly omit price history for test/development bundles')
    a=p.parse_args()
    print(export(ROOT,a.output,include_prices=not a.skip_prices))
