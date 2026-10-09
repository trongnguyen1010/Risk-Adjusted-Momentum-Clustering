"""PowerShell-friendly CafeF candidate trial entrypoint."""
import argparse
import json
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.stdout.reconfigure(encoding='utf8')
from delta_t1.experiments.cafef_financial_trial import CLOSED,prepare,jobs,run,verify,prepare50,feedback
from delta_t1.ingestion.financial_batch_evidence import inside
from delta_t1.ingestion.cafef_financial import digest


def verify_handoff(root,relative):
    result=verify(root,relative)
    refs=json.loads((inside(root,relative,'data')/'references.json').read_bytes())
    # Reviewed PDF/fact/image inputs can live outside the benchmark directory.
    # Check their exact pins as well as the local and cached-raw manifests.
    for name,pin in refs['source_pins'].items():
        if digest(inside(root,name,'data').read_bytes())!=pin:
            raise ValueError('reviewed reference input changed: '+name)
    return dict(result,reviewed_reference_files=len(refs['source_pins']))

if __name__=='__main__':
    p=argparse.ArgumentParser(description='CafeF-first trial50 candidate collection and offline gap reporting')
    p.add_argument('action',choices=['doctor','plan','run','verify','feedback','prepare50'])
    p.add_argument('--config',default='configs/data/cafef_financial_trial50_v1.json')
    p.add_argument('--output');p.add_argument('--run');p.add_argument('--resume-from');p.add_argument('--execute-network',action='store_true')
    a=p.parse_args()
    try:
        if a.action in ['doctor','plan']:
            c=json.loads((ROOT/a.config).read_bytes());_,members=prepare(ROOT,c)
            result=dict(status='READY',symbols=len(members),base_requests=len(jobs(c)),gap_request_limit=c['gap_request_limit'],
                max_attempts=c['budgets']['max_transport_attempts'],free_disk_bytes=shutil.disk_usage(ROOT).free,
                source='CAFEF_DETAIL',network_executed=False,**CLOSED)
        elif a.action=='run':
            if not a.output:p.error('--output required')
            r=run(ROOT,a.config,a.output,a.resume_from,a.execute_network)
            result={k:r[k] for k in ['engineering_status','attempted_symbols','base_success','present_statement_periods','target_statement_periods','cache_hits','qa_counts','accepted_facts','pilot_preflight_pass']}
            result['handoff_verification']=verify_handoff(ROOT,a.output)
        elif a.action=='verify':
            if not a.run:p.error('--run required')
            result=verify_handoff(ROOT,a.run)
        elif a.action=='prepare50':
            if not a.run or not a.output:p.error('--run pilot and --output config required')
            result=prepare50(ROOT,a.run,a.output)
        else:
            if not a.run or not a.output:p.error('--run and --output ZIP required')
            verify_handoff(ROOT,a.run)
            result=feedback(ROOT,a.run,a.output)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:
        print(json.dumps(dict(status='ERROR',error=str(e)),ensure_ascii=False));raise SystemExit(2)
