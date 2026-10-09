"""Acquire the bounded quotes needed by the financial pilot; no market write."""
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_price_reference import collect
if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--execute',action='store_true',required=True)
    a=p.parse_args();out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data/financial'):raise ValueError('financial evidence output only')
    records, quotes=collect(json.loads((ROOT/a.config).read_bytes()),out)
    print(json.dumps(dict(requests=records, quotes=len(quotes))))
