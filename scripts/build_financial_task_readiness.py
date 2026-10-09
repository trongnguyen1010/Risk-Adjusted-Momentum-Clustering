import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_task_readiness import export
if __name__=='__main__':
    p=argparse.ArgumentParser(description='Build per-task financial input readiness without calculating features')
    p.add_argument('--readiness-run',required=True);p.add_argument('--config',default='configs/data/financial_evidence_policy_v1.json');p.add_argument('--output',required=True)
    a=p.parse_args();out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data'):raise ValueError('output must be under data')
    r=export(ROOT/a.readiness_run,ROOT/a.config,out)
    print(json.dumps({'task_rows':len(r['rows']),'ready':sum(x['task_ready'] for x in r['rows'])}))
