"""User handoff for frozen50 continuation with inherited-metadata compatibility."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments import financial_resume as adapter
from delta_t1.experiments import financial_continuation as base
from delta_t1.experiments import financial_user_workflow as f


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['recover','extract','audit','verify','template','review'])
    p.add_argument('--config',default='configs/data/financial_resume50_v3/config.json')
    p.add_argument('--execute-network',action='store_true')
    p.add_argument('--pdf-sha'); p.add_argument('--symbol'); p.add_argument('--review-file')
    p.add_argument('--full-ocr',action='store_true'); p.add_argument('--retry-failed',action='store_true')
    a=p.parse_args(); c,d=adapter.open_adapter(ROOT,a.config)
    if a.action=='recover': r=base.recover(ROOT,c['base_config'],a.execute_network)
    elif a.action=='extract':
        if not a.pdf_sha: p.error('--pdf-sha required')
        r=adapter.extract(ROOT,a.config,a.pdf_sha,a.full_ocr,a.retry_failed,
            ROOT/'scripts/analyze_financial_scale.py')
    elif a.action=='template':
        if not a.symbol: p.error('--symbol required')
        r=f.template(ROOT,d['run'],a.symbol,pdf_sha=a.pdf_sha)
    elif a.action=='review':
        if not a.review_file: p.error('--review-file required')
        r=f.review(ROOT,d['run'],a.review_file)
    else: r=f.report(ROOT,d['run']) if a.action=='audit' else f.verify(ROOT,d['run'])
    print(json.dumps(r,ensure_ascii=False,indent=2),flush=True)
    return 3 if r.get('status')=='GLOBAL_STOP' else 2 if r.get('status') in ['FAILED','EXTRACTION_FAILED'] else 0


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps(dict(status='ERROR',error=str(exc)),ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
