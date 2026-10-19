"""Explicit bounded successor/recovery; never changes frozen v1 evidence."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments import financial_continuation as flow
from delta_t1.experiments import financial_user_workflow as old


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','recover','extract','audit','verify'])
    p.add_argument('--config',default='configs/data/financial_continuation50_v2.json')
    p.add_argument('--execute-network',action='store_true')
    p.add_argument('--pdf-sha'); p.add_argument('--full-ocr',action='store_true')
    p.add_argument('--retry-failed',action='store_true')
    a=p.parse_args()
    if a.action=='prepare': r=flow.prepare(ROOT,a.config)
    elif a.action=='recover': r=flow.recover(ROOT,a.config,a.execute_network)
    elif a.action=='extract':
        if not a.pdf_sha: p.error('--pdf-sha required')
        r=flow.extract(ROOT,a.config,a.pdf_sha,a.full_ocr,a.retry_failed,
            ROOT/'scripts/analyze_financial_scale.py')
    else:
        d=flow.descriptor(ROOT,a.config)
        r=old.report(ROOT,d['run']) if a.action=='audit' else old.verify(ROOT,d['run'])
    print(json.dumps(r,ensure_ascii=False,indent=2),flush=True)
    return 3 if r.get('status')=='GLOBAL_STOP' else 2 if r.get('status') in ['FAILED','EXTRACTION_FAILED'] else 0


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps(dict(status='ERROR',error=str(exc)),ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
