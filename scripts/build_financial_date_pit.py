import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_date_pit import export
if __name__=='__main__':
    p=argparse.ArgumentParser(description='Date PIT evidence using approved next-session rule, no timestamp inference')
    p.add_argument('--readiness-run',required=True);p.add_argument('--publication-run',required=True)
    p.add_argument('--policy',default='configs/data/financial_date_pit_v1.json');p.add_argument('--output',required=True)
    p.add_argument('--task-run');p.add_argument('--decision-date')
    a=p.parse_args();out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data'):raise ValueError('output must be under data')
    r=export(ROOT/a.readiness_run,ROOT/a.publication_run,ROOT/a.policy,ROOT,out,
             ROOT/a.task_run if a.task_run else None,a.decision_date)
    print(json.dumps(r['counts']))
