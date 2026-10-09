"""Local bounded financial trial: doctor, plan, run, verify, feedback."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf8')
from delta_t1.experiments.financial_crawl_trial import doctor, prepare, run, verify, feedback
from delta_t1.ingestion.financial_batch_evidence import Checkpoints, inside
from delta_t1.ingestion.financial_crawl_pdf import extract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action',required=True)
    for action in ['doctor','plan','run']:
        p = sub.add_parser(action)
        p.add_argument('--config',default='configs/data/financial_crawl_50_trial_v1.json')
        if action=='run':
            p.add_argument('--output',required=True)
            p.add_argument('--resume-from',action='append',default=[])
            p.add_argument('--execute-network',action='store_true')
    for action in ['verify','feedback']:
        p = sub.add_parser(action)
        p.add_argument('--run',required=True)
        if action=='feedback':
            p.add_argument('--output',required=True,help='New ZIP path under artifacts/')
    p = sub.add_parser('pdf-worker',help=argparse.SUPPRESS)
    p.add_argument('--output',required=True)
    p.add_argument('--job',required=True)
    args = parser.parse_args()
    try:
        if args.action=='pdf-worker':
            out = inside(ROOT,args.output,'data')
            job_path = inside(ROOT,args.job,'data')
            if not job_path.is_relative_to(out/'pdf-jobs'):
                raise ValueError('worker job outside output')
            job = json.loads(job_path.read_bytes())
            cp = Checkpoints(ROOT,out,job['config'],job['resume_runs'])
            r = extract(cp,job['document'],ROOT/'scripts/ocr_financial_pages.ps1')
            result = dict(receipt=r,metrics=cp.metrics)
        elif args.action=='verify':
            result = verify(ROOT,args.run)
        elif args.action=='feedback':
            result = feedback(ROOT,args.run,args.output)
        else:
            user = json.loads(inside(ROOT,args.config,'configs').read_bytes())
            if args.action=='doctor':
                result = doctor(ROOT,user)
                print(json.dumps(result,ensure_ascii=False,indent=2))
                return 0 if result['status']=='READY' else 3
            if args.action=='plan':
                plan,c = prepare(ROOT,user)
                result = dict(version=c['version'],members=plan['members'],waves=plan['waves'],
                    base_requests=len(c['symbols'])*6,budgets=c['budgets'],annual_years=c['annual_years'],
                    quarter_years=c['quarter_years'],documents_enabled=c['documents_enabled'],
                    environment=doctor(ROOT,user),network_executed=False)
            else:
                r = run(ROOT,args.config,args.output,args.resume_from,args.execute_network)
                result = {k:r[k] for k in ['engineering_status','attempted_symbols','planned_symbols',
                    'base_success','metrics','engineering_targets_pass','next_100_allowed']}
                print(json.dumps(result,ensure_ascii=False,indent=2))
                return 0 if r['engineering_status']=='COMPLETE' else 4 if r['engineering_status']=='HARD_STOP' else 2
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except KeyboardInterrupt:
        print('Interrupted. Preserve output; resume into a new directory using --resume-from.',file=sys.stderr)
        return 130
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps(dict(status='ERROR',message=str(exc)),ensure_ascii=False),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
