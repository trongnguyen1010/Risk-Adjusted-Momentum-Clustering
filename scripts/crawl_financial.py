"""Financial crawler for users: doctor, plan, crawl/resume, offline verify."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf8')
from delta_t1.experiments.financial_crawl import doctor, prepare, run, verify
from delta_t1.ingestion.financial_batch_evidence import inside


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ['doctor', 'plan', 'run']:
        p = sub.add_parser(name)
        p.add_argument('--config', required=True, help='JSON config relative to checkout')
        if name == 'run':
            p.add_argument('--output', required=True, help='New folder under data/')
            p.add_argument('--execute-network', action='store_true', help='Public bounded acquisition; default offline')
            p.add_argument('--resume-from', action='append', default=[])
            p.add_argument('--seed-run', action='append', default=[], help='Verified provider/document inventory under data/')
    p = sub.add_parser('verify')
    p.add_argument('--run', required=True)
    a = parser.parse_args()
    try:
        if a.action == 'verify':
            result = verify(ROOT, a.run)
        else:
            user = json.loads(inside(ROOT, a.config).read_bytes())
            c = prepare(user)
            if a.action == 'doctor':
                result = doctor(user)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0 if result['status'] == 'READY' else 3
            elif a.action == 'plan':
                result = dict(symbols=c['symbols'], years=c['years'], periods=user.get('periods', ['year']),
                    budgets={k:v for k,v in c.items() if k.startswith('max_')},
                    environment=doctor(user), network_executed=False,
                    pdf_discovery=user.get('pdf_discovery', True), pdf_quarters=user.get('pdf_quarters', [0]),
                    financial_features_allowed=False, full_universe_allowed=False)
            else:
                r = run(ROOT, a.config, a.output, a.resume_from, a.seed_run, a.execute_network)
                result = {k:r[k] for k in ['engineering_status', 'coverage_status', 'acceptance_status', 'metrics', 'review_queue_items']}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0 if r['engineering_status'] == 'COMPLETE' else 4 if r['engineering_status'] == 'HARD_STOP' else 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status='ERROR', message=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
