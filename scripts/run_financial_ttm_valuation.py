"""Run bounded offline financial TTM/share-event reference calculation."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_ttm_valuation import export
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();r=export(ROOT,a.config,a.output)
    print(json.dumps([dict(date=x['decision_at'],eps=x['ttm']['value'],pe=x['valuation']['pe'],pb=x['valuation']['pb']) for x in r['results']]))
