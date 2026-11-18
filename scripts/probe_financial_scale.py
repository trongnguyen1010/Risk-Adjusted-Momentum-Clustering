"""PowerShell-friendly bounded scale probe; defaults to offline."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
sys.stdout.reconfigure(encoding='utf8')
from delta_t1.experiments.financial_scale_probe import acquire,verify

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['acquire','verify'])
    p.add_argument('--config',default='configs/data/financial_scale_probe_v1.json')
    p.add_argument('--output');p.add_argument('--run');p.add_argument('--execute-network',action='store_true')
    a=p.parse_args()
    if a.action=='acquire' and not a.output:p.error('--output required')
    if a.action=='verify' and not a.run:p.error('--run required')
    try:
        r=acquire(ROOT,a.config,a.output,a.execute_network) if a.action=='acquire' else verify(ROOT,a.run)
        print(json.dumps({k:v for k,v in r.items() if k not in ['requests','discoveries','documents','transport_state']},ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:
        print(json.dumps(dict(status='ERROR',error=str(e)),ensure_ascii=False));raise SystemExit(2)
